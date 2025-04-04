# handlers_gpt.py
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from ..utils.states import MENU, GPT_QUESTION, CHECK_PRODUCT, RECIPES
from ..utils import gpt_35  # ваш файл с ChatGPTClient
from ..utils.config import KEY

GPT_CLIENT = gpt_35.ChatGPTClient(api_key=KEY)

logger = logging.getLogger(__name__)

async def gpt_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Состояние GPT_QUESTION: пользователь прислал текст - запрос к GPT.
    """
    user_question = update.message.text

    try:
        # Вызываем ChatGPT
        gpt_response = gpt_35.ChatGPTClient(api_key=gpt_35.KEY).generate_response(user_message=user_question)
        # Или, если вы уже имеете готовый клиент: gpt_35.client.generate_response(...)
        # В вашем коде GPT_CLIENT = gpt_35.ChatGPTClient(api_key=KEY).
        # Можете сохранить в глобальной переменной (как было), тогда просто используйте GPT_CLIENT.

        await update.message.reply_text(
            text=gpt_response,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 В меню", callback_data='back_to_menu')]
            ])
        )
    except Exception as e:
        logger.error(f"Ошибка при работе с GPT: {e}")
        await update.message.reply_text(
            text=f"⚠️ Произошла ошибка при обработке вашего вопроса:\n{str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 В меню", callback_data='back_to_menu')]
            ])
        )

    return MENU
