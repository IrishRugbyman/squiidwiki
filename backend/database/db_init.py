"""Database initialization: creates tables and ensures an admin user exists."""
import logging

from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

import backend.database.models  # noqa: F401 — register all models with metadata
from backend.database.base_class import Base, _get_engine, get_db_context
from backend.database.models import User
from backend.auth.auth_utils import get_password_hash
from backend.settings import settings

logger = logging.getLogger(__name__)


def create_tables():
    try:
        Base.metadata.create_all(bind=_get_engine())
        logger.info("Created all missing database tables")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error creating tables: {e}")
        return False


def check_tables():
    try:
        inspector = inspect(_get_engine())
        existing = set(inspector.get_table_names())
        expected = set(Base.metadata.tables.keys())
        missing = expected - existing
        if missing:
            logger.warning(f"Missing tables: {', '.join(missing)}")
        return existing, missing
    except SQLAlchemyError as e:
        logger.error(f"Error checking tables: {e}")
        return set(), set()


def ensure_admin_exists():
    try:
        with get_db_context() as db:
            admin_exists = db.query(User).filter(User.is_admin == True).first() is not None
            if not admin_exists:
                username = settings.auth.default_admin_username
                password = settings.auth.default_admin_password
                existing = db.query(User).filter(User.username == username).first()
                if existing:
                    if not existing.is_admin:
                        existing.is_admin = True
                        logger.info(f"Promoted '{username}' to admin")
                else:
                    new_admin = User(
                        username=username,
                        password_hash=get_password_hash(password),
                        is_admin=True,
                    )
                    db.add(new_admin)
                    logger.info(f"Created admin user '{username}'")
                return True
            return False
    except Exception as e:
        logger.error(f"Error ensuring admin: {e}")
        return False


def init_db(check_only=False):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger.info(f"Initializing database: {settings.database.database}")
    try:
        existing, missing = check_tables()
        if check_only:
            return len(missing) == 0
        if missing:
            if not create_tables():
                return False
        ensure_admin_exists()
        logger.info("Database initialization completed")
        return True
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    init_db()
