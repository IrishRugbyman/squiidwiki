import re
import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.models.business import Business, BusinessMember, BusinessSet, BusinessSource
from app.models.member import Member
from app.models.municipality import Municipality
from app.schemas.business import BusinessCreate, BusinessMemberOut, BusinessUpdate


def _fuzzy_to_dict(fd) -> dict | None:
    if fd is None:
        return None
    return fd.model_dump()


def _slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-") or "business"


async def _unique_slug(
    session: AsyncSession, universe_id: uuid.UUID, base: str, exclude_id: uuid.UUID | None = None
) -> str:
    slug, n = base, 2
    while True:
        q = select(Business).where(Business.universe_id == universe_id, Business.slug == slug)
        if exclude_id:
            q = q.where(Business.id != exclude_id)
        if (await session.execute(q)).scalar_one_or_none() is None:
            return slug
        slug, n = f"{base}-{n}", n + 1


async def _sync_business_members(session: AsyncSession, business_id: uuid.UUID, members) -> None:
    await session.execute(
        BusinessMember.__table__.delete().where(BusinessMember.business_id == business_id)
    )
    for m in members:
        session.add(BusinessMember(business_id=business_id, member_id=m.member_id, role=m.role))


async def _sync_business_sets(
    session: AsyncSession, business_id: uuid.UUID, set_ids: list[uuid.UUID]
) -> None:
    await session.execute(
        BusinessSet.__table__.delete().where(BusinessSet.business_id == business_id)
    )
    for sid in set_ids:
        session.add(BusinessSet(business_id=business_id, set_id=sid))


async def _sync_business_sources(
    session: AsyncSession, business_id: uuid.UUID, source_ids: list[uuid.UUID]
) -> None:
    await session.execute(
        BusinessSource.__table__.delete().where(BusinessSource.business_id == business_id)
    )
    for sid in source_ids:
        session.add(BusinessSource(business_id=business_id, source_id=sid))


async def create_business(
    session: AsyncSession, data: BusinessCreate, actor_id: uuid.UUID
) -> Business:
    dump = data.model_dump(exclude={"members", "set_ids", "source_ids", "founded_at", "ended_at"})
    dump["founded_at"] = _fuzzy_to_dict(data.founded_at)
    dump["ended_at"] = _fuzzy_to_dict(data.ended_at)
    base = _slugify(data.name)
    dump["slug"] = await _unique_slug(session, data.universe_id, base)
    obj = Business(**dump, created_by_id=actor_id)
    session.add(obj)
    await session.flush()
    await _sync_business_members(session, obj.id, data.members)
    await _sync_business_sets(session, obj.id, data.set_ids)
    await _sync_business_sources(session, obj.id, data.source_ids)
    await session.commit()
    await session.refresh(obj)
    return obj


