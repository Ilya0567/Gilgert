from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum
import datetime
import logging

# Get logger for this module
models_logger = logging.getLogger(__name__)

# Импортируем Base из database.py
from database.database import Base

models_logger.info("Registering models with SQLAlchemy")

class ActionType(enum.Enum):
    BUTTON_CLICK = "button_click"
    COMMAND = "command"
    MESSAGE = "message"
    PRODUCT_SEARCH = "product_search"
    GPT_QUESTION = "gpt_question"
    RECIPE_VIEW = "recipe_view"
    CLICK_RATE_BUTTON = "click_rate_button"
    SUBMIT_RATING = "submit_rating"
    HEALTH_CHECK = "health_check"  # New action type for health checks

class ClientProfile(Base):
    __tablename__ = "client_profiles"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True)
    username = Column(String, index=True)
    first_name = Column(String)
    last_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_interaction = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    interaction_count = Column(Integer, default=1)

    # Relationships
    sessions = relationship("UserSession", back_populates="user")
    interactions = relationship("UserInteraction", back_populates="user")
    conversations = relationship("UserConversation", order_by=UserConversation.timestamp, back_populates="user")
    
    def __repr__(self):
        """String representation of the ClientProfile model"""
        return f"ClientProfile(id={self.id}, telegram_id={self.telegram_id}, username={self.username}, interaction_count={self.interaction_count})"


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("client_profiles.id"))
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    last_interaction = Column(DateTime(timezone=True), server_default=func.now())
    session_duration = Column(Integer, nullable=True)  # in seconds
    source = Column(String)  # how user started session (/start, deep link, etc.)
    last_command = Column(String, nullable=True)
    is_completed = Column(Boolean, default=False)

    # Relationships
    user = relationship("ClientProfile", back_populates="sessions")
    interactions = relationship("UserInteraction", back_populates="session")
    
    def __repr__(self):
        return f"UserSession(id={self.id}, user_id={self.user_id}, start_time={self.start_time}, is_completed={self.is_completed})"

class UserInteraction(Base):
    __tablename__ = "user_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("client_profiles.id"))
    session_id = Column(Integer, ForeignKey("user_sessions.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    action_type = Column(String)  # Using String instead of Enum for flexibility
    action_data = Column(String)  # what exactly user did (button clicked, command sent, etc.)
    response_time = Column(Integer, nullable=True)  # in milliseconds
    success = Column(Boolean, default=True)

    # Relationships
    user = relationship("ClientProfile", back_populates="interactions")
    session = relationship("UserSession", back_populates="interactions")
    
    def __repr__(self):
        return f"UserInteraction(id={self.id}, user_id={self.user_id}, action_type={self.action_type}, success={self.success})"

# New model for recipe ratings
class RecipeRating(Base):
    __tablename__ = "recipe_ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("client_profiles.id"), nullable=False)
    recipe_type = Column(String, nullable=False) # e.g., 'breakfast', 'lunch', 'poldnik', 'drink'
    recipe_name = Column(String, nullable=False) # The name of the recipe being rated
    rating = Column(Integer, nullable=False) # Rating from 1 to 5
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("ClientProfile")

    def __repr__(self):
        return f"<RecipeRating(user_id={self.user_id}, recipe='{self.recipe_name}', rating={self.rating})>"

models_logger.info("RecipeRating model defined")

class DailyHealthCheck(Base):
    __tablename__ = "daily_health_checks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("client_profiles.id"), nullable=False)
    mood = Column(String, nullable=False)  # 'sad', 'neutral', 'happy'
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to user
    user = relationship("ClientProfile")

    def __repr__(self):
        return f"<DailyHealthCheck(user_id={self.user_id}, mood='{self.mood}', timestamp={self.timestamp})>"

models_logger.info("DailyHealthCheck model defined")

class BroadcastMessage(Base):
    __tablename__ = "broadcast_messages"

    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey("client_profiles.id"))
    message = Column(String)
    scheduled_time = Column(DateTime(timezone=True))
    sent = Column(Boolean, default=False)  # Единое поле для статуса отправки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)

    # Отношения
    admin = relationship("ClientProfile")

    def __repr__(self):
        return f"<BroadcastMessage(id={self.id}, scheduled_time={self.scheduled_time}, sent={self.sent})>"

models_logger.info("BroadcastMessage model defined")

class UserConversation(Base):
    """Модель для хранения истории разговоров пользователя с ботом"""
    __tablename__ = 'user_conversations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('client_profiles.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    # Храним сообщения в формате JSON: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    messages = Column(JSON, nullable=False, default=list)
    
    # Отношения
    user = relationship("ClientProfile", back_populates="conversations")
    
    def __repr__(self):
        return f"<UserConversation(user_id={self.user_id}, timestamp={self.timestamp})>"

# Ensure all models are registered with Base metadata if needed elsewhere
# For example, if you have a Base = declarative_base() line earlier, ensure this model uses it.
# If Base is imported, ensure it's correctly configured.

# It might be necessary to regenerate the database schema or use migrations (like Alembic)
# depending on how the database is managed. 