# handlers_gpt.py
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from utils.states import MENU, GPT_QUESTION, CHECK_PRODUCT, RECIPES
from utils import gpt_35
from utils.config import OPENAI_API_KEY
from handlers.recipes import recipes_callback
from database.database import SessionLocal
from database.crud import get_user_conversation_history, update_conversation_history, get_or_create_user

logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает все текстовые сообщения пользователя через GPT,
    если не активно другое состояние (проверка продукта и т.д.)
    """
    # Если активно другое состояние, не обрабатываем сообщение через GPT
    current_state = context.user_data.get('state')
    if current_state in [CHECK_PRODUCT, RECIPES]:
        return

    user_message = update.message.text
    user_id = update.effective_user.id
    
    # Создаем сессию базы данных
    db = SessionLocal()
    
    try:
        # Получаем профиль пользователя из context.user_data
        user_profile = context.user_data.get('user_profile')
        if not user_profile:
            # Если профиля нет в контексте, попробуем найти в БД по telegram_id
            user_profile = get_or_create_user(
                db=db,
                telegram_id=user_id,
                username=update.effective_user.username,
                first_name=update.effective_user.first_name,
                last_name=update.effective_user.last_name
            )
            # Сохраняем в контексте для будущего использования
            context.user_data['user_profile'] = user_profile
            
        # Используем ID пользователя из базы данных
        db_user_id = user_profile.id
        
        # Инициализируем историю сообщений из базы данных, если она не загружена
        if 'messages_history' not in context.user_data:
            # Загружаем историю из БД
            context.user_data['messages_history'] = get_user_conversation_history(db, db_user_id)
            logger.info(f"Loaded message history for user {user_id} from database")
        
        # Добавляем сообщение пользователя в историю
        context.user_data['messages_history'].append({
            "role": "user",
            "content": user_message
        })
        
        # Ограничиваем историю последними 10 сообщениями
        if len(context.user_data['messages_history']) > 10:
            context.user_data['messages_history'] = context.user_data['messages_history'][-10:]
        
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
                update_conversation_history(db, db_user_id, context.user_data['messages_history'])
                
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
                update_conversation_history(db, db_user_id, context.user_data['messages_history'])
                logger.info(f"Saved message history for user {user_id} to database")
            except Exception as e:
                logger.error(f"Failed to save message history: {e}")
        else:
            logger.warning(f"Cannot save message history: invalid user_id for user {user_id}")

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
