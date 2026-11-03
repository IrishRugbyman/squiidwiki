"""Per-entity change history, read out of audit_log.

audit_log stores two kinds of row (see app/core/audit.py):

* **snapshots**, written by the ORM listeners on every insert/update/delete of
  an audited table: `diff_json` is the *whole row* after the write, not a diff.
  The diff a History tab shows is therefore computed here, by comparing each
  snapshot with the previous snapshot of the same entity. An UPDATE that
  changed nothing visible (only `updated_at`) diffs to nothing and is dropped.
* **link changes**, written by `record_link_change` from the sync functions of
  join tables (a member's sets and sources, an incident's participants, a set's
  gangs and alliances, ...): already a delta, with `_related` naming every far
  side. An entity's history includes the link rows written on it *and* the ones
  written on other entities that name it, so a set's history shows "Member A
  was added to this set" and a member's shows the incidents they were put in.

Because empty updates are dropped after the diff, filtering and paging happen
in Python over the entity's full history. One entity's history is tens to a
few hundred rows, so that is cheaper than it sounds and keeps the counts right.
"""

import uuid
from dataclasses import dataclass, field

from sqlalchemy import cast, or_, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import LINK_MARKER
from app.core.enums import AuditAction
from app.models.alliance import Alliance
from app.models.auth import AuditLog, User
from app.models.gang import Gang
from app.models.gang_set import GangSet
from app.models.incident import Incident
from app.models.member import Member
from app.models.municipality import Municipality
from app.models.source import Source

# API name -> (audit_log entity_type / table name, model)
HISTORY_ENTITIES: dict[str, tuple[str, type]] = {
    "member": ("member", Member),
    "set": ("sets", GangSet),
    "alliance": ("alliance", Alliance),
    "incident": ("incident", Incident),
    "source": ("source", Source),
}
_TABLE_TO_API = {table: api for api, (table, _) in HISTORY_ENTITIES.items()}

# Never shown as a change: identity, bookkeeping, and values derived from
# another column (sortable_date is computed from date).
_HIDDEN_FIELDS = {"id", "universe_id", "created_at", "updated_at", "sortable_date", "created_by_id"}
# Large blobs whose old -> new would swamp the page; shown as "changed".
_OPAQUE_FIELDS = {"territory_polygon", "territory_point", "geometry", "boundary", "geojson"}
# Long prose, diffed word by word in the UI.
_TEXT_FIELDS = {
    "biography",
    "bio",
    "description",
    "narrative",
    "notes",
    "content",
    "card_description",
}
_LONG_TEXT = 120


@dataclass
class FieldChange:
    field: str
    old: object = None
    new: object = None
    kind: str = "scalar"  # scalar | text | opaque


@dataclass
class HistoryEntry:
    id: uuid.UUID
    created_at: object
    action: str
    actor_id: uuid.UUID | None
    entity_type: str  # API name of the entity the row was written on
    entity_id: uuid.UUID
    is_self: bool
    link: str | None = None
    link_key: str | None = None
    added: list[dict] = field(default_factory=list)
    removed: list[dict] = field(default_factory=list)
    changed: list[dict] = field(default_factory=list)
    changes: list[FieldChange] = field(default_factory=list)
    baseline: bool = False


def _is_empty(v) -> bool:
    return v is None or v == "" or v == [] or v == {} or v is False


def _kind(name: str, old, new) -> str:
    if name in _OPAQUE_FIELDS:
        return "opaque"
    if name in _TEXT_FIELDS:
        return "text"
    for v in (old, new):
        if isinstance(v, str) and (len(v) > _LONG_TEXT or "\n" in v):
            return "text"
    return "scalar"


def _field_change(name: str, old, new) -> FieldChange:
    kind = _kind(name, old, new)
    if kind == "opaque":
        return FieldChange(field=name, kind=kind)
    return FieldChange(field=name, old=old, new=new, kind=kind)


def diff_snapshots(prev: dict | None, cur: dict) -> list[FieldChange]:
    """Field-level changes between two snapshot rows; prev=None means a create."""
    out: list[FieldChange] = []
    for name, new in cur.items():
        if name in _HIDDEN_FIELDS:
            continue
        if prev is None:
            if not _is_empty(new):
                out.append(_field_change(name, None, new))
            continue
        old = prev.get(name)
        if old != new and not (_is_empty(old) and _is_empty(new)):
            out.append(_field_change(name, old, new))
    return out


