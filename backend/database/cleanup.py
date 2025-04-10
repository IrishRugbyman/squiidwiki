from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from backend.config.config import settings

# Create engine and session using config
engine = create_engine(settings.get_sqlalchemy_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def cleanup():
    """
    Cleanup temporary database objects.
    """
    db = SessionLocal()
    try:
        # Drop temporary tables if they exist
        db.execute(text("DROP TABLE IF EXISTS sets_new"))
        db.commit()
        print(f"Cleanup completed successfully on database: {settings.get_db_path()}")
    except Exception as e:
        db.rollback()
        print(f"Error during cleanup: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    cleanup() 