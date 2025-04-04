from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import SessionLocal
from models import ClientProfile, UserSession, UserInteraction, RecipeRating
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import pytz

async def get_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for getting user statistics"""
    user = update.effective_user
    
    # Check if user is authorized to view stats
    if str(user.id) != "669201758":
        await update.message.reply_text("⛔️ Sorry, you are not authorized to view statistics.")
        return
    
    db = SessionLocal()
    try:
        # Получаем данные из всех таблиц
        client_profiles = db.query(ClientProfile).all()
        user_sessions = db.query(UserSession).all()
        user_interactions = db.query(UserInteraction).all()
        recipe_ratings = db.query(RecipeRating).all()

        # Формируем сообщение с данными
        messages = []
        messages.append("📊 Содержание всех таблиц:\n\n")
        messages.append("Client Profiles:\n" + "\n".join([str(profile) for profile in client_profiles]) + "\n\n")
        messages.append("User Sessions:\n" + "\n".join([str(session) for session in user_sessions]) + "\n\n")
        messages.append("User Interactions:\n" + "\n".join([str(interaction) for interaction in user_interactions]) + "\n\n")
        messages.append("Recipe Ratings:\n" + "\n".join([str(rating) for rating in recipe_ratings]) + "\n\n")
        
        # Отправляем каждую часть сообщения отдельно
        for message in messages:
            if len(message) > 4096:  # Telegram ограничивает длину сообщения 4096 символами
                for i in range(0, len(message), 4096):
                    await update.message.reply_text(message[i:i+4096])
            else:
                await update.message.reply_text(message)
        
    finally:
        db.close()

async def send_daily_message(context):
    """Отправляет ежедневное сообщение пользователям."""
    job = context.job
    chat_id = job.context

    # Получаем имя пользователя
    user = await context.bot.get_chat(chat_id)
    user_name = user.first_name

    # Создаем кнопки с эмодзи
    keyboard = [
        [InlineKeyboardButton("😢", callback_data='sad')],
        [InlineKeyboardButton("😐", callback_data='neutral')],
        [InlineKeyboardButton("😊", callback_data='happy')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Привет, {user_name}! Как ты себя чувствуешь, как настроение? Оцени своё состояние.",
        reply_markup=reply_markup
    )

def schedule_daily_message(application):
    """Настраивает ежедневную отправку сообщений в 1:00 по московскому времени."""
    scheduler = AsyncIOScheduler()
    moscow_tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(moscow_tz)
    next_run_time = now.replace(hour=1, minute=0, second=0, microsecond=0)
    if now >= next_run_time:
        next_run_time += timedelta(days=1)

    # Добавляем задачу в планировщик
    scheduler.add_job(
        send_daily_message,
        'interval',
        days=1,
        start_date=next_run_time,
        args=[application],
        context=YOUR_CHAT_ID  # Замените на ID чата пользователя
    )
    scheduler.start()

def main():
    bot_logger.info("Starting bot application...")
    
    from database import init_db
    bot_logger.info("Initializing database...")
    init_db()
    bot_logger.info("Database initialized successfully")
    
    application = ApplicationBuilder().token(TOKEN_BOT).build()

    # Add stats command handler
    application.add_handler(CommandHandler("stats", get_stats))

    # Настраиваем ежедневную отправку сообщений
    schedule_daily_message(application)

    # ConversationHandler описывает сценарий общения бота с пользователем.
    bot_logger.info("Configuring conversation handler...")
    # ... остальной код ... 