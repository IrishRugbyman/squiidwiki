from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from typing import Generator
from contextlib import contextmanager

from backend.config.config import settings

# Create the SQLAlchemy base class
Base = declarative_base()

# Create engine using PostgreSQL configuration
pg_config = settings.get_pg_config()
engine = create_engine(
    settings.get_sqlalchemy_url(),
    pool_pre_ping=True,
    pool_size=pg_config["max_connections"],
    max_overflow=pg_config["max_connections"] * 2,
    pool_timeout=pg_config["connection_timeout"],
    pool_recycle=pg_config.get("pool_recycle", 3600)
)
print(f"SQLAlchemy using database: {settings.get_pg_config()['database']}")
    
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator:
    """
    Dependency function that provides a SQLAlchemy session.
    This should be used with FastAPI's dependency injection system.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database sessions.
    For use in utility functions or scripts outside the API context.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close() 