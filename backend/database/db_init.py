"""Database initialization: ensures an admin user exists.

Tables are managed by Alembic migrations — run `alembic upgrade head` before starting.
"""
import logging

from sqlalchemy import select

import backend.database.models  # noqa: F401
from backend.database.base_class import get_db_context
from backend.database.models import User
from backend.auth.auth_utils import get_password_hash
from backend.settings import settings

logger = logging.getLogger(__name__)


async def ensure_admin_exists() -> bool:
    try:
        async with get_db_context() as db:
            result = await db.execute(
                select(User).where(User.is_admin == True)  # noqa: E712
            )
            if result.scalars().first():
                return False

            username = settings.auth.default_admin_username
            password = settings.auth.default_admin_password

            existing_result = await db.execute(
                select(User).where(User.username == username)
            )
            existing = existing_result.scalars().first()
            if existing:
                if not existing.is_admin:
                    existing.is_admin = True
                    logger.info(f"Promoted '{username}' to admin")
            else:
                db.add(User(
                    username=username,
                    password_hash=get_password_hash(password),
                    is_admin=True,
                ))
                logger.info(f"Created admin user '{username}'")
            return True
    except Exception as e:
        logger.error(f"Error ensuring admin: {e}")
        return False


async def init_db() -> bool:
    """Seed admin user. Tables must already exist (run alembic upgrade head first)."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger.info(f"Seeding database: {settings.database.database}")
    try:
        await ensure_admin_exists()
        logger.info("Database seed completed")
        return True
    except Exception as e:
        logger.error(f"Unexpected error during seed: {e}")
        return False
