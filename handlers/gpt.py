# handlers_gpt.py
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from utils.states import MENU, GPT_QUESTION, CHECK_PRODUCT, RECIPES
from utils import gpt_35
from utils.config import OPENAI_API_KEY
from handlers.recipes import recipes_callback
from database.database import SessionLocal
from database.crud import get_user_conversation_history, update_conversation_history, get_or_create_user, save_conversation_history

logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает все текстовые сообщения пользователя через GPT,
    если не активно другое состояние (проверка продукта и т.д.)
    """
    # Инициализируем структуры данных, если они отсутствуют
    if not hasattr(context, 'user_data'):
        context.user_data = {}
    if 'state' not in context.user_data:
        context.user_data['state'] = MENU
        
    # Если активно другое состояние, не обрабатываем сообщение через GPT
    current_state = context.user_data.get('state')
    if current_state in [CHECK_PRODUCT, RECIPES]:
        return

    user_message = update.message.text
    user_id = update.effective_user.id
    
    # Создаем сессию базы данных
    db = SessionLocal()
    
    logger.info(f"Получено сообщение от пользователя {user_id}: {user_message[:50]}...")
    
    try:
        # Получаем user_id из контекста или создаем новый профиль
        db_user_id = context.user_data.get('user_id')
        if not db_user_id:
            # Если id нет в контексте, создаем профиль пользователя
            user_profile = get_or_create_user(
                db=db,
                telegram_id=user_id,
                username=update.effective_user.username,
                first_name=update.effective_user.first_name,
                last_name=update.effective_user.last_name
            )
            # Сохраняем ID в контексте для будущего использования
            db_user_id = user_profile.id
            context.user_data['user_id'] = db_user_id
            
        logger.info(f"ID пользователя в БД: {db_user_id}")
        
        # Инициализируем историю сообщений из базы данных, если она не загружена
        if 'messages_history' not in context.user_data:
            # Загружаем историю из БД
            history = get_user_conversation_history(db, db_user_id)
            # Проверяем, что история не None и не пустой список
            if history and isinstance(history, list):
                context.user_data['messages_history'] = history
                logger.info(f"Загружена история сообщений для пользователя {user_id} из БД: {len(history)} сообщений")
                logger.debug(f"Содержимое истории: {history}")
            else:
                # Инициализируем пустым списком, если история не найдена
                context.user_data['messages_history'] = []
                logger.info(f"История сообщений для пользователя {user_id} не найдена, создаем пустой список")
        else:
            logger.info(f"Используем существующую историю: {len(context.user_data['messages_history'])} сообщений")
            
        # Выводим текущую историю для отладки
        logger.info(f"История сообщений перед добавлением нового: {len(context.user_data.get('messages_history', []))} сообщений")
        
        # Добавляем сообщение пользователя в историю
        context.user_data['messages_history'].append({
            "role": "user",
            "content": user_message
        })
        
        # Ограничиваем историю последними 10 сообщениями
        if len(context.user_data['messages_history']) > 10:
            context.user_data['messages_history'] = context.user_data['messages_history'][-10:]
            logger.info(f"История сообщений ограничена 10 последними сообщениями")
        
        # Создаем клиента GPT с сохраненной историей
        gpt_client = gpt_35.ChatGPTClient(api_key=OPENAI_API_KEY)
        
        # Получаем ответ от GPT с учетом истории
        gpt_response = gpt_client.generate_response(
            user_message=user_message,
            message_history=context.user_data['messages_history']
        )
        
        # Проверяем, был ли вызов функции
        if gpt_response.startswith("FUNCTION_CALL:"):
            function_parts = gpt_response.split(":", 2)  # Разделяем на 3 части: FUNCTION_CALL, имя функции, контекстный ответ
            function_name = function_parts[1]
            
            # Получаем контекстный ответ (если есть)
            context_response = function_parts[2] if len(function_parts) > 2 else "Отлично! Сейчас покажу тебе наши здоровые рецепты 🥗"
            
            # Обработка вызова функции показа рецептов
            if function_name == "show_healthy_recipes":
                logger.info(f"Function call detected: {function_name}")
                
                # Создаем сообщение о переходе к рецептам с контекстным ответом
                await update.message.reply_text(context_response)
                
                # Отправляем меню рецептов напрямую
                keyboard = [
                    [InlineKeyboardButton("Завтраки", callback_data="breakfast")],
                    [InlineKeyboardButton("Полдники", callback_data="poldnik")],
                    [InlineKeyboardButton("Обеды", callback_data="lunch")],
                    [InlineKeyboardButton("Ужины", callback_data="dinner")],
                    [InlineKeyboardButton("Назад", callback_data='back_to_menu')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    text="Выберите прием пищи:",
                    reply_markup=reply_markup
                )
                
                # Не меняем состояние, чтобы пользователь мог продолжать общаться с ботом
                # Просто добавляем флаг, что меню рецептов активно
                context.user_data['recipes_menu_active'] = True
                
                # Добавляем ответ бота в историю
                context.user_data['messages_history'].append({
                    "role": "assistant",
                    "content": context_response
                })
                
                # Сохраняем историю в БД
                updated_conversation = update_conversation_history(db, db_user_id, context.user_data['messages_history'])
                logger.info(f"Сохранена история диалога для пользователя {user_id} в БД")
                if updated_conversation:
                    logger.info(f"История успешно сохранена, ID записи: {updated_conversation.id}")
                else:
                    logger.warning(f"Функция update_conversation_history вернула None")
                
                return MENU
        
        # Обычный ответ (не вызов функции)
        # Добавляем ответ в историю
        context.user_data['messages_history'].append({
            "role": "assistant",
            "content": gpt_response
        })
        
        # Сохраняем обновленную историю в базу данных
        if db_user_id:
            try:
                # Сохраняем историю в базу данных
                updated_conversation = update_conversation_history(db, db_user_id, context.user_data['messages_history'])
                logger.info(f"Сохранена история диалога для пользователя {user_id} в БД")
                if updated_conversation:
                    logger.info(f"История успешно сохранена, ID записи: {updated_conversation.id}")
                else:
                    logger.warning(f"Функция update_conversation_history вернула None")
            except Exception as e:
                logger.error(f"Ошибка при сохранении истории диалога: {e}", exc_info=True)
                # Попробуем еще раз, но создадим новую историю вместо обновления
                try:
                    new_conversation = save_conversation_history(db, db_user_id, context.user_data['messages_history'])
                    logger.info(f"Создана новая запись истории диалога: {new_conversation and new_conversation.id}")
                except Exception as e2:
                    logger.error(f"Не удалось создать новую запись истории: {e2}", exc_info=True)
        else:
            logger.warning(f"Не удалось сохранить историю диалога: неверный user_id для пользователя {user_id}")

        await update.message.reply_text(
            text=gpt_response
        )
        
    except Exception as e:
        logger.error(f"Ошибка при работе с GPT: {e}", exc_info=True)
        await update.message.reply_text(
            text=f"⚠️ Произошла ошибка при обработке вашего вопроса:\n{str(e)}"
        )
    finally:
        # Закрываем сессию БД
        db.close()

    return MENU
