"""
SQLAlchemy event listeners that write to AuditLog on insert/update/delete.
Attach via attach_audit_listeners() called from app startup.
The current user_id is passed via a contextvars.ContextVar set in auth middleware.
"""
import uuid
from contextvars import ContextVar
from typing import Optional

from sqlalchemy import event
from sqlalchemy.orm import Session

current_user_id: ContextVar[Optional[uuid.UUID]] = ContextVar("current_user_id", default=None)

_AUDITED_TABLES = {
    "universe", "municipality", "alliance", "sets",
    "member", "incident", "source",
}


def _get_diff(target, state: str) -> dict:
    if state == "deleted":
        return {"deleted": True}
    mapper = target.__class__.__mapper__  # type: ignore[attr-defined]
    return {
        col.key: getattr(target, col.key, None)
        for col in mapper.columns
        if col.key not in ("created_at", "updated_at")
    }


def _write_audit(session: Session, action: str, target) -> None:
    table = getattr(target.__class__, "__tablename__", None)
    if table not in _AUDITED_TABLES:
        return
    from app.models.auth import AuditLog
    from app.core.enums import AuditAction
    import datetime

    entry = AuditLog(
        user_id=current_user_id.get(),
        entity_type=table,
        entity_id=getattr(target, "id", uuid.uuid4()),
        action=AuditAction(action),
        diff_json=_get_diff(target, action.lower()),
        created_at=datetime.datetime.utcnow(),
    )
    session.add(entry)


def attach_audit_listeners() -> None:
    # Import all models so their mappers are registered
    import app.models.universe  # noqa: F401
    import app.models.municipality  # noqa: F401
    import app.models.alliance  # noqa: F401
    import app.models.gang_set  # noqa: F401
    import app.models.member  # noqa: F401
    import app.models.incident  # noqa: F401
    import app.models.source  # noqa: F401

    from sqlalchemy.orm import mapperlib

    for reg in mapperlib._mapper_registries:  # type: ignore[attr-defined]
        for mapped_class in reg.mappers:
            cls = mapped_class.class_
            table = getattr(cls, "__tablename__", None)
            if table not in _AUDITED_TABLES:
                continue

            @event.listens_for(cls, "after_insert")
            def after_insert(mapper, connection, target):
                session = Session.object_session(target)
                if session:
                    _write_audit(session, "CREATE", target)

            @event.listens_for(cls, "after_update")
            def after_update(mapper, connection, target):
                session = Session.object_session(target)
                if session:
                    _write_audit(session, "UPDATE", target)

            @event.listens_for(cls, "after_delete")
            def after_delete(mapper, connection, target):
                session = Session.object_session(target)
                if session:
                    _write_audit(session, "DELETE", target)
