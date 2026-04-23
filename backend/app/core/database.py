from collections.abc import AsyncGenerator
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

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
