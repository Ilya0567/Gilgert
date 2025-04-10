import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.database import SessionLocal
from database.crud import get_or_create_survey_status, update_survey_reminder, mark_survey_completed, get_user_survey_status
import time
import asyncio

# Создаем логгер для модуля
survey_logger = logging.getLogger(__name__)

async def send_survey_invitation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Отправляет приглашение заполнить анкету новому пользователю.
    """
    user = update.effective_user
    
    # Создаем сессию БД
    db = SessionLocal()
    try:
        # Получаем ID пользователя из контекста или создаем новый профиль
        user_id = context.user_data.get('user_id')
        
        if not user_id:
            # Если ID не найден в контексте, создаем профиль
            survey_logger.info(f"ID пользователя {user.id} не найден в контексте, получаем из базы данных")
            from database.database import get_or_create_user
            user_profile = get_or_create_user(
                db=db,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            user_id = user_profile.id
            # Сохраняем ID в контексте
            context.user_data['user_id'] = user_id
        
        if not user_id:
            survey_logger.error(f"Не удалось получить ID пользователя {user.id} для отправки приглашения анкеты")
            return

        survey_logger.info(f"Отправка приглашения заполнить анкету пользователю {user.id} (профиль: {user_id})")
        
        # Проверяем и обновляем статус анкеты
        survey_status = get_or_create_survey_status(db, user_id)
        
        # Если анкета уже заполнена, не отправляем приглашение
        if survey_status.is_completed:
            survey_logger.info(f"Пользователь {user.id} уже заполнил анкету, приглашение не отправлено")
            return
        
        # Обновляем время напоминания
        update_survey_reminder(db, user_id)

        # Формируем приветственное сообщение
        name = user.first_name or "друг"
        message = (
            f"Привет, {name}! 👋\n\n"
            f"Для того, чтобы я мог давать более подходящие рекомендации, "
            f"мне нужно больше узнать о тебе.\n\n"
            f"Пожалуйста, заполни небольшую анкету по ссылке ниже. "
            f"Это займет всего несколько минут."
        )
        
        # Создаем inline кнопку для перехода к анкете
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text="Заполнить анкету", 
                url=f"http://193.176.190.205:5000/survey?telegram_id={user.id}"
            )]
        ])
        
        # Отправляем сообщение, учитывая разные контексты
        try:
            survey_logger.info(f"Попытка отправки приглашения пользователю {user.id}")
            # Если обновление пришло из callback_query и это не первое сообщение
            if update.callback_query and hasattr(update.callback_query, 'message') and update.callback_query.message:
                try:
                    # Отправляем новое сообщение
                    await context.bot.send_message(
                        chat_id=user.id,
                        text=message,
                        reply_markup=keyboard
                    )
                except Exception as e:
                    survey_logger.error(f"Ошибка при отправке сообщения через callback_query: {e}", exc_info=True)
                    raise
            else:
                # Отправляем обычное сообщение
                await context.bot.send_message(
                    chat_id=user.id,
                    text=message,
                    reply_markup=keyboard
                )
                
            survey_logger.info(f"Приглашение заполнить анкету успешно отправлено пользователю {user.id}")
        except Exception as e:
            survey_logger.error(f"Ошибка при отправке сообщения с приглашением: {e}", exc_info=True)
            # Пытаемся отправить сообщение другим способом - прямой вызов API
            try:
                survey_logger.info(f"Попытка отправки сообщения альтернативным способом пользователю {user.id}")
                await context.bot.send_message(
                    chat_id=user.id,
                    text=message,
                    reply_markup=keyboard,
                    disable_notification=True  # Тихое сообщение
                )
                survey_logger.info(f"Приглашение отправлено альтернативным способом пользователю {user.id}")
            except Exception as e2:
                survey_logger.error(f"Не удалось отправить приглашение альтернативным способом: {e2}", exc_info=True)
                # Не выбрасываем исключение, чтобы не прерывать работу бота
            
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
                
                # Создаем inline кнопку для перехода к анкете
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="Заполнить анкету", 
                        url=f"http://193.176.190.205:5000/survey?telegram_id={user.telegram_id}"
                    )]
                ])
                
                # Отправляем напоминание
                await context.bot.send_message(
                    chat_id=user.telegram_id,
                    text=message,
                    reply_markup=keyboard
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
    Обрабатывает обратный вызов после заполнения анкеты.
    """
    survey_logger.info("Получен callback после заполнения анкеты")
    
    user = update.effective_user
    survey_logger.info(f"User ID для callback: {user.id}, username: {user.username}")
    
    # Создаем сессию БД
    db = SessionLocal()
    try:
        # Получаем профиль пользователя
        from database.database import get_or_create_user
        user_profile = get_or_create_user(
            db=db,
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        if not user_profile:
            survey_logger.error(f"Не удалось получить профиль пользователя {user.id} для обработки callback анкеты")
            return
        
        # Получаем ID пользователя и сохраняем в контексте
        user_id = user_profile.id
        context.user_data['user_id'] = user_id
        
        survey_logger.info(f"Обработка callback анкеты для пользователя {user.id} (профиль: {user_id})")
        
        # Проверяем текущий статус
        current_status = get_user_survey_status(db, user_id)
        survey_logger.info(f"Текущий статус анкеты: {current_status and current_status.is_completed}")
        
        # Отмечаем анкету как заполненную
        mark_survey_completed(db, user_id)
        survey_logger.info(f"Анкета отмечена как заполненная для пользователя с профилем {user_id}")
        
        # Проверяем, что статус обновился
        updated_status = get_user_survey_status(db, user_id)
        survey_logger.info(f"Обновленный статус анкеты: {updated_status and updated_status.is_completed}")
        
        # Сохраняем статус и в user_data для надежности
        if not context.user_data:
            context.user_data = {}
        context.user_data['survey_completed'] = True
        
        # Отправляем сообщение с благодарностью - используем send_message вместо reply_text
        await context.bot.send_message(
            chat_id=user.id,
            text="Спасибо за заполнение анкеты! Теперь я смогу давать более точные рекомендации."
        )
        survey_logger.info(f"Отправлено сообщение с благодарностью пользователю {user.id}")
    except Exception as e:
        survey_logger.error(f"Ошибка при обработке callback анкеты: {e}", exc_info=True)
    finally:
        db.close()

def schedule_survey_reminders(scheduler, application):
    """
    Добавляет задачу отправки напоминаний о заполнении анкеты в планировщик.
    
    Args:
        scheduler: Планировщик задач
        application: Экземпляр приложения Telegram бота
    """
    try:
        # Создаем функцию-обертку для передачи application в context
        async def send_survey_reminder_wrapper():
            survey_logger.info("Запуск отправки напоминаний об анкете через планировщик")
            # Создаем контекст для вызова обработчика
            context = ContextTypes.DEFAULT_TYPE(
                application=application,
                chat_data=None,
                user_data=None,
                bot_data=None,
                job=None
            )
            await send_survey_reminder(context)
        
        # Добавляем задачу в планировщик
        scheduler.add_job(
            lambda: asyncio.create_task(send_survey_reminder_wrapper()),
            'cron', 
            hour=15,  # Отправляем напоминания в 15:00
            minute=1,
            id='survey_reminder',
            replace_existing=True  # Заменяем существующую задачу, если она есть
        )
        survey_logger.info("Задача отправки напоминаний об анкете добавлена в планировщик")
    except Exception as e:
        survey_logger.error(f"Ошибка при добавлении задачи напоминаний в планировщик: {e}", exc_info=True) 