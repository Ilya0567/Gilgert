# crud.py

from sqlalchemy.orm import Session
from .models import ClientProfile, RecipeRating, DailyHealthCheck, BroadcastMessage, UserSurveyStatus
from database.models import UserConversation
import logging
from datetime import datetime, timedelta
import json

# Создаем логгер для этого модуля
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

# Функции для работы с историей диалогов

def save_conversation_history(db: Session, user_id: int, messages: list):
    """
    Сохраняет историю диалога пользователя в базу данных
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        messages: Список сообщений в формате [{role: 'user', content: '...'}, {role: 'assistant', content: '...'}]
    """
    try:
        # Проверяем, что пользователь существует
        user = db.query(ClientProfile).filter(ClientProfile.id == user_id).first()
        if not user:
            logger.error(f"Пользователь с ID {user_id} не найден в базе данных")
            return None
            
        # Создаем новую запись
        conversation = UserConversation(
            user_id=user_id,
            messages=messages if messages else []
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        logger.info(f"Сохранена история диалога для пользователя {user_id}, ID записи: {conversation.id}")
        return conversation
    except Exception as e:
        logger.error(f"Ошибка сохранения истории диалога: {e}", exc_info=True)
        db.rollback()
        return None

def get_user_conversation_history(db: Session, user_id: int, limit: int = 20):
    """
    Получает историю диалога пользователя из базы данных
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        limit: Максимальное количество сообщений для возврата
    
    Returns:
        list: Список сообщений в формате для отправки в GPT API
    """
    try:
        # Получаем последнюю запись в истории диалогов пользователя
        conversation = db.query(UserConversation)\
            .filter(UserConversation.user_id == user_id)\
            .order_by(UserConversation.timestamp.desc())\
            .first()
        
        if conversation:
            # Если есть история, возвращаем сообщения
            logger.info(f"Найдена история диалога для пользователя {user_id}, ID записи: {conversation.id}")
            # Проверяем, что messages - это список
            if conversation.messages and isinstance(conversation.messages, list):
                return conversation.messages[-limit:] if conversation.messages else []
            else:
                logger.warning(f"История диалога для пользователя {user_id} имеет неправильный формат: {type(conversation.messages)}")
                return []
        logger.info(f"История диалога для пользователя {user_id} не найдена")
        return []
    except Exception as e:
        logger.error(f"Ошибка при получении истории диалога: {e}", exc_info=True)
        return []

def update_conversation_history(db: Session, user_id: int, messages: list):
    """
    Updates the most recent conversation history for a user with new messages.
    
    Args:
        db: Database session
        user_id: The ID of the user
        messages: List of message dicts to append
    
    Returns:
        The updated UserConversation object
    """
    try:
        # Проверяем, что пользователь существует
        user = db.query(ClientProfile).filter(ClientProfile.id == user_id).first()
        if not user:
            logger.error(f"Пользователь с ID {user_id} не найден в базе данных при обновлении истории")
            return None
            
        # Find the most recent conversation for this user
        conversation = (
            db.query(UserConversation)
            .filter(UserConversation.user_id == user_id)
            .order_by(UserConversation.timestamp.desc())
            .first()
        )
        
        # If conversation exists, update it
        if conversation:
            logger.info(f"Обновляем существующую историю диалога (ID: {conversation.id}) для пользователя {user_id}")
            conversation.messages = messages if messages else []
            conversation.timestamp = datetime.now()  # Обновляем время для отображения в порядке последних изменений
            db.commit()
            db.refresh(conversation)
            return conversation
        
        # Otherwise create a new conversation
        logger.info(f"Создаем новую запись истории диалога для пользователя {user_id}")
        return save_conversation_history(db, user_id, messages)
    except Exception as e:
        logger.error(f"Ошибка при обновлении истории диалога: {e}", exc_info=True)
        db.rollback()
        return None

# Функции для работы с анкетами пользователей

def get_user_survey_status(db: Session, user_id: int) -> UserSurveyStatus:
    """
    Получает статус заполнения анкеты пользователем
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        
    Returns:
        Объект статуса анкеты или None если записи нет
    """
    return db.query(UserSurveyStatus).filter(UserSurveyStatus.user_id == user_id).first()

def get_or_create_survey_status(db: Session, user_id: int) -> UserSurveyStatus:
    """
    Получает или создает запись о статусе анкеты пользователя
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        
    Returns:
        Объект статуса анкеты
    """
    survey_status = get_user_survey_status(db, user_id)
    
    if not survey_status:
        survey_status = UserSurveyStatus(
            user_id=user_id,
            is_completed=False
        )
        db.add(survey_status)
        db.commit()
        db.refresh(survey_status)
        logger.info(f"Создан новый статус анкеты для пользователя {user_id}")
    
    return survey_status

def mark_survey_completed(db: Session, user_id: int) -> UserSurveyStatus:
    """
    Отмечает анкету пользователя как заполненную
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        
    Returns:
        Обновленный объект статуса анкеты
    """
    survey_status = get_or_create_survey_status(db, user_id)
    
    survey_status.is_completed = True
    survey_status.completed_at = datetime.now()
    db.commit()
    db.refresh(survey_status)
    
    logger.info(f"Анкета пользователя {user_id} отмечена как заполненная")
    return survey_status

def update_survey_reminder(db: Session, user_id: int) -> UserSurveyStatus:
    """
    Обновляет время последнего напоминания о заполнении анкеты
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        
    Returns:
        Обновленный объект статуса анкеты
    """
    survey_status = get_or_create_survey_status(db, user_id)
    
    survey_status.last_reminder_at = datetime.now()
    db.commit()
    db.refresh(survey_status)
    
    logger.info(f"Обновлено время напоминания об анкете для пользователя {user_id}")
    return survey_status

def get_users_needing_survey_reminder(db: Session, days_since_reminder: int = 1) -> list[ClientProfile]:
    """
    Получает список пользователей, которым нужно отправить напоминание о заполнении анкеты
    
    Args:
        db: Сессия базы данных
        days_since_reminder: Количество дней с момента последнего напоминания
        
    Returns:
        Список объектов пользователей
    """
    cutoff_time = datetime.now() - timedelta(days=days_since_reminder)
    
    # Пользователи с записью о статусе анкеты, которые её не заполнили и последнее напоминание было давно или его не было
    users_with_status = (
        db.query(ClientProfile)
        .join(UserSurveyStatus, ClientProfile.id == UserSurveyStatus.user_id)
        .filter(
            UserSurveyStatus.is_completed == False,
            or_(
                UserSurveyStatus.last_reminder_at == None,
                UserSurveyStatus.last_reminder_at < cutoff_time
            )
        )
        .all()
    )
    
    # Пользователи без записи о статусе анкеты (потенциально новые пользователи)
    users_without_status = (
        db.query(ClientProfile)
        .outerjoin(UserSurveyStatus, ClientProfile.id == UserSurveyStatus.user_id)
        .filter(UserSurveyStatus.id == None)
        .all()
    )
    
    return users_with_status + users_without_status 