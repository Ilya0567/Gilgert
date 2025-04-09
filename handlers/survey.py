import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.database import SessionLocal
from database.crud import get_or_create_survey_status, update_survey_reminder, mark_survey_completed
import time
import asyncio

# Создаем логгер для модуля
survey_logger = logging.getLogger(__name__)

async def send_survey_invitation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Отправляет приглашение заполнить анкету новому пользователю.
    """
    user = update.effective_user
    
    # Получаем профиль пользователя
    user_profile = context.user_data.get('user_profile')
    
    if not user_profile:
        survey_logger.error(f"Не удалось получить профиль пользователя {user.id} для отправки приглашения анкеты")
        return

    survey_logger.info(f"Отправка приглашения заполнить анкету пользователю {user.id}")
    
    # Создаем сессию БД
    db = SessionLocal()
    try:
        # Проверяем и обновляем статус анкеты
        survey_status = get_or_create_survey_status(db, user_profile.id)
        
        # Если анкета уже заполнена, не отправляем приглашение
        if survey_status.is_completed:
            survey_logger.info(f"Пользователь {user.id} уже заполнил анкету, приглашение не отправлено")
            return
        
        # Обновляем время напоминания
        update_survey_reminder(db, user_profile.id)

        # Формируем приветственное сообщение
        name = user.first_name or "друг"
        message = (
            f"Привет, {name}! 👋\n\n"
            f"Для того, чтобы я мог давать более подходящие рекомендации, "
            f"мне нужно больше узнать о тебе.\n\n"
            f"Пожалуйста, заполни небольшую анкету по ссылке ниже. "
            f"Это займет всего несколько минут."
        )
        
        # Создаем кнопку для перехода к анкете
        keyboard = [
            [InlineKeyboardButton("Заполнить анкету", url="https://example.com/survey")]  # URL будет заменен на настоящий
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем сообщение
        await context.bot.send_message(
            chat_id=user.id,
            text=message,
            reply_markup=reply_markup
        )
        
        survey_logger.info(f"Приглашение заполнить анкету успешно отправлено пользователю {user.id}")
    except Exception as e:
        survey_logger.error(f"Ошибка при отправке приглашения анкеты пользователю {user.id}: {e}", exc_info=True)
    finally:
        db.close()

async def send_survey_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Отправляет напоминание о заполнении анкеты пользователям, которые еще не заполнили её.
    Вызывается по расписанию.
    """
    survey_logger.info("Начало отправки напоминаний о заполнении анкеты")
    
    db = SessionLocal()
    try:
        from database.crud import get_users_needing_survey_reminder
        
        # Получаем пользователей, которым нужно отправить напоминание
        users = get_users_needing_survey_reminder(db)
        
        survey_logger.info(f"Найдено {len(users)} пользователей для напоминания об анкете")
        
        for user in users:
            try:
                # Формируем текст напоминания
                message = (
                    "Привет! 👋\n\n"
                    "Хочу напомнить, что ты еще не заполнил(а) анкету. "
                    "Это поможет мне давать более точные рекомендации и советы.\n\n"
                    "Пожалуйста, найди несколько минут, чтобы пройти опрос."
                )
                
                # Создаем кнопку для перехода к анкете
                keyboard = [
                    [InlineKeyboardButton("Заполнить анкету", url="https://example.com/survey")]  # URL будет заменен на настоящий
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Отправляем напоминание
                await context.bot.send_message(
                    chat_id=user.telegram_id,
                    text=message,
                    reply_markup=reply_markup
                )
                
                # Обновляем время последнего напоминания
                update_survey_reminder(db, user.id)
                
                survey_logger.info(f"Напоминание об анкете отправлено пользователю {user.telegram_id}")
                
                # Небольшая задержка между сообщениями
                await asyncio.sleep(0.5)
                
            except Exception as e:
                survey_logger.error(f"Ошибка при отправке напоминания пользователю {user.telegram_id}: {e}")
                continue
                
    except Exception as e:
        survey_logger.error(f"Ошибка при отправке напоминаний об анкете: {e}", exc_info=True)
    finally:
        db.close()

async def handle_survey_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает обратный вызов от заполненной анкеты (возможно, будет реализовано через веб-хук).
    """
    user = update.effective_user
    
    # Получаем профиль пользователя
    user_profile = context.user_data.get('user_profile')
    
    if not user_profile:
        survey_logger.error(f"Не удалось получить профиль пользователя {user.id} для обработки заполнения анкеты")
        return
        
    db = SessionLocal()
    try:
        # Отмечаем анкету как заполненную
        mark_survey_completed(db, user_profile.id)
        
        # Благодарим пользователя
        await context.bot.send_message(
            chat_id=user.id,
            text="Спасибо за заполнение анкеты! Теперь я смогу давать тебе более подходящие рекомендации. 😊"
        )
        
        survey_logger.info(f"Анкета пользователя {user.id} отмечена как заполненная")
    except Exception as e:
        survey_logger.error(f"Ошибка при обработке заполнения анкеты пользователем {user.id}: {e}", exc_info=True)
    finally:
        db.close()

def schedule_survey_reminders(scheduler):
    """
    Добавляет задачу отправки напоминаний о заполнении анкеты в планировщик.
    """
    scheduler.add_job(
        send_survey_reminder,
        'cron', 
        hour=15,  # Отправляем напоминания в 12:00
        minute=1,
        id='survey_reminder'
    )
    survey_logger.info("Задача отправки напоминаний об анкете добавлена в планировщик") 