from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database.database import SessionLocal
from database.models import RecipeRating
from sqlalchemy import func

async def get_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get statistics about recipe ratings."""
    db = SessionLocal()
    try:
        # Get average ratings per recipe type
        avg_ratings = (
            db.query(
                RecipeRating.recipe_type,
                func.avg(RecipeRating.rating).label('avg_rating'),
                func.count(RecipeRating.id).label('total_ratings')
            )
            .group_by(RecipeRating.recipe_type)
            .all()
        )

        # Format the statistics message
        stats_message = "📊 Статистика оценок рецептов:\n\n"
        
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

        # Add back button
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.message:
            await update.message.reply_text(stats_message, reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.edit_message_text(stats_message, reply_markup=reply_markup)

    finally:
        db.close() 