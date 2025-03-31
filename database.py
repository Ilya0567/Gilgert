from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
import os

# Get logger for this module
db_logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite:///./test.db"  # Using SQLite for simplicity
absolute_db_path = os.path.abspath("./test.db")

db_logger.info(f"Setting up database connection to: {DATABASE_URL}")
db_logger.info(f"Database file will be created at: {absolute_db_path}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Initialize the database by creating all tables."""
    # Import all models here to ensure they're registered with Base
    db_logger.info("Importing models before creating tables...")
    # This import is needed to register the models with Base
    import models
    
    db_logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    db_logger.info("Database tables created successfully")

def get_db():
    """Function to get a database session."""
    db_logger.debug("Creating new database session")
    db = SessionLocal()
    try:
        yield db
    finally:
        db_logger.debug("Closing database session")
        db.close()

def get_or_create_user(db, telegram_id, username=None, first_name=None, last_name=None):
    """
    Get an existing user or create a new one if doesn't exist.
    
    Args:
        db: Database session
        telegram_id: User's Telegram ID
        username: User's Telegram username
        first_name: User's first name
        last_name: User's last name
        
    Returns:
        User profile object
    """
    # Import here to avoid circular imports
    from models import ClientProfile
    
    db_logger.info(f"Looking for user with telegram_id: {telegram_id}")
    user = db.query(ClientProfile).filter(ClientProfile.telegram_id == str(telegram_id)).first()
    
    if user:
        db_logger.info(f"Found existing user: {telegram_id}, username: {user.username}")
        # Update user information if it has changed
        if username and user.username != username:
            db_logger.info(f"Updating username from '{user.username}' to '{username}'")
            user.username = username
        if first_name and user.first_name != first_name:
            db_logger.info(f"Updating first_name from '{user.first_name}' to '{first_name}'")
            user.first_name = first_name
        if last_name and user.last_name != last_name:
            db_logger.info(f"Updating last_name from '{user.last_name}' to '{last_name}'")
            user.last_name = last_name
            
        # Increment interaction count
        user.interaction_count += 1
        db_logger.info(f"Incremented interaction count to: {user.interaction_count}")
        db.commit()
        db_logger.debug("Database changes committed")
        return user
    
    # Create new user if not found
    db_logger.info(f"User {telegram_id} not found. Creating new user profile.")
    new_user = ClientProfile(
        telegram_id=str(telegram_id),
        username=username,
        first_name=first_name,
        last_name=last_name
    )
    
    db.add(new_user)
    db_logger.debug(f"Added new user to session: {telegram_id}")
    db.commit()
    db_logger.info(f"New user committed to database: {telegram_id}")
    db.refresh(new_user)
    return new_user 