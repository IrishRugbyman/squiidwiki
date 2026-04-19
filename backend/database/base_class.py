from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Generator

from sqlalchemy import Boolean, Column, DateTime, create_engine, func
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
# Engine & session factory — lazy so that importing Base / mixins for tests
# never requires a live database connection.
# ---------------------------------------------------------------------------
_engine = None
_SessionLocal = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.get_database_url(),
            pool_pre_ping=True,
            pool_size=settings.database.max_connections,
            max_overflow=settings.database.max_connections * 2,
            pool_timeout=settings.database.connection_timeout,
            pool_recycle=settings.database.pool_recycle,
        )
    return _engine


def _get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_get_engine())
    return _SessionLocal


class _EngineProxy:
    def __getattr__(self, name):
        return getattr(_get_engine(), name)

    def __repr__(self):
        return repr(_get_engine())


class _SessionLocalProxy:
    def __call__(self, *args, **kwargs):
        return _get_session_factory()(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(_get_session_factory(), name)


engine = _EngineProxy()
SessionLocal = _SessionLocalProxy()


def get_db() -> Generator:
    db = _get_session_factory()()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    db = _get_session_factory()()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
