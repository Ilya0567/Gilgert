from sqlalchemy import create_engine, and_, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
import os
from datetime import datetime, timedelta

# Get logger for this module
db_logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite:///./test.db"  # Using SQLite for simplicity
absolute_db_path = os.path.abspath("./test.db")

# Constants for session management
SESSION_TIMEOUT = timedelta(minutes=5)  # Time after which a new session starts

db_logger.info(f"Setting up database connection to: {DATABASE_URL}")
db_logger.info(f"Database file will be created at: {absolute_db_path}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Initialize the database by creating all tables."""
    # Import all models here to ensure they're registered with Base
    db_logger.info("Importing models before creating tables...")
    from . import models
    
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
    """Get or create user profile."""
    from .models import ClientProfile
    
    db_logger.info(f"Looking for user with telegram_id: {telegram_id}")
    user = db.query(ClientProfile).filter(ClientProfile.telegram_id == str(telegram_id)).first()
    
    if user:
        db_logger.info(f"Found existing user: {telegram_id}, username: {user.username}")
        if username and user.username != username:
            db_logger.info(f"Updating username from '{user.username}' to '{username}'")
            user.username = username
        if first_name and user.first_name != first_name:
            db_logger.info(f"Updating first_name from '{user.first_name}' to '{first_name}'")
            user.first_name = first_name
        if last_name and user.last_name != last_name:
            db_logger.info(f"Updating last_name from '{user.last_name}' to '{last_name}'")
            user.last_name = last_name
            
        user.interaction_count += 1
        db_logger.info(f"Incremented interaction count to: {user.interaction_count}")
        db.commit()
        return user
    
    db_logger.info(f"User {telegram_id} not found. Creating new user profile.")
    new_user = ClientProfile(
        telegram_id=str(telegram_id),
        username=username,
        first_name=first_name,
        last_name=last_name
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_or_create_session(db, user_id):
    """Get current active session or create new one if needed."""
    from .models import UserSession
    
    # Get the latest session for the user
    latest_session = (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id)
        .order_by(UserSession.start_time.desc())
        .first()
    )
    
    current_time = datetime.now()
    
    # If no session exists or the last interaction was more than SESSION_TIMEOUT ago
    if not latest_session or (
        latest_session.last_interaction 
        and current_time - latest_session.last_interaction > SESSION_TIMEOUT
    ):
        # If there was a previous session, close it
        if latest_session and not latest_session.is_completed:
            end_user_session(db, latest_session.id)
        
        # Create new session
        new_session = UserSession(
            user_id=user_id,
            source="continuation" if latest_session else "start"
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session
    
    # Update last interaction time
    latest_session.last_interaction = current_time
    db.commit()
    return latest_session

def end_user_session(db, session_id):
    """End a user session and calculate its duration."""
    from .models import UserSession
    
    db_logger.info(f"Ending session {session_id}")
    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if session and not session.is_completed:
        session.end_time = session.last_interaction or datetime.now()
        session.is_completed = True
        if session.start_time:
            duration = (session.end_time - session.start_time).total_seconds()
            session.session_duration = int(duration)
        db.commit()
        db_logger.info(f"Session {session_id} ended. Duration: {session.session_duration}s")
    return session

def log_user_interaction(db, user_id, action_type, action_data, response_time=None, success=True):
    """Log a user interaction and update session."""
    from .models import UserInteraction
    
    # First, get or create a session
    session = get_or_create_session(db, user_id)
    
    db_logger.info(f"Logging interaction for user {user_id}: {action_type}")
    interaction = UserInteraction(
        user_id=user_id,
        action_type=action_type,
        action_data=action_data,
        response_time=response_time,
        success=success,
        session_id=session.id
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction

def get_user_statistics(db, user_id):
    """Get statistics for a specific user."""
    from .models import UserSession, UserInteraction
    
    # Get completed sessions (more than SESSION_TIMEOUT since last interaction)
    current_time = datetime.now()
    completed_sessions = db.query(UserSession).filter(
        UserSession.user_id == user_id,
        or_(
            UserSession.is_completed == True,
            current_time - UserSession.last_interaction > SESSION_TIMEOUT
        )
    ).count()
    
    total_sessions = db.query(UserSession).filter(
        UserSession.user_id == user_id
    ).count()
    
    total_interactions = db.query(UserInteraction).filter(
        UserInteraction.user_id == user_id
    ).count()
    
    successful_interactions = db.query(UserInteraction).filter(
        UserInteraction.user_id == user_id,
        UserInteraction.success == True
    ).count()
    
    # Calculate average session duration for completed sessions
    completed_sessions_data = db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.session_duration.isnot(None)
    ).all()
    
    avg_duration = 0
    if completed_sessions_data:
        total_duration = sum(session.session_duration for session in completed_sessions_data)
        avg_duration = total_duration / len(completed_sessions_data)
    
    return {
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "total_interactions": total_interactions,
        "successful_interactions": successful_interactions,
        "average_session_duration": int(avg_duration)
    } 