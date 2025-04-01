from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import logging
import enum

# Get logger for this module
models_logger = logging.getLogger(__name__)

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

# Ensure all models are registered with Base metadata if needed elsewhere
# For example, if you have a Base = declarative_base() line earlier, ensure this model uses it.
# If Base is imported, ensure it's correctly configured.

# It might be necessary to regenerate the database schema or use migrations (like Alembic)
# depending on how the database is managed. 