from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base
import logging

# Get logger for this module
models_logger = logging.getLogger(__name__)

models_logger.info("Registering ClientProfile model with SQLAlchemy")

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
    # Add other fields as necessary 
    
    def __repr__(self):
        """String representation of the ClientProfile model"""
        return f"ClientProfile(id={self.id}, telegram_id={self.telegram_id}, username={self.username}, interaction_count={self.interaction_count})" 