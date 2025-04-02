from telegram import Update
from telegram.ext import ContextTypes
from database import SessionLocal
from models import ClientProfile, UserSession, UserInteraction, RecipeRating

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