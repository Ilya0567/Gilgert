from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./test.db"  # Using SQLite for simplicity

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    """Function to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
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
    from models import ClientProfile
    
    user = db.query(ClientProfile).filter(ClientProfile.telegram_id == str(telegram_id)).first()
    
    if user:
        # Update user information if it has changed
        if username and user.username != username:
            user.username = username
        if first_name and user.first_name != first_name:
            user.first_name = first_name
        if last_name and user.last_name != last_name:
            user.last_name = last_name
            
        # Increment interaction count
        user.interaction_count += 1
        db.commit()
        return user
    
    # Create new user if not found
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