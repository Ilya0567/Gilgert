# crud.py

from sqlalchemy.orm import Session
from .models import ClientProfile, RecipeRating, DailyHealthCheck, BroadcastMessage
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def get_or_create_user(
    db: Session,
    telegram_id: int,
    username: str = None,
    first_name: str = None,
    last_name: str = None
) -> ClientProfile:
    """
    Get existing user or create new one if doesn't exist.
    """
    user = db.query(ClientProfile).filter(ClientProfile.telegram_id == str(telegram_id)).first()
    
    if not user:
        user = ClientProfile(
            telegram_id=str(telegram_id),
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created new user profile for telegram_id {telegram_id}")
    else:
        # Update user info if changed
        if username != user.username or first_name != user.first_name or last_name != user.last_name:
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            db.commit()
            logger.info(f"Updated user profile for telegram_id {telegram_id}")
    
    return user

def add_recipe_rating(
    db: Session,
    user_id: int,
    recipe_type: str,
    recipe_name: str,
    rating: int
) -> RecipeRating:
    """
    Add a new recipe rating to the database.
    """
    if not 1 <= rating <= 5:
        raise ValueError("Rating must be between 1 and 5")

    # Create new rating
    recipe_rating = RecipeRating(
        user_id=user_id,
        recipe_type=recipe_type,
        recipe_name=recipe_name,
        rating=rating
    )
    
    db.add(recipe_rating)
    db.commit()
    db.refresh(recipe_rating)
    
    logger.info(f"Added rating {rating} for recipe '{recipe_name}' ({recipe_type}) by user {user_id}")
    return recipe_rating

def get_user_ratings(db: Session, user_id: int) -> list[RecipeRating]:
    """
    Get all ratings by a specific user.
    """
    return db.query(RecipeRating).filter(RecipeRating.user_id == user_id).all()

def get_recipe_ratings(db: Session, recipe_type: str, recipe_name: str) -> list[RecipeRating]:
    """
    Get all ratings for a specific recipe.
    """
    return db.query(RecipeRating).filter(
        RecipeRating.recipe_type == recipe_type,
        RecipeRating.recipe_name == recipe_name
    ).all()

def get_recipe_average_rating(db: Session, recipe_type: str, recipe_name: str) -> float:
    """
    Get average rating for a specific recipe.
    Returns 0 if no ratings exist.
    """
    ratings = get_recipe_ratings(db, recipe_type, recipe_name)
    if not ratings:
        return 0.0
    return sum(r.rating for r in ratings) / len(ratings)

def add_health_check(
    db: Session,
    user_id: int,
    mood: str
) -> DailyHealthCheck:
    """
    Add a new health check response to the database.
    Args:
        db: Database session
        user_id: ID of the user
        mood: One of 'sad', 'neutral', 'happy'
    """
    if mood not in ['sad', 'neutral', 'happy']:
        raise ValueError("Mood must be one of: sad, neutral, happy")

    health_check = DailyHealthCheck(
        user_id=user_id,
        mood=mood
    )
    
    db.add(health_check)
    db.commit()
    db.refresh(health_check)
    
    logger.info(f"Added health check for user {user_id}: {mood}")
    return health_check

def get_user_health_stats(db: Session, user_id: int, days: int = 30) -> dict:
    """
    Get health check statistics for a user over the last N days.
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Get all health checks for this period
    checks = db.query(DailyHealthCheck).filter(
        DailyHealthCheck.user_id == user_id,
        DailyHealthCheck.timestamp >= cutoff_date
    ).all()
    
    # Count moods
    stats = {
        'total_checks': len(checks),
        'happy': sum(1 for c in checks if c.mood == 'happy'),
        'neutral': sum(1 for c in checks if c.mood == 'neutral'),
        'sad': sum(1 for c in checks if c.mood == 'sad'),
        'days_tracked': days
    }
    
    # Calculate percentages if there are any checks
    if stats['total_checks'] > 0:
        stats['happy_percent'] = (stats['happy'] / stats['total_checks']) * 100
        stats['neutral_percent'] = (stats['neutral'] / stats['total_checks']) * 100
        stats['sad_percent'] = (stats['sad'] / stats['total_checks']) * 100
    
    return stats

def create_broadcast(
    db: Session,
    admin_id: int,
    message: str,
    scheduled_time: datetime
) -> BroadcastMessage:
    """
    Create a new broadcast message
    """
    broadcast = BroadcastMessage(
        admin_id=admin_id,
        message=message,
        scheduled_time=scheduled_time
    )
    
    db.add(broadcast)
    db.commit()
    db.refresh(broadcast)
    
    logger.info(f"Created broadcast message scheduled for {scheduled_time}")
    return broadcast

def get_pending_broadcasts(db: Session) -> list[BroadcastMessage]:
    """
    Get all broadcasts that haven't been sent and are due to be sent
    """
    return (
        db.query(BroadcastMessage)
        .filter(
            BroadcastMessage.sent == False,
            BroadcastMessage.scheduled_time <= datetime.now()
        )
        .all()
    )

def mark_broadcast_sent(db: Session, broadcast_id: int) -> None:
    """
    Mark a broadcast as sent
    """
    broadcast = db.query(BroadcastMessage).filter(BroadcastMessage.id == broadcast_id).first()
    if broadcast:
        broadcast.sent = True
        broadcast.sent_at = datetime.now()
        db.commit()
        logger.info(f"Marked broadcast {broadcast_id} as sent")

def get_all_active_users(db: Session) -> list[ClientProfile]:
    """
    Get all users that have interacted with the bot
    """
    return db.query(ClientProfile).filter(ClientProfile.is_active == True).all() 