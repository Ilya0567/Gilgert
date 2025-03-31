import logging
import os
from logging.handlers import RotatingFileHandler
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

from database import init_db, SessionLocal, get_or_create_user, Base

# Настройка логирования
LOG_FILENAME = 'bot.log'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Ensure the log directory exists
os.makedirs('logs', exist_ok=True)
log_file_path = os.path.join('logs', LOG_FILENAME)

# Create handlers for both console and file output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

file_handler = RotatingFileHandler(
    log_file_path, 
    maxBytes=10*1024*1024,  # 10MB max file size
    backupCount=5  # Keep 5 backup files
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# Configure the root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Get a module-specific logger
bot_logger = logging.getLogger(__name__)

# Decorator for tracking user interactions
def track_user(func):
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        # Extract user information
        user = update.effective_user
        handler_name = func.__name__
        
        bot_logger.info(f"Handler called: {handler_name} by user: {user.id} ({user.username or 'No username'})")
        
        # Create a database session
        db = SessionLocal()
        try:
            bot_logger.info(f"Checking if user {user.id} exists in database...")
            
            # Get or create user profile
            user_profile = get_or_create_user(
                db=db,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            if user_profile.interaction_count == 1:
                bot_logger.info(f"NEW USER created: {user.id} ({user.username or 'No username'}) - {user.first_name} {user.last_name or ''}")
            else:
                bot_logger.info(f"Existing user found: {user.id} ({user.username or 'No username'}) - interaction count: {user_profile.interaction_count}")
            
            # Call the original handler function
            bot_logger.debug(f"Calling original handler: {handler_name}")
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            bot_logger.error(f"Error tracking user: {e}", exc_info=True)
            # Still call the original function even if tracking fails
            return await func(update, context, *args, **kwargs)
        finally:
            bot_logger.debug(f"Closing database session for user: {user.id}")
            db.close()
            
    return wrapper

# Apply the track_user decorator to all handler functions
init_db()
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
    bot_logger.info("Starting bot application...")
    application = ApplicationBuilder().token(TOKEN_BOT).build()

    # ConversationHandler описывает сценарий общения бота с пользователем.
    bot_logger.info("Configuring conversation handler...")
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
    bot_logger.info("Initializing database...")
    init_db()
    bot_logger.info("Database initialized successfully")

    bot_logger.info("Bot started and running...")
    application.run_polling()


if __name__ == "__main__":
    main()
