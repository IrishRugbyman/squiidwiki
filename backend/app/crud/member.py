import uuid
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.member import Member, MemberSource
from app.schemas.common import make_cursor, parse_cursor
from app.schemas.member import MemberCreate, MemberUpdate


def _fuzzy_to_dict(fd) -> dict | None:
    if fd is None:
        return None
    return fd.model_dump()


async def _sync_member_sources(
    session: AsyncSession, member_id: uuid.UUID, source_ids: list[uuid.UUID]
) -> None:
    await session.execute(
        MemberSource.__table__.delete().where(MemberSource.member_id == member_id)
    )
    for sid in source_ids:
        session.add(MemberSource(member_id=member_id, source_id=sid))


async def create_member(
    session: AsyncSession, data: MemberCreate, actor_id: uuid.UUID
) -> Member:
    dump = data.model_dump(exclude={"source_ids", "dob", "date_of_death", "release_date"})
    dump["dob"] = _fuzzy_to_dict(data.dob)
    dump["date_of_death"] = _fuzzy_to_dict(data.date_of_death)
    dump["release_date"] = _fuzzy_to_dict(data.release_date)
    obj = Member(**dump, created_by_id=actor_id)
    session.add(obj)
    await session.flush()
    await _sync_member_sources(session, obj.id, data.source_ids)
    await session.commit()
    await session.refresh(obj)
    return obj


async def get_member(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> Member | None:
    result = await session.execute(
        select(Member).where(Member.id == id, Member.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def list_members(
    session: AsyncSession,
    universe_id: uuid.UUID,
    limit: int = 50,
    cursor: str | None = None,
    set_id: uuid.UUID | None = None,
) -> tuple[list[Member], str | None]:
    stmt = select(Member).where(Member.universe_id == universe_id)
    if set_id is not None:
        stmt = stmt.where(Member.set_id == set_id)

    if cursor:
        cursor_at, cursor_id = parse_cursor(cursor)
        stmt = stmt.where(
            (Member.created_at < cursor_at)
            | ((Member.created_at == cursor_at) & (Member.id < cursor_id))
        )

    stmt = stmt.order_by(Member.created_at.desc(), Member.id.desc()).limit(limit + 1)
    result = await session.execute(stmt)
    items = result.scalars().all()

    next_cursor = None
    if len(items) > limit:
        items = items[:limit]
        last = items[-1]
        next_cursor = make_cursor(last.created_at, last.id)

    return items, next_cursor


async def update_member(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, data: MemberUpdate
) -> Member | None:
    obj = await get_member(session, id, universe_id)
    if obj is None:
        return None
    dump = data.model_dump(
        exclude_unset=True, exclude={"source_ids", "dob", "date_of_death", "release_date"}
    )
    if "dob" in data.model_fields_set:
        dump["dob"] = _fuzzy_to_dict(data.dob)
    if "date_of_death" in data.model_fields_set:
        dump["date_of_death"] = _fuzzy_to_dict(data.date_of_death)
    if "release_date" in data.model_fields_set:
        dump["release_date"] = _fuzzy_to_dict(data.release_date)
    dump["updated_at"] = datetime.utcnow()
    for k, v in dump.items():
        setattr(obj, k, v)
    session.add(obj)
    if data.source_ids is not None:
        await _sync_member_sources(session, obj.id, data.source_ids)
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_member(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> bool:
    obj = await get_member(session, id, universe_id)
    if obj is None:
        return False
    await session.delete(obj)
    await session.commit()
    return True


async def list_member_source_ids(
    session: AsyncSession, member_id: uuid.UUID
) -> list[uuid.UUID]:
    result = await session.execute(
        select(MemberSource.source_id).where(MemberSource.member_id == member_id)
    )
    return result.scalars().all()


async def search_members(
    session: AsyncSession, universe_id: uuid.UUID, q: str
) -> list[Member]:
    result = await session.execute(
        select(Member).where(
            Member.universe_id == universe_id,
            Member.nickname.ilike(f"%{q}%") | Member.legal_name.ilike(f"%{q}%"),
        )
    )
    return result.scalars().all()


async def get_member_stats(session: AsyncSession, member_id: uuid.UUID) -> dict | None:
    try:
        result = await session.execute(
            text("SELECT * FROM member_stats WHERE member_id = :mid"),
            {"mid": member_id},
        )
        row = result.mappings().one_or_none()
        if row:
            return dict(row)
    except Exception:
        await session.rollback()
    return {
        "member_id": member_id,
        "shootings": 0,
        "assists": 0,
        "kills": 0,
        "times_shot_survived": 0,
    }
