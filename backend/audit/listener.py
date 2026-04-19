"""SQLAlchemy event listener that emits AuditLog rows on flush.

Tracks INSERT, UPDATE (with a diff), and soft-DELETE (deleted_at set)
for any model that carries AuditMixin.  The listener is registered once
in the app lifespan via ``register_audit_listener()``.

The ``_audit_user_id`` session info key can be set by request middleware
to attach the acting user to every log row in that session.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Session

from backend.database.base_class import AuditMixin
from backend.database.models import AuditAction, AuditLog


def _json_default(obj: Any) -> Any:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _make_diff(attrs: dict[str, Any]) -> str | None:
    if not attrs:
        return None
    return json.dumps(attrs, default=_json_default)


def _is_audit_target(instance: Any) -> bool:
    return isinstance(instance, AuditMixin)


def _after_flush(session: Session, flush_context: Any) -> None:
    user_id = session.info.get("audit_user_id")
    new_logs: list[AuditLog] = []

    for obj in session.new:
        if not _is_audit_target(obj):
            continue
        entity_type = type(obj).__tablename__
        new_logs.append(AuditLog(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=obj.id,
            action=AuditAction.CREATE,
            diff_json=None,
        ))

    for obj in session.dirty:
        if not _is_audit_target(obj):
            continue
        history = {}
        from sqlalchemy import inspect as sa_inspect
        insp = sa_inspect(obj)
        for attr in insp.attrs:
            hist = attr.history
            if hist.has_changes() and (hist.deleted or hist.added):
                history[attr.key] = {
                    "old": hist.deleted[0] if hist.deleted else None,
                    "new": hist.added[0] if hist.added else None,
                }
        if not history:
            continue

        # Treat setting deleted_at as a DELETE
        if "deleted_at" in history and history["deleted_at"]["new"] is not None:
            action = AuditAction.DELETE
        else:
            action = AuditAction.UPDATE

        new_logs.append(AuditLog(
            user_id=user_id,
            entity_type=type(obj).__tablename__,
            entity_id=obj.id,
            action=action,
            diff_json=_make_diff(history),
        ))

    for log in new_logs:
        session.add(log)


def register_audit_listener() -> None:
    """Call once at app startup to wire the flush listener."""
    event.listen(Session, "after_flush", _after_flush)


def unregister_audit_listener() -> None:
    """Call at app shutdown (useful in tests to avoid double-registration)."""
    if event.contains(Session, "after_flush", _after_flush):
        event.remove(Session, "after_flush", _after_flush)
