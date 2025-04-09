import logging
import os
import signal
import sys
from logging.handlers import RotatingFileHandler
from functools import wraps
from telegram.ext import (
    ApplicationBuilder,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    PicklePersistence,
    PersistenceInput
)
import time
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
import asyncio
from telegram.ext import CallbackContext

from utils.states import MENU, GPT_QUESTION, CHECK_PRODUCT, RECIPES

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
from database.database import (
    SessionLocal, 
    get_or_create_user, 
    get_or_create_session,
    end_user_session,
    log_user_interaction,
)
from database.crud import add_health_check  # Moved this import here
# Импорт хендлеров из отдельных файлов
from handlers.menu import start_menu, menu_callback, cancel
from handlers.gpt import handle_message
from handlers.product import product_user_message
from handlers.recipes import recipes_callback  
from database.models import ClientProfile

# Импорт конфигурации (TOKEN_BOT)
from utils.config import TOKEN_BOT, CHAT_ID

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
            
            # Сохраняем профиль пользователя в контексте для дальнейшего использования
            context.user_data['user_profile'] = user_profile
            
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
handle_message = track_user(handle_message)
product_user_message = track_user(product_user_message)
recipes_callback = track_user(recipes_callback)
cancel = track_user(cancel)

from stats_handler import get_stats

from handlers.stats import stats_recipes, stats_health, stats_users, stats_help

from handlers.broadcast import get_broadcast_handler, process_broadcasts
from handlers.admin import admin_commands