async def entity_history(
    session: AsyncSession, entity_type: str, entity_id: uuid.UUID
) -> list[HistoryEntry]:
    """Every visible change to one entity, newest first. `entity_type` is the API name."""
    table, _ = HISTORY_ENTITIES[entity_type]
    rows = (
        (
            await session.execute(
                select(AuditLog)
                .where(
                    or_(
                        (AuditLog.entity_type == table) & (AuditLog.entity_id == entity_id),
                        AuditLog.diff_json["_related"].op("@>")(cast([str(entity_id)], JSONB)),
                    )
                )
                .order_by(AuditLog.created_at, AuditLog.id)
            )
        )
        .scalars()
        .all()
    )

    entries: list[HistoryEntry] = []
    prev_snapshot: dict | None = None
    seen_snapshot = False
    for row in rows:
        diff = row.diff_json or {}
        is_self = row.entity_type == table and row.entity_id == entity_id
        base = dict(
            id=row.id,
            created_at=row.created_at,
            action=row.action.value if isinstance(row.action, AuditAction) else str(row.action),
            actor_id=row.user_id,
            entity_type=_TABLE_TO_API.get(row.entity_type, row.entity_type),
            entity_id=row.entity_id,
            is_self=is_self,
        )
        if LINK_MARKER in diff:
            entry = HistoryEntry(
                **base,
                link=diff[LINK_MARKER],
                link_key=diff.get("_key"),
                added=diff.get("added", []),
                removed=diff.get("removed", []),
                changed=diff.get("changed", []),
            )
            if not is_self:
                # Another entity's link list: keep only the rows about this one.
                me = str(entity_id)
                key = entry.link_key
                entry.added = [r for r in entry.added if str(r.get(key)) == me]
                entry.removed = [r for r in entry.removed if str(r.get(key)) == me]
                entry.changed = [c for c in entry.changed if c.get("key") == me]
            if entry.added or entry.removed or entry.changed:
                entries.append(entry)
            continue
        if not is_self:
            continue
        if diff.get("deleted") is True:
            entries.append(HistoryEntry(**base))
            prev_snapshot = None
            continue
        if base["action"] == AuditAction.CREATE.value:
            changes = diff_snapshots(None, diff)
            entries.append(HistoryEntry(**base, changes=changes))
        elif prev_snapshot is None:
            # An UPDATE with no earlier snapshot: the entity predates the audit
            # log (seeded or written in SQL). Nothing to diff against, so mark
            # the first one as the baseline and skip the rest until we have one.
            if not seen_snapshot:
                entries.append(HistoryEntry(**base, baseline=True))
        else:
            changes = diff_snapshots(prev_snapshot, diff)
            if changes:
                entries.append(HistoryEntry(**base, changes=changes))
        prev_snapshot = diff
        seen_snapshot = True

    entries.reverse()
    return entries


# ---------------------------------------------------------------------------
# Labels: turn the UUIDs an entry mentions into names the page can link.
# ---------------------------------------------------------------------------


def collect_ids(entries: list[HistoryEntry]) -> set[uuid.UUID]:
    found: set[uuid.UUID] = set()

    def visit(v):
        if isinstance(v, str) and len(v) == 36:
            try:
                found.add(uuid.UUID(v))
            except ValueError:
                pass
        elif isinstance(v, uuid.UUID):
            found.add(v)
        elif isinstance(v, dict):
            for x in v.values():
                visit(x)
        elif isinstance(v, list):
            for x in v:
                visit(x)

    for e in entries:
        found.add(e.entity_id)
        for c in e.changes:
            if c.field.endswith("_id"):
                visit(c.old)
                visit(c.new)
        for r in e.added + e.removed:
            visit(r)
        for c in e.changed:
            visit(c.get("key"))
    return found


def _incident_label(inc: Incident) -> str:
    from app.core.fuzzy_date import FuzzyDate

    when = ""
    if inc.date:
        try:
            when = FuzzyDate(**inc.date).display()
        except Exception:  # a malformed legacy date must not break the page
            when = ""
    kind = inc.type.value if hasattr(inc.type, "value") else str(inc.type)
    return f"{kind.title()} {when}".strip()


async def resolve_labels(session: AsyncSession, ids: set[uuid.UUID]) -> dict[str, dict]:
    """{id: {type, label, slug}} for every id that names a known entity."""
    if not ids:
        return {}
    out: dict[str, dict] = {}
    for m in (await session.execute(select(Member).where(Member.id.in_(ids)))).scalars():
        out[str(m.id)] = {"type": "member", "label": m.display_name, "slug": m.slug}
    for model, typ in ((GangSet, "set"), (Alliance, "alliance"), (Gang, "gang")):
        stmt = select(model.id, model.name, model.slug).where(model.id.in_(ids))
        for i, name, slug in (await session.execute(stmt)).all():
            out[str(i)] = {"type": typ, "label": name, "slug": slug}
    for i, title in (
        await session.execute(select(Source.id, Source.title).where(Source.id.in_(ids)))
    ).all():
        out[str(i)] = {"type": "source", "label": title, "slug": None}
    for inc in (await session.execute(select(Incident).where(Incident.id.in_(ids)))).scalars():
        out[str(inc.id)] = {"type": "incident", "label": _incident_label(inc), "slug": None}
    for i, name in (
        await session.execute(
            select(Municipality.id, Municipality.name).where(Municipality.id.in_(ids))
        )
    ).all():
        out[str(i)] = {"type": "municipality", "label": name, "slug": None}
    return out


async def resolve_actors(session: AsyncSession, ids: set[uuid.UUID]) -> dict[uuid.UUID, str]:
    if not ids:
        return {}
    rows = await session.execute(select(User.id, User.email).where(User.id.in_(ids)))
    return {i: email for i, email in rows.all()}
