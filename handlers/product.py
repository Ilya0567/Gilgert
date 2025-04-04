# handlers_product.py
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from states import MENU, GPT_QUESTION, CHECK_PRODUCT, RECIPES
from data_operation import check_product, id_request
from config import CHAT_ID

logger = logging.getLogger(__name__)

async def product_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Состояние CHECK_PRODUCT: пользователь вводит название продукта,
    бот проверяет и отвечает.
    """
    product = update.message.text
    user_name = update.message.from_user.username or update.message.from_user.full_name

    # ищем ответ
    answer = check_product(product)

    # Отправляем ответ
    await update.message.reply_text(
        answer,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 В меню", callback_data='back_to_menu')]
        ])
    )

    # Если требуется, перенаправляем вопрос специалистам
    # (судя по вашему коду, если "ответ" фигурирует в тексте)
    if "ответ" in answer.lower():
        product_question_id = id_request()
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=f'Вопрос по продукту №{product_question_id} от пользователя {user_name}:\n "{product}"'
        )

    return MENU
