"""Citations: every write and read of "this record cites this source".

Every path that links a source to a record goes through here, so the rules
live in one place:

- a citation stays inside one universe (source, record and citation agree);
- one citation per (source, record): a second attach updates or is skipped;
- writes go through the ORM (`session.add` / `session.delete`), never a bulk
  `DELETE`, because the audit log hangs off mapper events and a bulk statement
  would skip them.

Callers own the transaction: nothing here commits.
"""

import uuid
from collections.abc import Iterable
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models.alliance import Alliance
from app.models.business import Business
from app.models.citation import TARGET_COLUMN, Citation
from app.models.court_case import CourtCase
from app.models.gang_set import GangSet
from app.models.incident import Incident
from app.models.member import Member
from app.models.municipality import Municipality
from app.models.rap_group import RapGroup
from app.models.source import Source
from app.schemas.citation import CitationCreate, CitationRead, CitationUpdate, SourceSummary

ENTITY_MODELS = {
    "member": Member,
    "incident": Incident,
    "set": GangSet,
    "alliance": Alliance,
    "rap_group": RapGroup,
    "court_case": CourtCase,
    "municipality": Municipality,
    "business": Business,
}


def _target_column(entity_type: str):
    try:
        return getattr(Citation, TARGET_COLUMN[entity_type])
    except KeyError:
        raise HTTPException(422, f"Unknown entity type {entity_type!r}") from None


async def entity_universe(
    session: AsyncSession, entity_type: str, entity_id: uuid.UUID
) -> uuid.UUID | None:
    """The universe a record belongs to, or None if there is no such record."""
    model = ENTITY_MODELS[entity_type]
    return (
        await session.execute(select(model.universe_id).where(model.id == entity_id))
    ).scalar_one_or_none()


def to_read(citation: Citation, source: Source) -> CitationRead:
    return CitationRead(
        id=citation.id,
        source_id=citation.source_id,
        position=citation.position,
        locator=citation.locator,
        quote=citation.quote,
        note=citation.note,
        accessed_at=citation.accessed_at,
        created_at=citation.created_at,
        source=SourceSummary.model_validate(source),
    )


async def list_citations(
    session: AsyncSession, entity_type: str, entity_id: uuid.UUID
) -> list[CitationRead]:
    """A record's citations with their sources, in display order."""
    col = _target_column(entity_type)
    rows = await session.execute(
        select(Citation, Source)
        .join(Source, Source.id == Citation.source_id)
        .where(col == entity_id)
        .order_by(Citation.position, Citation.created_at, Citation.id)
    )
    return [to_read(c, s) for c, s in rows.all()]


async def _sources_in_universe(
    session: AsyncSession, ids: Iterable[uuid.UUID], universe_id: uuid.UUID
) -> dict[uuid.UUID, Source]:
    wanted = list(dict.fromkeys(ids))
    if not wanted:
        return {}
    rows = await session.execute(
        select(Source).where(Source.id.in_(wanted), Source.universe_id == universe_id)
    )
    found = {s.id: s for s in rows.scalars().all()}
    missing = [str(i) for i in wanted if i not in found]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Sources not found in this universe: {', '.join(missing)}",
        )
    return found


async def _next_position(session: AsyncSession, entity_type: str, entity_id: uuid.UUID) -> int:
    col = _target_column(entity_type)
    current = (
        await session.execute(select(func.max(Citation.position)).where(col == entity_id))
    ).scalar_one_or_none()
    return 0 if current is None else current + 1


async def _existing(
    session: AsyncSession, entity_type: str, entity_id: uuid.UUID, source_id: uuid.UUID
) -> Citation | None:
    col = _target_column(entity_type)
    return (
        await session.execute(
            select(Citation).where(col == entity_id, Citation.source_id == source_id)
        )
    ).scalar_one_or_none()


async def _check_target(
    session: AsyncSession, universe_id: uuid.UUID, entity_type: str, entity_id: uuid.UUID
) -> None:
    found = await entity_universe(session, entity_type, entity_id)
    if found is None:
        raise HTTPException(404, f"No {entity_type} {entity_id}")
    if found != universe_id:
        raise HTTPException(422, f"The {entity_type} is in another universe than the source")


async def create_citation(
    session: AsyncSession, universe_id: uuid.UUID, data: CitationCreate, actor_id: uuid.UUID
) -> CitationRead:
    sources = await _sources_in_universe(session, [data.source_id], universe_id)
    await _check_target(session, universe_id, data.entity_type, data.entity_id)
    prior = await _existing(session, data.entity_type, data.entity_id, data.source_id)
    if prior is not None:
        raise ApiError(
            409, "citation_exists", "This record already cites this source.", citation_id=prior.id
        )
    position = (
        data.position
        if data.position is not None
        else await _next_position(session, data.entity_type, data.entity_id)
    )
    obj = Citation(
        universe_id=universe_id,
        source_id=data.source_id,
        locator=data.locator,
        quote=data.quote,
        note=data.note,
        accessed_at=data.accessed_at,
        position=position,
        created_by_id=actor_id,
        **{TARGET_COLUMN[data.entity_type]: data.entity_id},
    )
    session.add(obj)
    await session.flush()
    return to_read(obj, sources[data.source_id])


