import logging
from telegram.ext import (
    ApplicationBuilder,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

# Импорт хендлеров из отдельных файлов
from handlers_menu import start_menu, menu_callback, cancel
from handlers_gpt import gpt_question_answer
from handlers_product import product_check_answer
from handlers_recipes import recipes_submenu_callback

# Импорт конфигурации (TOKEN_BOT)
from config import TOKEN_BOT

# Определяем «ID состояний» (enum-like) для ConversationHandler
MENU, GPT_QUESTION, CHECK_PRODUCT, RECIPES = range(4)

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
        entry_points=[CommandHandler("start", start_menu)],  # Точка входа (команда /start)
        states={
            MENU: [
                CallbackQueryHandler(menu_callback, pattern="^(about|ask_question|check_product|healthy_recipes|back_to_menu)$")
            ],
            GPT_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, gpt_question_answer)
            ],
            CHECK_PRODUCT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, product_check_answer)
            ],
            RECIPES: [
                CallbackQueryHandler(recipes_submenu_callback)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
