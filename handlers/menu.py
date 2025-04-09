# handlers_menu.py
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from utils.states import MENU, GPT_QUESTION, CHECK_PRODUCT, RECIPES
from handlers.survey import send_survey_invitation

logger = logging.getLogger(__name__)

async def start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Хендлер для команды /start.
    Показывает приветственное сообщение и клавиатуру главного меню.
    """
    keyboard = [
        [InlineKeyboardButton("Здоровые рецепты", callback_data='healthy_recipes')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Получаем имя пользователя
    user = update.effective_user
    user_name = user.first_name if user.first_name else "пользователь"

    # Приветствие с обращением по имени
    welcome_text = (
        f"👋 Привет, {user_name}! Я ваш помощник, созданный специально для людей с синдромом Жильбера.\n\n"
        "Я могу помочь тебе с рекомендациями по продуктам питания и ответить на вопросы о том, "
        "можно ли употреблять определенный продукт или блюдо при синдроме Жильбера.\n\n"
        "✨ Просто спроси меня в чате о любом продукте или блюде, и я подскажу, разрешено ли оно к употреблению "
        "и какие могут быть нюансы или противопоказания.\n\n"
        "📝 Также ты можешь посмотреть собранные мной вкусные здоровые рецепты, нажав на кнопку ниже."
    )

    if update.message:
        await update.message.reply_text(text=welcome_text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text=welcome_text, reply_markup=reply_markup)
    
    # Отправляем приглашение заполнить анкету (если нужно)
    await send_survey_invitation(update, context)
    
    return MENU


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_query=None):
    """
    Обработка нажатий на кнопки главного меню.
    Параметр callback_query позволяет передать внешний объект callback_query для имитации нажатия кнопки.
    """
    
    query = callback_query or update.callback_query
    
    # Безопасный вызов answer() с проверкой 
    if hasattr(query, 'answer') and callable(query.answer):
        await query.answer()
    
    data = query.data

    logger.debug(data)

    if data == 'about':
        # Ставим старый текст "О нас":
        about_text = (
            "🤖 «PYOOTS» — это интеллектуальный помощник, созданный специально для людей с синдромом Жильбера.\n\n"
            "🏥 Он призван поддержать пользователей в повседневном уходе за здоровьем и сделать образ жизни комфортнее.\n\n"
            "💙 Бот уже применяет искусственный интеллект для предоставления полезных рекомендаций, "
            "а в будущем функциональность будет расширяться, обеспечивая ещё более точные и персонализированные советы."
        )
        await query.edit_message_text(
            text=about_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')]
            ])
        )
        return MENU

    elif data == 'ask_question':
        # Текст при переходе к GPT
        await query.edit_message_text(
            text="❓ Пожалуйста, задайте ваш вопрос.\n\n"
                 "Как только вы отправите сообщение, я постараюсь ответить вам.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Отмена", callback_data='back_to_menu')]
            ])
        )
        return GPT_QUESTION

    elif data == 'check_product':
        await query.edit_message_text(
            text="🔍 Пожалуйста, введите название продукта, который Вас интересует:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Отмена", callback_data='back_to_menu')]
            ])
        )
        return CHECK_PRODUCT

    elif data == 'healthy_recipes':
        # Меню, где мы показываем «завтраки», «обеды», «ужины»
        await query.edit_message_text(
            text="Выберите прием пищи:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Завтраки", callback_data="breakfast")],
                [InlineKeyboardButton("Полдники", callback_data="poldnik")],
                [InlineKeyboardButton("Обеды", callback_data="lunch")],
                [InlineKeyboardButton("Ужины", callback_data="dinner")],
                [InlineKeyboardButton("Назад", callback_data='back_to_menu')]
            ])
        )
        # Остаемся в MENU вместо перехода в RECIPES, чтобы можно было писать сообщения
        return MENU

    # Обрабатываем callback_query от кнопок меню рецептов, но остаемся в меню MENU
    # Это позволяет взаимодействовать с кнопками без переключения состояния
    elif data in ["breakfast", "poldnik", "lunch", "dinner", "drinks"] or \
         data.startswith(("bcat_", "bitem_", "pcat_", "pitem_", "lcat_", "litem_", "dcat_", "ditem_")) or \
         data == "rate_recipe" or data.startswith("rating_") or data == "ignore_rating" or \
         data.startswith("category_") or data.startswith("dish_") or \
         data.startswith("drinks_cat_") or data.startswith("drinks_name_"):
        from handlers.recipes import recipes_callback
        # Временно устанавливаем флаг, что работаем с рецептами
        context.user_data['temp_recipes_mode'] = True
        # Вызываем обработчик рецептов
        await recipes_callback(update, context)
        # Убираем флаг после обработки
        if 'temp_recipes_mode' in context.user_data:
            del context.user_data['temp_recipes_mode']
        # Остаемся в MENU для продолжения чата
        return MENU

    elif data == 'back_to_menu':
        return await start_menu(update, context)

    return MENU


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Общий fallback (используется при /cancel).
    Завершает диалог и ConversationHandler.
    """
    if update.message:
        await update.message.reply_text("Диалог прерван. Введите /start заново.")
    elif update.callback_query:
        await update.callback_query.edit_message_text("Диалог прерван. Введите /start заново.")
    return ConversationHandler.END
