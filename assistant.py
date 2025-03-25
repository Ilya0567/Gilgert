import logging
from telegram.ext import (
    ApplicationBuilder,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from states import MENU, GPT_QUESTION, CHECK_PRODUCT, RECIPES

# Импорт хендлеров из отдельных файлов
from handlers_menu import start_menu, menu_callback, cancel
from handlers_gpt import gpt_user_message
from handlers_product import product_user_message
from handlers_recipes import recipes_callback  

# Импорт конфигурации (TOKEN_BOT)
from config import TOKEN_BOT


# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """
    Главная точка входа: создаём приложение, регистрируем ConversationHandler и запускаем бота.
    """
    application = ApplicationBuilder().token(TOKEN_BOT).build()

    # ConversationHandler описывает сценарий общения бота с пользователем.
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_menu)],
        states={
            MENU: [
                CallbackQueryHandler(menu_callback, pattern="^(about|ask_question|check_product|healthy_recipes|back_to_menu|...)$")
            ],
            GPT_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, gpt_user_message)
            ],
            CHECK_PRODUCT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, product_user_message)
            ],
            RECIPES: [
                CallbackQueryHandler(recipes_callback)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
