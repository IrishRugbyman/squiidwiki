"""Standalone seed script.

Creates the Default universe, admin user, and grants admin universe access.
Run after `alembic upgrade head`:

    python -m backend.seed
"""
import asyncio
import logging

from sqlalchemy import select

from backend.auth.auth_utils import get_password_hash
from backend.database.base_class import get_db_context
from backend.database.models import GlobalRole, Universe, UniverseRole, User, UserUniverseAccess
from backend.settings import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def _seed() -> None:
    async with get_db_context() as db:
        # Universe
        result = await db.execute(select(Universe).where(Universe.slug == "default"))
        universe = result.scalars().first()
        if not universe:
            universe = Universe(name="Default", slug="default")
            db.add(universe)
            await db.flush()
            logger.info("Created 'Default' universe (slug=default)")

        # Admin user
        username = settings.auth.default_admin_username
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalars().first()
        if not user:
            user = User(
                username=username,
                hashed_password=get_password_hash(settings.auth.default_admin_password),
                global_role=GlobalRole.ADMIN,
            )
            db.add(user)
            await db.flush()
            logger.info(f"Created admin user '{username}'")

        # Universe access
        result = await db.execute(
            select(UserUniverseAccess).where(
                UserUniverseAccess.user_id == user.id,
                UserUniverseAccess.universe_id == universe.id,
            )
        )
        if not result.scalars().first():
            db.add(UserUniverseAccess(
                user_id=user.id,
                universe_id=universe.id,
                role=UniverseRole.ADMIN,
            ))
            logger.info(f"Granted ADMIN universe access to '{username}' on 'default'")


if __name__ == "__main__":
    asyncio.run(_seed())
