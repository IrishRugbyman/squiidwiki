from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator

from sqlalchemy import Boolean, Column, DateTime, create_engine, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from backend.settings import settings


Base = declarative_base()


class TimestampMixin:
    created_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
    )


class SoftDeleteMixin:
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    is_archived = Column(Boolean, default=False, server_default="false", nullable=False)

    @hybrid_property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @is_deleted.expression  # type: ignore[no-redef]
    def is_deleted(cls):
        return cls.deleted_at.isnot(None)

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        self.deleted_at = None


class AuditMixin(TimestampMixin, SoftDeleteMixin):
    pass


# ---------------------------------------------------------------------------
# Async engine + session — used by the application at runtime.
# Lazy so that importing Base/mixins for tests doesn't require a live DB.
# ---------------------------------------------------------------------------
_async_engine = None
_AsyncSessionLocal = None


def _get_async_engine():
    global _async_engine
    if _async_engine is None:
        _async_engine = create_async_engine(
            settings.get_async_database_url(),
            pool_pre_ping=True,
            pool_size=settings.database.max_connections,
            max_overflow=settings.database.max_connections * 2,
            pool_timeout=settings.database.connection_timeout,
            pool_recycle=settings.database.pool_recycle,
        )
    return _async_engine


def _get_async_session_factory():
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            _get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _get_async_session_factory()() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    async with _get_async_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Sync engine — kept for Alembic migrations and as a legacy proxy.
# ---------------------------------------------------------------------------
_sync_engine = None
_SyncSessionLocal = None


def _get_sync_engine():
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(
            settings.get_database_url(),
            pool_pre_ping=True,
        )
    return _sync_engine


def _get_sync_session_factory():
    global _SyncSessionLocal
    if _SyncSessionLocal is None:
        _SyncSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=_get_sync_engine()
        )
    return _SyncSessionLocal


class _EngineProxy:
    def __getattr__(self, name):
        return getattr(_get_sync_engine(), name)

    def __repr__(self):
        return repr(_get_sync_engine())


class _SessionLocalProxy:
    def __call__(self, *args, **kwargs):
        return _get_sync_session_factory()(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(_get_sync_session_factory(), name)


engine = _EngineProxy()
SessionLocal = _SessionLocalProxy()


def get_sync_db() -> Generator[Session, None, None]:
    db = _get_sync_session_factory()()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_sync_db_context() -> Generator[Session, None, None]:
    db = _get_sync_session_factory()()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
