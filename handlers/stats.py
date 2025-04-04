from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from datetime import datetime, timedelta

from database.database import SessionLocal
from database.models import RecipeRating, DailyHealthCheck, ClientProfile
from database.crud import get_user_health_stats
from sqlalchemy import func
from utils.config import ADMIN_ID  # Добавь свой Telegram ID в config.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
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

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь админом"""
    return str(user_id) == str(ADMIN_ID)

async def check_admin(update: Update) -> bool:
    """Проверяет права админа и отправляет сообщение если нет доступа"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.")
        return False
    return True

async def stats_recipes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Статистика по рецептам"""
    if not await check_admin(update):
        return

    db = SessionLocal()
    try:
        # Получаем статистику по рецептам
        avg_ratings = (
            db.query(
                RecipeRating.recipe_type,
                func.avg(RecipeRating.rating).label('avg_rating'),
                func.count(RecipeRating.id).label('total_ratings')
            )
            .group_by(RecipeRating.recipe_type)
            .all()
        )

        stats_message = "📊 Статистика рецептов:\n\n"
        
        type_names = {
            'breakfast': 'Завтраки',
            'lunch': 'Обеды',
            'poldnik': 'Полдники',
            'drink': 'Напитки'
        }
        
        for recipe_type, avg_rating, total in avg_ratings:
            display_name = type_names.get(recipe_type, recipe_type)
            stats_message += f"{display_name}:\n"
            stats_message += f"⭐ Средняя оценка: {avg_rating:.1f}\n"
            stats_message += f"📝 Всего оценок: {total}\n\n"

        if not avg_ratings:
            stats_message = "Пока нет оценок рецептов."

        await update.message.reply_text(stats_message)

    finally:
        db.close()

async def stats_health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Статистика по настроению пользователей"""
    if not await check_admin(update):
        return

    db = SessionLocal()
    try:
        # Получаем статистику за последние 30 дней
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # Общая статистика по настроению
        mood_stats = (
            db.query(
                DailyHealthCheck.mood,
                func.count(DailyHealthCheck.id).label('count')
            )
            .filter(DailyHealthCheck.timestamp >= thirty_days_ago)
            .group_by(DailyHealthCheck.mood)
            .all()
        )

        # Количество активных пользователей
        active_users = (
            db.query(func.count(func.distinct(DailyHealthCheck.user_id)))
            .filter(DailyHealthCheck.timestamp >= thirty_days_ago)
            .scalar()
        )

        stats_message = "🎭 Статистика настроения (за 30 дней):\n\n"
        
        total_responses = sum(count for _, count in mood_stats)
        
        mood_names = {
            'happy': '😊 Хорошее',
            'neutral': '😐 Нейтральное',
            'sad': '😢 Грустное'
        }
        
        for mood, count in mood_stats:
            percentage = (count / total_responses * 100) if total_responses > 0 else 0
            stats_message += f"{mood_names.get(mood, mood)}:\n"
            stats_message += f"Количество: {count} ({percentage:.1f}%)\n\n"
        
        stats_message += f"👥 Активных пользователей: {active_users}\n"
        stats_message += f"📝 Всего ответов: {total_responses}"

        await update.message.reply_text(stats_message)

    finally:
        db.close()

async def stats_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Статистика по пользователям"""
    if not await check_admin(update):
        return

    db = SessionLocal()
    try:
        # Общее количество пользователей
        total_users = db.query(func.count(ClientProfile.id)).scalar()
        
        # Активные пользователи за последние 7 дней
        week_ago = datetime.now() - timedelta(days=7)
        active_users_week = (
            db.query(func.count(func.distinct(ClientProfile.id)))
            .filter(ClientProfile.last_interaction >= week_ago)
            .scalar()
        )

        # Новые пользователи за последние 7 дней
        new_users_week = (
            db.query(func.count(ClientProfile.id))
            .filter(ClientProfile.created_at >= week_ago)
            .scalar()
        )

        stats_message = "👥 Статистика пользователей:\n\n"
        stats_message += f"Всего пользователей: {total_users}\n"
        stats_message += f"Активных за неделю: {active_users_week}\n"
        stats_message += f"Новых за неделю: {new_users_week}\n"

        await update.message.reply_text(stats_message)

    finally:
        db.close()

async def stats_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает список доступных команд статистики"""
    if not await check_admin(update):
        return

    help_message = "📊 Доступные команды статистики:\n\n"
    help_message += "/stats_recipes - Статистика по рецептам\n"
    help_message += "/stats_health - Статистика настроения\n"
    help_message += "/stats_users - Статистика пользователей\n"
    help_message += "/stats_help - Это сообщение"

    await update.message.reply_text(help_message)

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