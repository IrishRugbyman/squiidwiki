import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.incident import Incident, IncidentParticipant, IncidentSource
from app.models.member import Member, MemberSource
from app.models.alliance import AllianceSet
from app.models.gang_set import GangSet
from app.schemas.common import make_cursor, parse_cursor
from app.schemas.incident import IncidentCreate, IncidentUpdate, ParticipantCreate


def _fuzzy_to_dict(fd) -> dict | None:
    if fd is None:
        return None
    return fd.model_dump()


async def _sync_participants(
    session: AsyncSession, incident_id: uuid.UUID, participants: list[ParticipantCreate]
) -> None:
    await session.execute(
        IncidentParticipant.__table__.delete().where(
            IncidentParticipant.incident_id == incident_id
        )
    )
    for p in participants:
        session.add(
            IncidentParticipant(
                incident_id=incident_id,
                member_id=p.member_id,
                role=p.role,
                outcome=p.outcome,
                notes=p.notes,
            )
        )


async def _sync_incident_sources(
    session: AsyncSession, incident_id: uuid.UUID, source_ids: list[uuid.UUID]
) -> None:
    await session.execute(
        IncidentSource.__table__.delete().where(IncidentSource.incident_id == incident_id)
    )
    for sid in source_ids:
        session.add(IncidentSource(incident_id=incident_id, source_id=sid))


async def create_incident(
    session: AsyncSession, data: IncidentCreate, actor_id: uuid.UUID
) -> Incident:
    fd = data.date
    sortable = None
    if fd is not None:
        sd = fd.to_sortable_date()
        if sd is not None:
            from datetime import datetime
            sortable = datetime(sd.year, sd.month, sd.day)

    dump = data.model_dump(exclude={"date", "participants", "source_ids"})
    dump["date"] = _fuzzy_to_dict(fd)
    dump["sortable_date"] = sortable
    obj = Incident(**dump, created_by_id=actor_id)
    session.add(obj)
    await session.flush()
    await _sync_participants(session, obj.id, data.participants)
    await _sync_incident_sources(session, obj.id, data.source_ids)
    await session.commit()
    await session.refresh(obj)
    return obj


async def get_incident(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> Incident | None:
    result = await session.execute(
        select(Incident).where(Incident.id == id, Incident.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def list_incidents(
    session: AsyncSession,
    universe_id: uuid.UUID,
    limit: int = 50,
    cursor: str | None = None,
) -> tuple[list[Incident], str | None]:
    stmt = select(Incident).where(Incident.universe_id == universe_id)

    if cursor:
        cursor_at, cursor_id = parse_cursor(cursor)
        stmt = stmt.where(
            (Incident.created_at < cursor_at)
            | ((Incident.created_at == cursor_at) & (Incident.id < cursor_id))
        )

    stmt = stmt.order_by(Incident.created_at.desc(), Incident.id.desc()).limit(limit + 1)
    result = await session.execute(stmt)
    items = result.scalars().all()

    next_cursor = None
    if len(items) > limit:
        items = items[:limit]
        last = items[-1]
        next_cursor = make_cursor(last.created_at, last.id)

    return items, next_cursor


async def update_incident(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, data: IncidentUpdate
) -> Incident | None:
    obj = await get_incident(session, id, universe_id)
    if obj is None:
        return None
    dump = data.model_dump(exclude_unset=True, exclude={"date", "participants", "source_ids"})
    if "date" in data.model_fields_set:
        fd = data.date
        dump["date"] = _fuzzy_to_dict(fd)
        if fd is not None:
            sd = fd.to_sortable_date()
            if sd is not None:
                from datetime import datetime
                dump["sortable_date"] = datetime(sd.year, sd.month, sd.day)
            else:
                dump["sortable_date"] = None
        else:
            dump["sortable_date"] = None
    for k, v in dump.items():
        setattr(obj, k, v)
    session.add(obj)
    if data.participants is not None:
        await _sync_participants(session, obj.id, data.participants)
    if data.source_ids is not None:
        await _sync_incident_sources(session, obj.id, data.source_ids)
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_incident(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> bool:
    obj = await get_incident(session, id, universe_id)
    if obj is None:
        return False
    await session.delete(obj)
    await session.commit()
    return True


async def list_incident_participants(
    session: AsyncSession, incident_id: uuid.UUID
) -> list[IncidentParticipant]:
    result = await session.execute(
        select(IncidentParticipant).where(IncidentParticipant.incident_id == incident_id)
    )
    return result.scalars().all()


async def list_incidents_by_member(
    session: AsyncSession,
    member_id: uuid.UUID,
    universe_id: uuid.UUID,
    limit: int = 50,
) -> list[Incident]:
    stmt = (
        select(Incident)
        .join(IncidentParticipant, IncidentParticipant.incident_id == Incident.id)
        .where(IncidentParticipant.member_id == member_id, Incident.universe_id == universe_id)
        .order_by(Incident.sortable_date.desc(), Incident.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def list_incidents_by_set(
    session: AsyncSession,
    set_id: uuid.UUID,
    universe_id: uuid.UUID,
    limit: int = 50,
) -> list[Incident]:
    stmt = (
        select(Incident)
        .join(IncidentParticipant, IncidentParticipant.incident_id == Incident.id)
        .join(Member, Member.id == IncidentParticipant.member_id)
        .where(Member.set_id == set_id, Incident.universe_id == universe_id)
        .distinct()
        .order_by(Incident.sortable_date.desc(), Incident.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def list_incidents_by_alliance(
    session: AsyncSession,
    alliance_id: uuid.UUID,
    universe_id: uuid.UUID,
    limit: int = 50,
) -> list[Incident]:
    stmt = (
        select(Incident)
        .join(IncidentParticipant, IncidentParticipant.incident_id == Incident.id)
        .join(Member, Member.id == IncidentParticipant.member_id)
        .where(Member.alliance_id == alliance_id, Incident.universe_id == universe_id)
        .distinct()
        .order_by(Incident.sortable_date.desc(), Incident.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def list_incidents_by_source(
    session: AsyncSession,
    source_id: uuid.UUID,
    universe_id: uuid.UUID,
    limit: int = 100,
) -> list[Incident]:
    stmt = (
        select(Incident)
        .join(IncidentSource, IncidentSource.incident_id == Incident.id)
        .where(IncidentSource.source_id == source_id, Incident.universe_id == universe_id)
        .order_by(Incident.sortable_date.desc(), Incident.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def list_incident_source_ids(
    session: AsyncSession, incident_id: uuid.UUID
) -> list[uuid.UUID]:
    result = await session.execute(
        select(IncidentSource.source_id).where(IncidentSource.incident_id == incident_id)
    )
    return result.scalars().all()


async def search_incidents(
    session: AsyncSession, universe_id: uuid.UUID, q: str
) -> list[Incident]:
    result = await session.execute(
        select(Incident).where(
            Incident.universe_id == universe_id,
            Incident.narrative.ilike(f"%{q}%") | Incident.location_text.ilike(f"%{q}%"),
        )
    )
    return result.scalars().all()


async def get_set_stats(session: AsyncSession, set_id: uuid.UUID) -> dict | None:
    try:
        result = await session.execute(
            text("SELECT * FROM set_stats WHERE set_id = :sid"),
            {"sid": set_id},
        )
        row = result.mappings().one_or_none()
        if row:
            return dict(row)
    except Exception:
        await session.rollback()
    return {
        "set_id": set_id,
        "member_count": 0,
        "dead_members": 0,
        "total_shootings": 0,
        "total_assists": 0,
        "total_kills": 0,
    }
