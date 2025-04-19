"""
Comprehensive database initialization script.

This script:
1. Creates all tables defined in SQLAlchemy models
2. Checks for and creates missing tables
3. Ensures an admin user exists with proper credentials
"""
import logging
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

# Import all models to ensure they are registered with SQLAlchemy metadata
from backend.database.imports import *
from backend.auth.auth_utils import get_password_hash
from backend.config.config import settings

logger = logging.getLogger(__name__)

def create_tables():
    """
    Create all tables defined in SQLAlchemy models.
    This is safe to run multiple times as it will not recreate existing tables.
    """
    try:
        # Create all tables that don't exist
        Base.metadata.create_all(bind=engine)
        logger.info("Successfully created all missing database tables")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {str(e)}")
        return False

def check_tables():
    """
    Check which tables exist and which are missing.
    Returns a tuple of (existing_tables, missing_tables)
    """
    try:
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        
        # Get all tables defined in models
        model_tables = set(Base.metadata.tables.keys())
        
        # Find missing tables
        missing_tables = model_tables - existing_tables
        
        if missing_tables:
            logger.warning(f"Missing tables detected: {', '.join(missing_tables)}")
        else:
            logger.info("All required database tables exist")
            
        return existing_tables, missing_tables
    except SQLAlchemyError as e:
        logger.error(f"Error checking database tables: {str(e)}")
        return set(), set()

def ensure_admin_exists():
    """
    Check if any admin users exist, and if not, create one using
    the default credentials from the config.
    """
    try:
        with get_db_context() as db:
            # Check if any admin users exist
            admin_exists = db.query(Users).filter(Users.is_admin == True).first() is not None
            
            if not admin_exists:
                # Get default admin credentials
                default_admin = settings.get_default_admin()
                username = default_admin["username"]
                password = default_admin["password"]
                is_admin = default_admin["is_admin"]
                
                # Check if user with that username already exists
                existing_user = db.query(Users).filter(Users.username == username).first()
                
                if existing_user:
                    # If the user exists but is not admin, make them admin
                    if not existing_user.is_admin:
                        existing_user.is_admin = True
                        db.commit()
                        logger.info(f"Updated existing user '{username}' to have admin privileges")
                else:
                    # Create new admin user
                    hashed_password = get_password_hash(password)
                    new_admin = Users(
                        username=username,
                        password_hash=hashed_password,
                        is_admin=is_admin
                    )
                    db.add(new_admin)
                    db.commit()
                    logger.info(f"Created default admin user '{username}'")
                
                return True
            else:
                logger.debug("Admin user already exists, no need to create default")
                return False
                
    except SQLAlchemyError as e:
        logger.error(f"Database error when checking/creating admin user: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error when checking/creating admin user: {str(e)}")
        return False

def init_db(check_only=False):
    """
    Initialize the database by creating all missing tables
    and ensuring required data exists.
    
    Args:
        check_only: If True, only check tables but don't create them
    
    Returns:
        bool: Whether initialization was successful
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    logger.info(f"Initializing database: {settings.get_pg_config()['database']}")
    
    try:
        # Check existing tables
        existing_tables, missing_tables = check_tables()
        
        if check_only:
            return len(missing_tables) == 0
        
        if missing_tables:
            # Create missing tables
            if not create_tables():
                return False
        
        # Ensure admin user exists
        admin_created = ensure_admin_exists()
        if admin_created:
            logger.info("Admin user was created or updated")
        else:
            logger.info("Admin user check completed, no action needed")
        
        logger.info("Database initialization completed successfully")
        return True
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {str(e)}")
        return False

def force_create_admin():
    """
    Force creation/update of the admin user from config settings.
    Useful for password resets or troubleshooting.
    """
    try:
        with get_db_context() as db:
            # Get default admin credentials
            default_admin = settings.get_default_admin()
            username = default_admin["username"]
            password = default_admin["password"]
            is_admin = default_admin["is_admin"]
            
            # Check if user with that username already exists
            existing_user = db.query(Users).filter(Users.username == username).first()
            
            if existing_user:
                # Update existing user
                existing_user.password_hash = get_password_hash(password)
                existing_user.is_admin = True
                db.commit()
                logger.info(f"Updated existing user '{username}' with new password and admin privileges")
            else:
                # Create new admin user
                hashed_password = get_password_hash(password)
                new_admin = Users(
                    username=username,
                    password_hash=hashed_password,
                    is_admin=is_admin
                )
                db.add(new_admin)
                db.commit()
                logger.info(f"Created new admin user '{username}'")
            
            logger.info(f"Admin username: {username}")
            logger.info(f"Admin password: {password}")
            return True
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        return False

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Run initialization
    init_db() 