async def send_daily_message(context, chat_id):
    """Отправляет ежедневное сообщение пользователям."""
    # Получаем имя пользователя
    user = await context.bot.get_chat(chat_id)
    user_name = user.first_name if user.first_name else "пользователь"

    # Создаем кнопки с эмодзи в одну линию
    keyboard = [[
        InlineKeyboardButton("😢", callback_data='very_sad'),
        InlineKeyboardButton("😕", callback_data='sad'),
        InlineKeyboardButton("😐", callback_data='neutral'),
        InlineKeyboardButton("🙂", callback_data='good'),
        InlineKeyboardButton("😊", callback_data='very_good')
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение с обращением по имени
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Доброго дня, {user_name}! Как ты себя чувствуешь сегодня? Оцени своё состояние.",
        reply_markup=reply_markup
    )

    # Логируем успешную отправку
    bot_logger.info(f"Message sent successfully to user: {user_name} (ID: {chat_id})")


def schedule_daily_message(application):
    """Настраивает ежедневную отправку сообщений в 1:32 по московскому времени."""
    loop = asyncio.get_event_loop()
    scheduler = AsyncIOScheduler(event_loop=loop)
    moscow_tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(moscow_tz)
    next_run_time = now.replace(hour=12, minute=0, second=0, microsecond=0)
    if now >= next_run_time:
        next_run_time += timedelta(days=1)

    # Получаем всех пользователей из базы данных
    db = SessionLocal()
    try:
        users = db.query(ClientProfile).all()
        for user in users:
            bot_logger.info(f"Scheduling daily message for user: {user.username} (ID: {user.telegram_id})")
            # Добавляем задачу в планировщик для каждого пользователя
            scheduler.add_job(
                send_daily_message,
                'interval',
                days=1,
                start_date=next_run_time,
                args=[application, user.telegram_id]  # Передаем ID чата пользователя через args
            )
    finally:
        db.close()

    # Сохраняем scheduler как атрибут application для возможности остановки
    application.scheduler = scheduler
    
    scheduler.start()
    bot_logger.info("Daily message scheduler started.")

@track_user
async def handle_emoji_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает ответы пользователя на ежедневный опрос о самочувствии."""
    query = update.callback_query
    await query.answer()
    
    mood = query.data
    user = query.from_user
    user_name = user.first_name if user.first_name else "пользователь"
    
    # Создаем ключевые структуры данных, если они отсутствуют
    if 'user_data' not in context:
        context.user_data = {}
    if 'state' not in context.user_data:
        context.user_data['state'] = MENU
    
    # Сохраняем реакцию в базу данных
    db = SessionLocal()
    try:
        # Получаем или создаем профиль пользователя
        user_profile = get_or_create_user(
            db=db,
            telegram_id=str(user.id),
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Сохраняем обновленный профиль в контексте
        context.user_data['user_profile'] = user_profile
        
        # Сохраняем реакцию
        add_health_check(db=db, user_id=user_profile.id, mood=mood)
        
        # Отправляем подтверждение с обращением по имени
        mood_responses = {
            'very_sad': f'{user_name}, мне очень жаль, что ты чувствуешь себя плохо. Не стесняйся обратиться за помощью, если нужно! 🌅',
            'sad': f'{user_name}, жаль, что ты чувствуешь себя не очень. Надеюсь, завтра будет лучше! 🌅',
            'neutral': f'{user_name}, понятно. Надеюсь, завтра настроение будет лучше! ✨',
            'good': f'Отлично, {user_name}! Продолжай в том же духе! 🌟',
            'very_good': f'Замечательно, {user_name}! Очень рад, что у тебя всё отлично! 🌟'
        }
        
        await query.edit_message_text(
            text=mood_responses[mood]
        )
        
    finally:
        db.close()

def main():
    """
    Главная точка входа: создаём приложение, регистрируем ConversationHandler и запускаем бота.
    """
    bot_logger.info("Starting bot application...")
    
    try:
        # Import and initialize database here
        from database.database import init_db
        bot_logger.info("Initializing database...")
        init_db()
        bot_logger.info("Database initialized successfully")
        
        # Создаем объект персистентности для сохранения данных между перезапусками
        persistence_path = 'persistence/data'
        os.makedirs('persistence', exist_ok=True)
        
        try:
            bot_logger.info("Setting up persistence...")
            persistence = PicklePersistence(
                filepath=persistence_path,
                store_data=PersistenceInput(user_data=True, chat_data=True, bot_data=True, callback_data=True),
                single_file=True,
                on_flush=False,
                update_interval=60  # Сохраняем каждые 60 секунд
            )
            bot_logger.info("Persistence setup complete")
        except Exception as e:
            bot_logger.error(f"ERROR SETTING UP PERSISTENCE: {e}", exc_info=True)
            # Fallback to no persistence if there's an error
            bot_logger.info("Falling back to no persistence...")
            persistence = None
        
        try:
            bot_logger.info("Building application with persistence...")
            if persistence:
                application = ApplicationBuilder().token(TOKEN_BOT).persistence(persistence).build()
            else:
                application = ApplicationBuilder().token(TOKEN_BOT).build()
            bot_logger.info("Application built successfully")
        except Exception as e:
            bot_logger.error(f"ERROR BUILDING APPLICATION: {e}", exc_info=True)
            raise

        # Обработчик сигналов для плавного завершения
        def signal_handler(sig, frame):
            bot_logger.info(f"Received signal {sig}, shutting down gracefully...")
            # Остановить планировщик задач
            if hasattr(application, 'scheduler') and application.scheduler:
                application.scheduler.shutdown()
            # Завершить работу бота
            application.stop()
            sys.exit(0)
        
        bot_logger.info("Setting up signal handlers...")
        # Регистрируем обработчики сигналов
        signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # kill
        
        if hasattr(signal, 'SIGBREAK'):  # Windows
            signal.signal(signal.SIGBREAK, signal_handler)
        bot_logger.info("Signal handlers configured")

        bot_logger.info("Registering command handlers...")
        # Добавляем обработчик команды админа
        application.add_handler(CommandHandler("admin", admin_commands))

        # Добавляем обработчики команд статистики
        application.add_handler(CommandHandler("stats_recipes", stats_recipes))
        application.add_handler(CommandHandler("stats_health", stats_health))
        application.add_handler(CommandHandler("stats_users", stats_users))
        application.add_handler(CommandHandler("stats_help", stats_help))
        bot_logger.info("Command handlers registered")

        bot_logger.info("Setting up broadcast handler...")
        # Добавляем обработчик рассылок
        application.add_handler(get_broadcast_handler())
        bot_logger.info("Broadcast handler configured")

        bot_logger.info("Setting up table handlers...")
        # Добавляем обработчики команд для таблиц
        from handlers.tables import (
            table_users, table_sessions, table_interactions,
            table_ratings, table_health, table_broadcasts
        )
        application.add_handler(CommandHandler("table_users", table_users))
        application.add_handler(CommandHandler("table_sessions", table_sessions))
        application.add_handler(CommandHandler("table_interactions", table_interactions))
        application.add_handler(CommandHandler("table_ratings", table_ratings))
        application.add_handler(CommandHandler("table_health", table_health))
        application.add_handler(CommandHandler("table_broadcasts", table_broadcasts))
        bot_logger.info("Table handlers configured")

        # Добавляем обработчик для всех текстовых сообщений вне ConversationHandler
        # Если пользователь пишет сообщение без вызова /start, бот ответит как если бы команда была вызвана
        bot_logger.info("Adding fallback message handler for non-conversation messages...")
        
        async def fallback_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Обрабатывает текстовые сообщения вне ConversationHandler (когда бот перезапущен)"""
            bot_logger.info(f"Received message outside of conversation from user {update.effective_user.id}")
            
            # Создаем ключевые структуры данных, если они отсутствуют
            if 'user_data' not in context:
                context.user_data = {}
            if 'state' not in context.user_data:
                context.user_data['state'] = MENU
                
            user = update.effective_user
            if update.message and update.message.text.strip().lower() in ['привет', 'начать', 'старт', 'меню', '/start']:
                # Если это приветственное сообщение, показываем стартовое меню
                return await start_menu(update, context)
            else:
                # Иначе обрабатываем как обычный запрос через GPT
                bot_logger.info(f"Processing message as GPT query: '{update.message.text}'")
                return await handle_message(update, context)
        
        # Обработчик неизвестных команд
        async def unknown_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Обрабатывает неизвестные команды вне ConversationHandler"""
            bot_logger.info(f"Received unknown command from user {update.effective_user.id}: {update.message.text}")
            
            # Создаем ключевые структуры данных, если они отсутствуют
            if 'user_data' not in context:
                context.user_data = {}
            if 'state' not in context.user_data:
                context.user_data['state'] = MENU
            
            # Предлагаем пользователю перейти к началу взаимодействия
            await update.message.reply_text(
                "Извини, я не знаю эту команду. Напиши /start, чтобы начать общение, или просто задай мне вопрос! 😊"
            )
            
            return MENU
        
        # Добавляем обработчики до основного ConversationHandler
        # Это важно, так как ConversationHandler имеет приоритет над обычными обработчиками
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_text_handler), group=1)
        bot_logger.info("Fallback text handler added")
        
        # Добавляем обработчик для неизвестных команд с тем же приоритетом
        application.add_handler(MessageHandler(filters.COMMAND & ~filters.Regex(r'^/start'), unknown_command_handler), group=1)
        bot_logger.info("Unknown command handler added")

        # ConversationHandler описывает сценарий общения бота с пользователем.
        bot_logger.info("Configuring conversation handler...")
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start_menu)],
            states={
                MENU: [
                    CallbackQueryHandler(menu_callback, pattern="^(about|check_product|healthy_recipes|back_to_menu|breakfast|poldnik|lunch|dinner|bcat_.*|bitem_.*|pcat_.*|pitem_.*|lcat_.*|litem_.*|dcat_.*|ditem_.*|rate_recipe|rating_.*|ignore_rating|category_.*|dish_.*|drinks|drinks_cat_.*|drinks_name_.*)$"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)  # Обработка всех текстовых сообщений через GPT
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
            allow_reentry=True,
            name="main_conversation",  # Добавим имя для отладки
            persistent=True  # Включаем сохранение состояния между перезапусками
        )
        bot_logger.info("Adding conversation handler to application...")
        application.add_handler(conv_handler)
        bot_logger.info("Conversation handler added")

        bot_logger.info("Setting up emoji response handler...")
        # Добавляем обработчик для нажатий на эмодзи
        application.add_handler(CallbackQueryHandler(handle_emoji_response, pattern="^(very_sad|sad|neutral|good|very_good)$"))
        bot_logger.info("Emoji handler configured")

        bot_logger.info("Configuring job queue...")
        # Настраиваем проверку рассылок каждую минуту
        job_queue = application.job_queue
        job_queue.run_repeating(process_broadcasts, interval=60)
        bot_logger.info("Job queue configured")

        bot_logger.info("Setting up daily messages...")
        # Вызов функции schedule_daily_message в main()
        schedule_daily_message(application)
        bot_logger.info("Daily messages scheduled")

        bot_logger.info("Starting polling...")
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        bot_logger.info("Bot stopped")
        
    except Exception as e:
        bot_logger.error(f"ERROR DURING BOT INITIALIZATION: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
