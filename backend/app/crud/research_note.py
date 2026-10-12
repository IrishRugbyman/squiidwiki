import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core.enums import NoteKind
from app.core.fuzzy_date import FuzzyDate
from app.models.alliance import Alliance
from app.models.gang_set import GangSet
from app.models.incident import Incident
from app.models.member import Member
from app.models.research_note import ResearchNote, ResearchNotePin
from app.schemas.research_note import (
    PinKind,
    PinRead,
    PinRef,
    ResearchNoteCreate,
    ResearchNoteListItem,
    ResearchNoteRead,
    ResearchNoteUpdate,
)

# Pin kind -> (entity model, ResearchNotePin column holding its id).
_PIN_TARGETS: dict[str, tuple[type, str]] = {
    "member": (Member, "member_id"),
    "set": (GangSet, "set_id"),
    "incident": (Incident, "incident_id"),
    "alliance": (Alliance, "alliance_id"),
}
_PIN_ORDER = {kind: i for i, kind in enumerate(_PIN_TARGETS)}


def _incident_label(inc: Incident) -> str:
    """A label for an incident, which has no name: its date and where it happened."""
    parts = []
    if inc.date:
        text = FuzzyDate(**inc.date).display()
        if text != "unknown":
            parts.append(text)
    if inc.location_text:
        parts.append(inc.location_text)
    return ", ".join(parts) if parts else "Incident"


def _pin_read(kind: PinKind, entity) -> PinRead:
    if kind == "member":
        return PinRead(kind=kind, id=entity.id, slug=entity.slug, name=entity.display_name)
    if kind == "incident":
        return PinRead(kind=kind, id=entity.id, slug=None, name=_incident_label(entity))
    return PinRead(kind=kind, id=entity.id, slug=entity.slug, name=entity.name)


async def _pins_for(
    session: AsyncSession, note_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[PinRead]]:
    """Resolve the pins of several notes to what the UI needs, one query per entity kind."""
    out: dict[uuid.UUID, list[PinRead]] = {nid: [] for nid in note_ids}
    if not note_ids:
        return out
    rows = (
        (
            await session.execute(
                select(ResearchNotePin).where(ResearchNotePin.note_id.in_(note_ids))
            )
        )
        .scalars()
        .all()
    )
    for kind, (model, col) in _PIN_TARGETS.items():
        ids = {getattr(r, col) for r in rows if getattr(r, col) is not None}
        if not ids:
            continue
        entities = {
            e.id: e
            for e in (await session.execute(select(model).where(model.id.in_(ids)))).scalars().all()
        }
        for r in rows:
            target = getattr(r, col)
            if target is not None and target in entities:
                out[r.note_id].append(_pin_read(kind, entities[target]))
    for pins in out.values():
        pins.sort(key=lambda p: (_PIN_ORDER[p.kind], p.name.lower()))
    return out


async def _with_pins(session: AsyncSession, notes: list[ResearchNote], schema: type) -> list:
    pins = await _pins_for(session, [n.id for n in notes])
    return [schema.model_validate(n).model_copy(update={"pins": pins[n.id]}) for n in notes]


async def _validate_pins(
    session: AsyncSession, universe_id: uuid.UUID, pins: list[PinRef]
) -> list[PinRef]:
    """Drop duplicates and 422 on a pin whose entity is missing or in another universe."""
    unique = list(dict.fromkeys((p.kind, p.id) for p in pins))
    for kind, id_ in unique:
        model = _PIN_TARGETS[kind][0]
        found = await session.execute(
            select(model.id).where(model.id == id_, model.universe_id == universe_id)
        )
        if found.scalar_one_or_none() is None:
            raise HTTPException(422, f"Cannot pin {kind} {id_}: not found in this universe")
    return [PinRef(kind=k, id=i) for k, i in unique]


def _add_pins(session: AsyncSession, note_id: uuid.UUID, pins: list[PinRef]) -> None:
    for p in pins:
        session.add(ResearchNotePin(note_id=note_id, **{_PIN_TARGETS[p.kind][1]: p.id}))


async def create_note(
    session: AsyncSession, data: ResearchNoteCreate, actor_id: uuid.UUID
) -> ResearchNoteRead:
    pins = await _validate_pins(session, data.universe_id, data.pins)
    obj = ResearchNote(**data.model_dump(exclude={"pins"}), created_by_id=actor_id)
    session.add(obj)
    await session.flush()
    _add_pins(session, obj.id, pins)
    await session.commit()
    await session.refresh(obj)
    return (await _with_pins(session, [obj], ResearchNoteRead))[0]


async def _get_note_row(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> ResearchNote | None:
    result = await session.execute(
        select(ResearchNote).where(ResearchNote.id == id, ResearchNote.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def get_note(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> ResearchNoteRead | None:
    obj = await _get_note_row(session, id, universe_id)
    if obj is None:
        return None
    return (await _with_pins(session, [obj], ResearchNoteRead))[0]


async def list_notes(
    session: AsyncSession,
    universe_id: uuid.UUID,
    offset: int = 0,
    limit: int = 50,
    kind: NoteKind | None = None,
) -> tuple[list[ResearchNoteListItem], int]:
    where = [ResearchNote.universe_id == universe_id]
    if kind is not None:
        where.append(ResearchNote.kind == kind.value)
    total = (
        await session.execute(select(func.count()).select_from(ResearchNote).where(*where))
    ).scalar_one()
    result = await session.execute(
        select(ResearchNote)
        .where(*where)
        .order_by(ResearchNote.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return await _with_pins(session, result.scalars().all(), ResearchNoteListItem), total


async def search_notes(
    session: AsyncSession, universe_id: uuid.UUID, q: str
) -> list[ResearchNoteListItem]:
    result = await session.execute(
        select(ResearchNote)
        .where(
            ResearchNote.universe_id == universe_id,
            (ResearchNote.title.ilike(f"%{q}%") | ResearchNote.content.ilike(f"%{q}%")),
        )
        .order_by(ResearchNote.updated_at.desc())
    )
    return await _with_pins(session, result.scalars().all(), ResearchNoteListItem)


async def list_pinned_notes(
    session: AsyncSession, universe_id: uuid.UUID, kind: PinKind, entity_id: uuid.UUID
) -> list[ResearchNoteListItem]:
    """The notes pinned to one entity, newest first."""
    col = getattr(ResearchNotePin, _PIN_TARGETS[kind][1])
    result = await session.execute(
        select(ResearchNote)
        .join(ResearchNotePin, ResearchNotePin.note_id == ResearchNote.id)
        .where(ResearchNote.universe_id == universe_id, col == entity_id)
        .order_by(ResearchNote.updated_at.desc())
    )
    return await _with_pins(session, result.scalars().all(), ResearchNoteListItem)


async def update_note(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, data: ResearchNoteUpdate
) -> ResearchNoteRead | None:
    obj = await _get_note_row(session, id, universe_id)
    if obj is None:
        return None
    changes = data.model_dump(exclude_unset=True)
    pins = changes.pop("pins", None)
    if pins is not None:
        wanted = await _validate_pins(session, universe_id, data.pins or [])
        await session.execute(
            ResearchNotePin.__table__.delete().where(ResearchNotePin.note_id == id)
        )
        _add_pins(session, id, wanted)
    for k, v in changes.items():
        setattr(obj, k, v)
    obj.updated_at = datetime.now(UTC)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return (await _with_pins(session, [obj], ResearchNoteRead))[0]


async def delete_note(session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID) -> bool:
    obj = await _get_note_row(session, id, universe_id)
    if obj is None:
        return False
    await session.delete(obj)
    await session.commit()
    return True
