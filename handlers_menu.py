import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

# Импортируем перечисление состояний (чтобы возвращать нужное состояние ConversationHandler)
from assistant import MENU, GPT_QUESTION, CHECK_PRODUCT, RECIPES

logger = logging.getLogger(__name__)


async def start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Хендлер для команды /start.
    Показывает приветственное сообщение и клавиатуру главного меню.
    """
    keyboard = [
        [InlineKeyboardButton("О нас", callback_data='about')],
        [InlineKeyboardButton("Задать вопрос (GPT)", callback_data='ask_question')],
        [InlineKeyboardButton("Проверить продукт", callback_data='check_product')],
        [InlineKeyboardButton("Здоровые рецепты", callback_data='healthy_recipes')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Если вызвано командой /start
    if update.message:
        await update.message.reply_text(
            text="👋 Привет! Я ваш помощник, созданный специально для помощи людям с синдромом Жильбера.\n\n"
                 "• 'О нас' — информация о проекте\n"
                 "• 'Задать вопрос (GPT)' — получить ответ от ИИ\n"
                 "• 'Проверить продукт' — узнать, можно ли его есть\n"
                 "• 'Здоровые рецепты' — посмотреть подборку блюд\n\n"
                 "Используйте /cancel, чтобы прервать диалог.",
            reply_markup=reply_markup
        )
    # Если вызвано из callback
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            text="👋 Привет! Я ваш помощник, созданный специально для помощи людям с синдромом Жильбера.\n\n"
                 "• 'О нас' — информация о проекте\n"
                 "• 'Задать вопрос (GPT)' — получить ответ от ИИ\n"
                 "• 'Проверить продукт' — узнать, можно ли его есть\n"
                 "• 'Здоровые рецепты' — посмотреть подборку блюд\n\n"
                 "Используйте /cancel, чтобы прервать диалог.",
            reply_markup=reply_markup
        )

    return MENU


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка нажатий на кнопки главного меню.
    """
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'about':
        # «О нас»
        about_text = (
            "🤖 «PYOOTS» — интеллектуальный помощник для людей с синдромом Жильбера.\n\n"
            "• Помогает в уходе за здоровьем\n"
            "• Даёт рекомендации по продуктам\n"
            "• Делится здоровыми рецептами\n"
            "• Использует ИИ для ответов на вопросы\n\n"
            "В будущем функционал будет ещё шире!"
        )
        await query.edit_message_text(
            text=about_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')]
            ])
        )
        # Остаёмся в MENU
        return MENU

    elif data == 'ask_question':
        # Переход к состоянию GPT_QUESTION
        await query.edit_message_text(
            text="❓ Пожалуйста, отправьте ваш вопрос сообщением. Я отвечу, как только прочитаю.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Отмена", callback_data='back_to_menu')]
            ])
        )
        return GPT_QUESTION

    elif data == 'check_product':
        # Переход к состоянию CHECK_PRODUCT
        await query.edit_message_text(
            text="🔍 Введите название продукта, который вас интересует:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Отмена", callback_data='back_to_menu')]
            ])
        )
        return CHECK_PRODUCT

    elif data == 'healthy_recipes':
        # Переход в меню рецептов (RECIPES)
        # Здесь можем сразу показать подменю в этом же файле — или вызывать другой хендлер
        await query.edit_message_text(
            text="Выберите категорию здоровых рецептов:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Завтраки", callback_data="breakfast")],
                [InlineKeyboardButton("Обеды", callback_data="lunch")],
                [InlineKeyboardButton("Ужины", callback_data="dinner")],
                [InlineKeyboardButton("Напитки", callback_data="drinks")],
                [InlineKeyboardButton("Назад", callback_data='back_to_menu')]
            ])
        )
        return RECIPES

    elif data == 'back_to_menu':
        # Возвращаемся к главному меню
        return await start_menu(update, context)

    return MENU


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Общий fallback (используется при /cancel).
    Завершает диалог и ConversationHandler.
    """
    if update.message:
        await update.message.reply_text("Диалог прерван. Для начала заново введите /start.")
    elif update.callback_query:
        await update.callback_query.edit_message_text("Диалог прерван. Для начала заново введите /start.")

    return ConversationHandler.END
