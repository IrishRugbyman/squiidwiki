import uuid
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import MemberStatus, ParticipantOutcome
from app.models.gang_set import GangSet
from app.models.incident import (
    Incident,
    IncidentParticipant,
    IncidentSetParticipant,
    IncidentSource,
)
from app.models.member import Member, MemberSet
from app.schemas.common import make_cursor, parse_cursor
from app.schemas.incident import (
    IncidentCreate,
    IncidentUpdate,
    ParticipantCreate,
    SetParticipantCreate,
)


def _fuzzy_to_dict(fd) -> dict | None:
    if fd is None:
        return None
    return fd.model_dump()


async def _sync_participants(
    session: AsyncSession, incident_id: uuid.UUID, participants: list[ParticipantCreate]
) -> None:
    await session.execute(
        IncidentParticipant.__table__.delete().where(IncidentParticipant.incident_id == incident_id)
    )
    for p in participants:
        session.add(
            IncidentParticipant(
                incident_id=incident_id,
                member_id=p.member_id,
                role=p.role,
                outcome=p.outcome,
                acquitted=p.acquitted,
                notes=p.notes,
            )
        )


async def _sync_set_participants(
    session: AsyncSession, incident_id: uuid.UUID, set_participants: list[SetParticipantCreate]
) -> None:
    await session.execute(
        IncidentSetParticipant.__table__.delete().where(
            IncidentSetParticipant.incident_id == incident_id
        )
    )
    for p in set_participants:
        session.add(
            IncidentSetParticipant(
                incident_id=incident_id,
                set_id=p.set_id,
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


async def _unsync_killed_participants(
    session: AsyncSession, incident: Incident, new_participants: list[ParticipantCreate]
) -> None:
    """On incident update, clear death linkage for members who are no longer KILLED."""
    new_killed_ids = {
        p.member_id for p in new_participants if p.outcome == ParticipantOutcome.KILLED
    }

    result = await session.execute(
        select(Member).where(
            Member.death_incident_id == incident.id,
            Member.universe_id == incident.universe_id,
        )
    )
    prev_linked = result.scalars().all()

    now = datetime.now(UTC)
    for m in prev_linked:
        if m.id not in new_killed_ids:
            m.death_incident_id = None
            m.date_of_death = None
            m.status = MemberStatus.UNKNOWN
            m.updated_at = now
            session.add(m)


async def _sync_killed_participants(
    session: AsyncSession,
    incident: Incident,
    participants: list[ParticipantCreate],
    previous_date: dict | None = None,
) -> None:
    """
    Propagate KILLED-participant outcomes onto the member record:
      - status -> DEAD if not already
      - death_incident_id -> this incident (first death wins; never override an
        existing link to a different incident)
      - date_of_death -> incident.date, but only when this incident is what put
        the date there in the first place (see below)

    ``previous_date`` is the incident's date *before* this edit, which only
    ``update_incident`` can know; on create it is None.

    **A date_of_death that disagrees with the incident was entered by hand and
    outranks this sync.** The shooting and the death it causes are separate
    events: Djuan Page was shot 14 Jul 2014 and died in August, and this
    function used to overwrite the August date on every single save of that
    incident, so the hand correction never survived the next edit. A date is
    therefore only written when it is null, or still equal to whatever the
    incident said a moment ago - which keeps genuine incident-date corrections
    propagating to members who never got a manual date.

    Never reverts; un-kill is a manual member edit. Audit listeners on `member`
    pick these mutations up automatically.
    """
    killed_ids = [p.member_id for p in participants if p.outcome == ParticipantOutcome.KILLED]
    if not killed_ids:
        return

    result = await session.execute(
        select(Member).where(Member.id.in_(killed_ids), Member.universe_id == incident.universe_id)
    )
    members = result.scalars().all()

    incident_date = incident.date
    incident_has_date = bool(incident_date and incident_date.get("year"))

    now = datetime.now(UTC)
    for m in members:
        if m.status != MemberStatus.DEAD:
            m.status = MemberStatus.DEAD
        if m.death_incident_id is None:
            m.death_incident_id = incident.id
        date_is_ours = m.date_of_death is None or (
            previous_date is not None and m.date_of_death == previous_date
        )
        if m.death_incident_id == incident.id and incident_has_date and date_is_ours:
            m.date_of_death = incident_date
        m.updated_at = now
        session.add(m)


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

    dump = data.model_dump(exclude={"date", "participants", "set_participants", "source_ids"})
    dump["date"] = _fuzzy_to_dict(fd)
    dump["sortable_date"] = sortable
    obj = Incident(**dump, created_by_id=actor_id)
    session.add(obj)
    await session.flush()
    await _sync_participants(session, obj.id, data.participants)
    await _sync_set_participants(session, obj.id, data.set_participants)
    await _sync_incident_sources(session, obj.id, data.source_ids)
    await _sync_killed_participants(session, obj, data.participants)
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


async def list_incidents_by_capability(
    session: AsyncSession,
    universe_id: uuid.UUID,
    *,
    needs: str,
    limit: int = 2000,
) -> list[Incident]:
    """Incidents a given view can actually render.

    The generic listing pages by creation date, so a map or a calendar built on it
    shows whichever incidents happen to be newest rather than the ones carrying
    what it needs. Selecting on the field itself is both correct and naturally
    bounded: almost no incident has coordinates, and only a small minority has a
    date precise enough to place.

    `needs` is "coords" or "date".
    """
    stmt = select(Incident).where(Incident.universe_id == universe_id)
    if needs == "coords":
        stmt = stmt.where(Incident.lat.is_not(None), Incident.lng.is_not(None))
    elif needs == "date":
        # sortable_date is written only when the fuzzy date has at least a year,
        # which is exactly what both the calendar and the timeline require.
        stmt = stmt.where(Incident.sortable_date.is_not(None))
    else:
        raise ValueError(f"unknown capability {needs!r}")
    stmt = stmt.order_by(
        Incident.sortable_date.desc().nullslast(), Incident.created_at.desc()
    ).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


async def update_incident(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, data: IncidentUpdate
) -> Incident | None:
    obj = await get_incident(session, id, universe_id)
    if obj is None:
        return None
    # Read before the setattr loop below replaces it: _sync_killed_participants
    # needs to tell a member date it wrote itself from one a human wrote.
    previous_date = obj.date
    dump = data.model_dump(
        exclude_unset=True, exclude={"date", "participants", "set_participants", "source_ids"}
    )
    if "date" in data.model_fields_set:
        fd = data.date
        dump["date"] = _fuzzy_to_dict(fd)
        if fd is not None:
            sd = fd.to_sortable_date()
            if sd is not None:
                dump["sortable_date"] = datetime(sd.year, sd.month, sd.day)
            else:
                dump["sortable_date"] = None
        else:
            dump["sortable_date"] = None
    for k, v in dump.items():
        setattr(obj, k, v)
    obj.updated_at = datetime.now(UTC)
    session.add(obj)
    if data.participants is not None:
        await _unsync_killed_participants(session, obj, data.participants)
        await _sync_participants(session, obj.id, data.participants)
        await _sync_killed_participants(session, obj, data.participants, previous_date)
    if data.set_participants is not None:
        await _sync_set_participants(session, obj.id, data.set_participants)
    if data.source_ids is not None:
        await _sync_incident_sources(session, obj.id, data.source_ids)
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_incident(session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID) -> bool:
    obj = await get_incident(session, id, universe_id)
    if obj is None:
        return False
    # incident_participant and incident_source have NO ACTION FKs - clear them
    # first or the delete raises. Set participants and media cascade, and
    # member.death_incident_id is ON DELETE SET NULL.
    await session.execute(
        IncidentParticipant.__table__.delete().where(IncidentParticipant.incident_id == id)
    )
    await session.execute(IncidentSource.__table__.delete().where(IncidentSource.incident_id == id))
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


async def participant_member_briefs(
    session: AsyncSession, member_ids: list[uuid.UUID]
) -> dict[uuid.UUID, Member]:
    """Members referenced by an incident's participants, for name enrichment."""
    if not member_ids:
        return {}
    result = await session.execute(select(Member).where(Member.id.in_(member_ids)))
    return {m.id: m for m in result.scalars()}


async def participant_set_briefs(
    session: AsyncSession, set_ids: list[uuid.UUID]
) -> dict[uuid.UUID, GangSet]:
    """Sets referenced by an incident's set participants, for name enrichment."""
    if not set_ids:
        return {}
    result = await session.execute(select(GangSet).where(GangSet.id.in_(set_ids)))
    return {s.id: s for s in result.scalars()}


async def list_incident_set_participants(
    session: AsyncSession, incident_id: uuid.UUID
) -> list[IncidentSetParticipant]:
    result = await session.execute(
        select(IncidentSetParticipant).where(IncidentSetParticipant.incident_id == incident_id)
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
        .join(MemberSet, (MemberSet.member_id == Member.id) & (MemberSet.set_id == set_id))
        .where(Incident.universe_id == universe_id)
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
        # Same union as list_members' alliance filter: an alliance's people are
        # those tagged straight to it plus the current members of its sets.
        # Joining on Member.alliance_id alone reported no incidents for an
        # alliance whose sets were full of participants.
        .where(
            (Member.alliance_id == alliance_id)
            | Member.id.in_(
                select(MemberSet.member_id).where(
                    MemberSet.set_id.in_(
                        select(GangSet.id).where(GangSet.alliance_id == alliance_id)
                    ),
                    MemberSet.until_date.is_(None),
                )
            ),
            Incident.universe_id == universe_id,
        )
        .distinct()
        .order_by(Incident.sortable_date.desc(), Incident.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def list_incidents_by_municipality(
    session: AsyncSession,
    municipality_id: uuid.UUID,
    universe_id: uuid.UUID,
    limit: int = 50,
) -> list[Incident]:
    stmt = (
        select(Incident)
        .where(Incident.municipality_id == municipality_id, Incident.universe_id == universe_id)
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


async def search_incidents(session: AsyncSession, universe_id: uuid.UUID, q: str) -> list[Incident]:
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
