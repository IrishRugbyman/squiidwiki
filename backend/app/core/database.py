import uuid
from collections.abc import AsyncGenerator
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

from app.core.config import settings

DbMode = Literal["prod", "test"]

_active_db: DbMode = "prod"


def _make_engine(url: str):
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return create_async_engine(url, echo=settings.environment == "development")


_engines = {
    "prod": _make_engine(settings.database_url_prod),
    "test": _make_engine(settings.database_url_test),
}

_session_factories = {
    mode: async_sessionmaker(eng, expire_on_commit=False)
    for mode, eng in _engines.items()
}


def get_db_mode() -> DbMode:
    return _active_db


def set_db_mode(mode: DbMode) -> None:
    global _active_db
    _active_db = mode


async def init_db() -> None:
    async with _engines["prod"].begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with _session_factories[_active_db]() as session:
        yield session


async def get_prod_session() -> AsyncGenerator[AsyncSession, None]:
    """Always uses the prod engine — for auth so switching DBs doesn't invalidate tokens."""
    async with _session_factories["prod"]() as session:
        yield session


async def resolve_prod_universe(
    active_session: AsyncSession,
    prod_session: AsyncSession,
    universe_id: uuid.UUID,
) -> uuid.UUID | None:
    """Map an active-DB universe id to the matching prod-DB universe id by slug.

    Used by features that always live in prod regardless of the active mode
    (e.g. municipalities — geo reference data shared across modes).

    Returns the prod universe id, or None if the active universe doesn't exist
    or has no slug match in prod.
    """
    if _active_db == "prod":
        return universe_id

    from app.models.universe import Universe

    active_univ = (
        await active_session.execute(select(Universe).where(Universe.id == universe_id))
    ).scalar_one_or_none()
    if active_univ is None:
        return None

    prod_univ = (
        await prod_session.execute(select(Universe).where(Universe.slug == active_univ.slug))
    ).scalar_one_or_none()
    return prod_univ.id if prod_univ else None
