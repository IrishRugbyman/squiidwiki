"""
SQLAlchemy event listeners that write to AuditLog on insert/update/delete.
Attach via attach_audit_listeners() called from app startup.
The current user_id is passed via a contextvars.ContextVar set in auth middleware.
"""

import datetime
import enum
import uuid
from contextvars import ContextVar

from sqlalchemy import event
from sqlalchemy.orm import Session

current_user_id: ContextVar[uuid.UUID | None] = ContextVar("current_user_id", default=None)

_AUDITED_TABLES = {
    "universe",
    "municipality",
    "alliance",
    "sets",
    "member",
    "incident",
    "source",
    "media",
}


def _json_safe(v):
    if isinstance(v, uuid.UUID):
        return str(v)
    if isinstance(v, enum.Enum):
        return v.value
    if isinstance(v, datetime.datetime | datetime.date):
        return v.isoformat()
    return v


def _get_diff(target, state: str) -> dict:
    if state == "deleted":
        return {"deleted": True}
    mapper = target.__class__.__mapper__  # type: ignore[attr-defined]
    return {
        col.key: _json_safe(getattr(target, col.key, None))
        for col in mapper.columns
        if col.key not in ("created_at", "updated_at")
    }


def _write_audit(session: Session, action: str, target) -> None:
    table = getattr(target.__class__, "__tablename__", None)
    if table not in _AUDITED_TABLES:
        return
    import datetime

    from app.core.enums import AuditAction
    from app.models.auth import AuditLog

    entry = AuditLog(
        user_id=current_user_id.get(),
        entity_type=table,
        entity_id=getattr(target, "id", uuid.uuid4()),
        action=AuditAction(action),
        diff_json=_get_diff(target, action.lower()),
        created_at=datetime.datetime.now(datetime.UTC),
    )
    session.add(entry)


_attached = False


def attach_audit_listeners() -> None:
    # Idempotent: listens_for registers a new closure on every call, so a
    # second call would write every audit row twice.
    global _attached
    if _attached:
        return
    _attached = True
    # Import all models so their mappers are registered
    from sqlalchemy.orm import mapperlib

    import app.models.alliance  # noqa: F401
    import app.models.gang_set  # noqa: F401
    import app.models.incident  # noqa: F401
    import app.models.media  # noqa: F401
    import app.models.member  # noqa: F401
    import app.models.municipality  # noqa: F401
    import app.models.source  # noqa: F401
    import app.models.universe  # noqa: F401

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


# ---------------------------------------------------------------------------
# Link changes (join rows)
#
# Join tables (member_set, incident_participant, *_source, set_gang,
# alliance_set, ...) are not snapshotted by the listeners above: their sync
# functions replace every row with a Core DELETE and re-insert on each save, so
# a row-level listener would log "added" for every unchanged link on every
# edit, and would miss the deletes entirely (Core statements bypass the ORM
# events). Instead each sync function reads the rows before it writes and calls
# record_link_change, which writes ONE audit_log row on the owning entity when,
# and only when, something actually changed:
#
#   entity_type / entity_id  the owner (e.g. "member", the member's id)
#   action                   UPDATE
#   diff_json = {
#     "_link":    "sets",                       which link list changed
#     "_key":     "set_id",                     the field that names the far side
#     "added":    [{...row...}],
#     "removed":  [{...row...}],
#     "changed":  [{"key": "<id>", "from": {...}, "to": {...}}],
#     "_related": ["<far-side id>", ...],       every far side touched
#   }
#
# "_related" is what lets the far side see the change too: the set's history
# shows "Member A was added to this set" by containment on that list (GIN
# index ix_audit_log_diff_json_related). The leading underscore keeps these
# keys from ever colliding with a column name in a snapshot row.
# ---------------------------------------------------------------------------

LINK_MARKER = "_link"


def _norm_row(row: dict) -> dict:
    # A JSON round trip, so nested values (a FuzzyDate dict holding a
    # DatePrecision enum) compare equal to what the database hands back.
    import json

    return json.loads(json.dumps(row, default=_json_safe))


def link_delta(key: str, before: list[dict], after: list[dict]) -> dict | None:
    """Compare two lists of join rows keyed by `key`. None when nothing changed."""
    b = {str(_json_safe(r[key])): _norm_row(r) for r in before}
    a = {str(_json_safe(r[key])): _norm_row(r) for r in after}
    added = [a[k] for k in a if k not in b]
    removed = [b[k] for k in b if k not in a]
    changed = []
    for k in a:
        if k in b and a[k] != b[k]:
            old = {f: v for f, v in b[k].items() if a[k].get(f) != v}
            new = {f: a[k].get(f) for f in old}
            new.update({f: v for f, v in a[k].items() if f not in b[k]})
            changed.append({"key": k, "from": old, "to": new})
    if not (added or removed or changed):
        return None
    related = [r[key] for r in added] + [r[key] for r in removed] + [c["key"] for c in changed]
    return {
        "_key": key,
        "added": added,
        "removed": removed,
        "changed": changed,
        "_related": sorted(set(related)),
    }


def record_link_change(
    session,
    *,
    entity_type: str,
    entity_id: uuid.UUID,
    link: str,
    key: str,
    before: list[dict],
    after: list[dict],
) -> None:
    """Add one audit_log row describing how a link list changed (see above)."""
    delta = link_delta(key, before, after)
    if delta is None:
        return
    from app.core.enums import AuditAction
    from app.models.auth import AuditLog

    session.add(
        AuditLog(
            user_id=current_user_id.get(),
            entity_type=entity_type,
            entity_id=entity_id,
            action=AuditAction.UPDATE,
            diff_json={LINK_MARKER: link, **delta},
            created_at=datetime.datetime.now(datetime.UTC),
        )
    )


async def load_link_rows(session, model, where, fields: list[str]) -> list[dict]:
    """The current join rows matching `where`, as plain dicts of `fields`."""
    from sqlalchemy import select

    cols = [getattr(model, f) for f in fields]
    rows = (await session.execute(select(*cols).where(where))).all()
    return [dict(zip(fields, r, strict=True)) for r in rows]
