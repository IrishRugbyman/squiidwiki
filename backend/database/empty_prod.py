import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.config.config import settings

# Create engine and session using config
engine = create_engine(settings.get_sqlalchemy_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def empty_prod():
    """
    Empty the production database while preserving the sets and config tables.
    """
    db = SessionLocal()
    try:
        # Disable foreign keys temporarily to allow truncating tables with dependencies
        db.execute(text("SET session_replication_role = 'replica'"))
        
        # Get the special set IDs from config
        result = db.execute(text("SELECT value FROM config WHERE key IN ('unknown_set_id', 'civilian_set_id')"))
        special_set_ids = [row[0] for row in result.fetchall()]
        
        # Delete all members except those in special sets
        if special_set_ids:
            special_set_ids_str = ','.join(str(id) for id in special_set_ids)
            db.execute(text(f"DELETE FROM members WHERE set_id NOT IN ({special_set_ids_str})"))
        else:
            db.execute(text("DELETE FROM members"))
        
        # Delete all other tables
        tables_to_empty = [
            'alliance_sets_map',
            'set_allies_map',
            'set_enemies_map',
            'alliances',
            'shootings',
            'murders',
            'assists'
        ]
        
        for table in tables_to_empty:
            db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
        
        # Re-enable foreign key constraints
        db.execute(text("SET session_replication_role = 'origin'"))
        
        # Commit the transaction
        db.commit()
        print(f"Production database emptied successfully while preserving sets and config tables: {settings.get_pg_config()['database']}")
        
    except Exception as e:
        db.rollback()
        print(f"Error emptying production database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    empty_prod() 