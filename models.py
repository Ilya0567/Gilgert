from sqlalchemy import Column, Integer, String, Boolean
from .database import Base

class ClientProfile(Base):
    __tablename__ = "client_profiles"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True)
    username = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    # Add other fields as necessary 