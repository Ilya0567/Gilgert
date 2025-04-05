from telegram import Update
from telegram.ext import ContextTypes
from database.database import SessionLocal
from database.models import ClientProfile, UserSession, UserInteraction, RecipeRating, DailyHealthCheck, BroadcastMessage
from .admin import check_admin
from sqlalchemy import desc

async def get_table_data(model, limit=10):
    """Get last records from table"""
    db = SessionLocal()
    try:
        records = db.query(model).order_by(desc(model.id)).limit(limit).all()
        return records
    finally:
        db.close()

async def get_all_users():
    """Get all users"""
    db = SessionLocal()
    try:
        users = db.query(ClientProfile).order_by(desc(ClientProfile.id)).all()
        return users
    finally:
        db.close()

async def format_table_data(records, model):
    """Format table data for display"""
    if not records:
        return "Нет данных"
        
    result = ""
    
    if model == ClientProfile:
        for record in records:
            result += f"ID: {record.id}\n"
            result += f"Telegram ID: {record.telegram_id}\n"
            result += f"Username: {record.username}\n"
            result += f"Name: {record.first_name} {record.last_name}\n"
            result += f"Active: {record.is_active}\n"
            result += f"Created: {record.created_at}\n"
            result += f"Last interaction: {record.last_interaction}\n"
            result += f"Interactions: {record.interaction_count}\n"
            result += "---\n"
            
    elif model == UserSession:
        for record in records:
            result += f"ID: {record.id}\n"
            result += f"User ID: {record.user_id}\n"
            result += f"Start: {record.start_time}\n"
            result += f"End: {record.end_time}\n"
            result += f"Duration: {record.session_duration}s\n"
            result += f"Source: {record.source}\n"
            result += f"Last command: {record.last_command}\n"
            result += f"Completed: {record.is_completed}\n"
            result += "---\n"
            
    elif model == UserInteraction:
        for record in records:
            result += f"ID: {record.id}\n"
            result += f"User ID: {record.user_id}\n"
            result += f"Session ID: {record.session_id}\n"
            result += f"Time: {record.timestamp}\n"
            result += f"Type: {record.action_type}\n"
            result += f"Data: {record.action_data}\n"
            result += f"Response time: {record.response_time}ms\n"
            result += f"Success: {record.success}\n"
            result += "---\n"
            
    elif model == RecipeRating:
        for record in records:
            result += f"ID: {record.id}\n"
            result += f"User ID: {record.user_id}\n"
            result += f"Recipe: {record.recipe_name}\n"
            result += f"Type: {record.recipe_type}\n"
            result += f"Rating: {record.rating}\n"
            result += f"Time: {record.timestamp}\n"
            result += "---\n"
            
    elif model == DailyHealthCheck:
        for record in records:
            result += f"ID: {record.id}\n"
            result += f"User ID: {record.user_id}\n"
            result += f"Mood: {record.mood}\n"
            result += f"Time: {record.timestamp}\n"
            result += "---\n"
            
    elif model == BroadcastMessage:
        for record in records:
            result += f"ID: {record.id}\n"
            result += f"Admin ID: {record.admin_id}\n"
            result += f"Message: {record.message}\n"
            result += f"Scheduled: {record.scheduled_time}\n"
            result += f"Sent: {record.sent}\n"
            result += f"Created: {record.created_at}\n"
            result += f"Sent at: {record.sent_at}\n"
            result += "---\n"
            
    return result

async def table_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show users table"""
    if not await check_admin(update):
        return
        
    records = await get_all_users()
    formatted_data = await format_table_data(records, ClientProfile)
    await update.message.reply_text(formatted_data)

async def table_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show last 10 sessions"""
    if not await check_admin(update):
        return
        
    records = await get_table_data(UserSession)
    formatted_data = await format_table_data(records, UserSession)
    await update.message.reply_text(formatted_data)

async def table_interactions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show last 10 interactions"""
    if not await check_admin(update):
        return
        
    records = await get_table_data(UserInteraction)
    formatted_data = await format_table_data(records, UserInteraction)
    await update.message.reply_text(formatted_data)

async def table_ratings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show last 10 recipe ratings"""
    if not await check_admin(update):
        return
        
    records = await get_table_data(RecipeRating)
    formatted_data = await format_table_data(records, RecipeRating)
    await update.message.reply_text(formatted_data)

async def table_health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show last 10 health checks"""
    if not await check_admin(update):
        return
        
    records = await get_table_data(DailyHealthCheck)
    formatted_data = await format_table_data(records, DailyHealthCheck)
    await update.message.reply_text(formatted_data)

async def table_broadcasts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show last 10 broadcast messages"""
    if not await check_admin(update):
        return
        
    records = await get_table_data(BroadcastMessage)
    formatted_data = await format_table_data(records, BroadcastMessage)
    await update.message.reply_text(formatted_data) 