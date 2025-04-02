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
import time
from datetime import datetime

from states import MENU, GPT_QUESTION, CHECK_PRODUCT, RECIPES

# Set up logging first
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

# Import database and models
from database import (
    SessionLocal, 
    get_or_create_user, 
    get_or_create_session,
    end_user_session,
    log_user_interaction,
        
)
# Импорт хендлеров из отдельных файлов
from handlers_menu import start_menu, menu_callback, cancel
from handlers_gpt import gpt_user_message
from handlers_product import product_user_message
from handlers_recipes import recipes_callback  

# Импорт конфигурации (TOKEN_BOT)
from config import TOKEN_BOT

# Dictionary to store active sessions
active_sessions = {}

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
        start_time = time.time()
        
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
            
            # Handle session tracking
            if handler_name == 'start_menu':
                # Create new session when user starts bot
                session = get_or_create_session(db, user_profile.id)
                active_sessions[user.id] = session.id
                bot_logger.info(f"Created new session for user {user.id}: {session.id}")
            elif handler_name == 'cancel':
                # End session when user cancels
                if user.id in active_sessions:
                    session_id = active_sessions[user.id]
                    end_user_session(db, session_id)
                    del active_sessions[user.id]
                    bot_logger.info(f"Ended session {session_id} for user {user.id}")

            # Log the interaction
            action_type = handler_name
            action_data = str(update.callback_query.data) if update.callback_query else str(update.message.text) if update.message else None
            
            # Call the original handler function
            bot_logger.debug(f"Calling original handler: {handler_name}")
            result = await func(update, context, *args, **kwargs)
            
            # Calculate response time
            response_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
            
            # Log successful interaction
            log_user_interaction(
                db=db,
                user_id=user_profile.id,
                action_type=action_type,
                action_data=action_data,
                response_time=response_time,
                success=True
            )
            
            return result
            
        except Exception as e:
            bot_logger.error(f"Error tracking user: {e}", exc_info=True)
            # Log failed interaction
            if 'user_profile' in locals():
                log_user_interaction(
                    db=db,
                    user_id=user_profile.id,
                    action_type=handler_name,
                    action_data=str(e),
                    response_time=int((time.time() - start_time) * 1000),
                    success=False
                )
            # Still call the original function even if tracking fails
            return await func(update, context, *args, **kwargs)
        finally:
            bot_logger.debug(f"Closing database session for user: {user.id}")
            db.close()
            
    return wrapper

# Apply the track_user decorator to all handler functions
start_menu = track_user(start_menu)
menu_callback = track_user(menu_callback)
gpt_user_message = track_user(gpt_user_message)
product_user_message = track_user(product_user_message)
recipes_callback = track_user(recipes_callback)
cancel = track_user(cancel)

from stats_handler import get_stats

def main():
    """
    Главная точка входа: создаём приложение, регистрируем ConversationHandler и запускаем бота.
    """
    bot_logger.info("Starting bot application...")
    
    # Import and initialize database here
    from database import init_db
    bot_logger.info("Initializing database...")
    init_db()
    bot_logger.info("Database initialized successfully")
    
    application = ApplicationBuilder().token(TOKEN_BOT).build()

    # Add stats command handler
    application.add_handler(CommandHandler("stats", get_stats))

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

    bot_logger.info("Bot started and running...")
    application.run_polling()


if __name__ == "__main__":
    main()
