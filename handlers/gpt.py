# handlers_gpt.py
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from utils.states import MENU, GPT_QUESTION, CHECK_PRODUCT, RECIPES
from utils import gpt_35
from utils.config import KEY

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
    
    # Инициализируем историю сообщений, если её нет
    if 'messages_history' not in context.user_data:
        context.user_data['messages_history'] = []
    
    # Добавляем сообщение пользователя в историю
    context.user_data['messages_history'].append({
        "role": "user",
        "content": user_message
    })
    
    # Ограничиваем историю последними 10 сообщениями
    if len(context.user_data['messages_history']) > 10:
        context.user_data['messages_history'] = context.user_data['messages_history'][-10:]

    try:
        # Создаем клиента GPT с сохраненной историей
        gpt_client = gpt_35.ChatGPTClient(api_key=KEY)
        
        # Получаем ответ от GPT с учетом истории
        gpt_response = gpt_client.generate_response(
            user_message=user_message,
            message_history=context.user_data['messages_history']
        )
        
        # Добавляем ответ в историю
        context.user_data['messages_history'].append({
            "role": "assistant",
            "content": gpt_response
        })

        await update.message.reply_text(
            text=gpt_response
        )
        
    except Exception as e:
        logger.error(f"Ошибка при работе с GPT: {e}")
        await update.message.reply_text(
            text=f"⚠️ Произошла ошибка при обработке вашего вопроса:\n{str(e)}"
        )

    return MENU
