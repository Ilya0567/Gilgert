import logging
from functools import wraps
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

from database import init_db, SessionLocal, get_or_create_user

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Decorator for tracking user interactions
def track_user(func):
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        # Extract user information
        user = update.effective_user
        
        # Create a database session
        db = SessionLocal()
        try:
            # Get or create user profile
            user_profile = get_or_create_user(
                db=db,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            # Log user interaction
            logger.info(f"User interaction: {user.id} ({user.username}), interaction count: {user_profile.interaction_count}")
            
            # Call the original handler function
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error tracking user: {e}")
            # Still call the original function even if tracking fails
            return await func(update, context, *args, **kwargs)
        finally:
            db.close()
            
    return wrapper

# Apply the track_user decorator to all handler functions
start_menu = track_user(start_menu)
menu_callback = track_user(menu_callback)
gpt_user_message = track_user(gpt_user_message)
product_user_message = track_user(product_user_message)
recipes_callback = track_user(recipes_callback)
cancel = track_user(cancel)

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
                MessageHandler(filters.TEXT & ~filters.COMMAND, gpt_user_message),
                # И ловим колбэки "back_to_menu" 
                CallbackQueryHandler(menu_callback, pattern="^back_to_menu$")
            ],
            CHECK_PRODUCT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, product_user_message),
                CallbackQueryHandler(menu_callback, pattern="^back_to_menu$")
            ],
            RECIPES: [
                CallbackQueryHandler(recipes_callback)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    application.add_handler(conv_handler)

    # Initialize the database
    init_db()

    # Example of using a session
    # with SessionLocal() as session:
    #     # Perform database operations here
    #     pass

    application.run_polling()


if __name__ == "__main__":
    main()