async def get_business(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> Business | None:
    result = await session.execute(
        select(Business).where(Business.id == id, Business.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def get_business_by_slug(
    session: AsyncSession, slug: str, universe_id: uuid.UUID
) -> Business | None:
    result = await session.execute(
        select(Business).where(Business.slug == slug, Business.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def list_businesses(
    session: AsyncSession,
    universe_id: uuid.UUID,
    offset: int = 0,
    limit: int = 50,
    business_type: str | None = None,
    status: str | None = None,
    municipality_id: uuid.UUID | None = None,
    set_id: uuid.UUID | None = None,
    member_id: uuid.UUID | None = None,
) -> tuple[list[Business], int]:
    stmt = select(Business).where(Business.universe_id == universe_id)
    if business_type is not None:
        stmt = stmt.where(Business.business_type == business_type)
    if status is not None:
        stmt = stmt.where(Business.status == status)
    if municipality_id is not None:
        stmt = stmt.where(Business.municipality_id == municipality_id)
    if set_id is not None:
        stmt = stmt.where(
            Business.id.in_(select(BusinessSet.business_id).where(BusinessSet.set_id == set_id))
        )
    if member_id is not None:
        stmt = stmt.where(
            Business.id.in_(
                select(BusinessMember.business_id).where(BusinessMember.member_id == member_id)
            )
        )

    count_result = await session.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_result.scalar_one()

    member_count_sq = (
        select(BusinessMember.business_id, func.count().label("member_count"))
        .group_by(BusinessMember.business_id)
        .subquery()
    )
    rows = await session.execute(
        stmt.add_columns(Municipality.name, func.coalesce(member_count_sq.c.member_count, 0))
        .outerjoin(Municipality, Municipality.id == Business.municipality_id)
        .outerjoin(member_count_sq, member_count_sq.c.business_id == Business.id)
        .offset(offset)
        .limit(limit)
    )
    items = []
    for obj, municipality_name, member_count in rows.all():
        object.__setattr__(obj, "municipality_name", municipality_name)
        object.__setattr__(obj, "member_count", member_count)
        items.append(obj)
    return items, total


async def update_business(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, data: BusinessUpdate
) -> Business | None:
    obj = await get_business(session, id, universe_id)
    if obj is None:
        return None
    dump = data.model_dump(
        exclude_unset=True, exclude={"members", "set_ids", "source_ids", "founded_at", "ended_at"}
    )
    fields_set = data.model_fields_set
    if "founded_at" in fields_set:
        dump["founded_at"] = _fuzzy_to_dict(data.founded_at)
    if "ended_at" in fields_set:
        dump["ended_at"] = _fuzzy_to_dict(data.ended_at)
    if "name" in dump:
        base = _slugify(dump["name"])
        dump["slug"] = await _unique_slug(session, universe_id, base, exclude_id=id)
    for k, v in dump.items():
        setattr(obj, k, v)
    obj.updated_at = datetime.now(UTC)
    session.add(obj)
    if data.members is not None:
        await _sync_business_members(session, obj.id, data.members)
    if data.set_ids is not None:
        await _sync_business_sets(session, obj.id, data.set_ids)
    if data.source_ids is not None:
        await _sync_business_sources(session, obj.id, data.source_ids)
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_business(session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID) -> bool:
    obj = await get_business(session, id, universe_id)
    if obj is None:
        return False
    await session.execute(BusinessMember.__table__.delete().where(BusinessMember.business_id == id))
    await session.execute(BusinessSet.__table__.delete().where(BusinessSet.business_id == id))
    await session.execute(BusinessSource.__table__.delete().where(BusinessSource.business_id == id))
    await session.delete(obj)
    await session.commit()
    return True


async def list_business_members(
    session: AsyncSession, business_id: uuid.UUID
) -> list[BusinessMemberOut]:
    rows = await session.execute(
        select(
            BusinessMember.member_id,
            BusinessMember.role,
            Member.slug,
            Member.nickname,
            Member.legal_name,
            Member.nickname_unknown,
        )
        .join(Member, Member.id == BusinessMember.member_id)
        .where(BusinessMember.business_id == business_id)
    )
    out = []
    for member_id, role, slug, nickname, legal_name, nickname_unknown in rows.all():
        display = legal_name if (nickname_unknown or not nickname) else nickname
        out.append(
            BusinessMemberOut(
                member_id=member_id, member_name=display or "Unknown", member_slug=slug, role=role
            )
        )
    return out


async def list_business_set_ids(session: AsyncSession, business_id: uuid.UUID) -> list[uuid.UUID]:
    result = await session.execute(
        select(BusinessSet.set_id).where(BusinessSet.business_id == business_id)
    )
    return result.scalars().all()


async def list_business_source_ids(
    session: AsyncSession, business_id: uuid.UUID
) -> list[uuid.UUID]:
    result = await session.execute(
        select(BusinessSource.source_id).where(BusinessSource.business_id == business_id)
    )
    return result.scalars().all()


async def search_businesses(
    session: AsyncSession, universe_id: uuid.UUID, q: str
) -> list[Business]:
    pattern = f"%{q}%"
    result = await session.execute(
        select(Business).where(
            Business.universe_id == universe_id,
            Business.name.ilike(pattern) | sa.cast(Business.aliases, sa.Text).ilike(pattern),
        )
    )
    return result.scalars().all()