async def batch_citations(
    session: AsyncSession,
    universe_id: uuid.UUID,
    items: list[CitationCreate],
    on_conflict: str,
    actor_id: uuid.UUID,
) -> dict[str, list[uuid.UUID]]:
    """Cite many (source, record) pairs at once, all or nothing.

    Everything is validated before anything is written, and a failure names
    every bad item, so a reverse attach of fifty records never half-lands.
    """
    await _sources_in_universe(session, [i.source_id for i in items], universe_id)
    problems: list[str] = []
    for n, item in enumerate(items):
        found = await entity_universe(session, item.entity_type, item.entity_id)
        if found is None:
            problems.append(f"item {n}: no {item.entity_type} {item.entity_id}")
        elif found != universe_id:
            problems.append(f"item {n}: the {item.entity_type} is in another universe")
    if problems:
        raise HTTPException(422, "; ".join(problems))

    result: dict[str, list[uuid.UUID]] = {"created": [], "updated": [], "skipped": []}
    next_pos: dict[tuple[str, uuid.UUID], int] = {}
    seen: set[tuple[str, uuid.UUID, uuid.UUID]] = set()
    for item in items:
        key = (item.entity_type, item.entity_id, item.source_id)
        if key in seen:
            continue
        seen.add(key)
        prior = await _existing(session, item.entity_type, item.entity_id, item.source_id)
        if prior is not None:
            if on_conflict == "update":
                changed = False
                for field in ("locator", "quote", "note", "accessed_at"):
                    value = getattr(item, field)
                    if value is not None and getattr(prior, field) != value:
                        setattr(prior, field, value)
                        changed = True
                if changed:
                    prior.updated_at = datetime.now(UTC)
                    session.add(prior)
                    result["updated"].append(prior.id)
                else:
                    result["skipped"].append(prior.id)
            else:
                result["skipped"].append(prior.id)
            continue
        target = (item.entity_type, item.entity_id)
        if target not in next_pos:
            next_pos[target] = await _next_position(session, *target)
        position = item.position if item.position is not None else next_pos[target]
        next_pos[target] = max(next_pos[target], position + 1)
        obj = Citation(
            universe_id=universe_id,
            source_id=item.source_id,
            locator=item.locator,
            quote=item.quote,
            note=item.note,
            accessed_at=item.accessed_at,
            position=position,
            created_by_id=actor_id,
            **{TARGET_COLUMN[item.entity_type]: item.entity_id},
        )
        session.add(obj)
        await session.flush()
        result["created"].append(obj.id)
    return result


async def get_citation(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> Citation | None:
    return (
        await session.execute(
            select(Citation).where(Citation.id == id, Citation.universe_id == universe_id)
        )
    ).scalar_one_or_none()


async def update_citation(
    session: AsyncSession, obj: Citation, data: CitationUpdate
) -> CitationRead:
    fields = data.model_dump(exclude_unset=True)
    new_source = fields.pop("source_id", None)
    if new_source is not None and new_source != obj.source_id:
        await _sources_in_universe(session, [new_source], obj.universe_id)
        entity_type, entity_id = obj.target()
        clash = await _existing(session, entity_type, entity_id, new_source)
        if clash is not None:
            raise ApiError(
                409,
                "citation_exists",
                "This record already cites that source.",
                citation_id=clash.id,
            )
        obj.source_id = new_source
    for k, v in fields.items():
        setattr(obj, k, v)
    obj.updated_at = datetime.now(UTC)
    session.add(obj)
    await session.flush()
    source = await session.get(Source, obj.source_id)
    return to_read(obj, source)


async def reorder_citations(
    session: AsyncSession, entity_type: str, entity_id: uuid.UUID, ids: list[uuid.UUID]
) -> list[CitationRead]:
    col = _target_column(entity_type)
    existing = (await session.execute(select(Citation).where(col == entity_id))).scalars().all()
    if len(ids) != len(set(ids)) or set(ids) != {c.id for c in existing}:
        raise HTTPException(422, "ids must list every citation of the record exactly once")
    by_id = {c.id: c for c in existing}
    for position, cid in enumerate(ids):
        c = by_id[cid]
        if c.position != position:
            c.position = position
            session.add(c)
    await session.flush()
    return await list_citations(session, entity_type, entity_id)
