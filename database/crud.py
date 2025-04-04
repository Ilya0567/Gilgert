# crud.py

from sqlalchemy.orm import Session
from .models import ClientProfile, RecipeRating
import logging

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