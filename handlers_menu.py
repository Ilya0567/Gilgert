# handlers_menu.py
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

# Состояния
from assistant import MENU, GPT_QUESTION, CHECK_PRODUCT, RECIPES

logger = logging.getLogger(__name__)


async def start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("О нас", callback_data='about')],
        [InlineKeyboardButton("Задать вопрос (GPT)", callback_data='ask_question')],
        [InlineKeyboardButton("Проверить продукт", callback_data='check_product')],
        [InlineKeyboardButton("Здоровые рецепты", callback_data='healthy_recipes')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            text="👋 Привет! Я ваш помощник...",
            reply_markup=reply_markup
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            text="👋 Привет! Я ваш помощник...",
            reply_markup=reply_markup
        )
    return MENU


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'about':
        about_text = "🤖 «PYOOTS» — ... (описание)"
        await query.edit_message_text(
            text=about_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')]
            ])
        )
        return MENU

    elif data == 'ask_question':
        await query.edit_message_text(
            text="❓ Введите ваш вопрос для GPT:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Отмена", callback_data='back_to_menu')]
            ])
        )
        return GPT_QUESTION

    elif data == 'check_product':
        await query.edit_message_text(
            text="🔍 Введите название продукта:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Отмена", callback_data='back_to_menu')]
            ])
        )
        return CHECK_PRODUCT

    elif data == 'healthy_recipes':
        # Меню, где мы показываем «завтраки», «обеды», «ужины»
        # (Убираем "напитки" - оно теперь внутри подменю)
        await query.edit_message_text(
            text="Выберите прием пищи:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Завтраки", callback_data="breakfast")],
                [InlineKeyboardButton("Обеды", callback_data="lunch")],
                [InlineKeyboardButton("Ужины", callback_data="dinner")],
                [InlineKeyboardButton("Назад", callback_data='back_to_menu')]
            ])
        )
        return RECIPES

    elif data == 'back_to_menu':
        return await start_menu(update, context)

    return MENU


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Диалог прерван. Введите /start заново.")
    elif update.callback_query:
        await update.callback_query.edit_message_text("Диалог прерван. Введите /start заново.")
    return ConversationHandler.END
