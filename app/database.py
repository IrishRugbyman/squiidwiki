"""Database setup and session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Import Base from models.base
from app.models.base import Base

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=True  # Set to False in production
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
