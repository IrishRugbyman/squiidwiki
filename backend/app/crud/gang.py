import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core.slug import slugify
from app.models.alliance import Alliance
from app.models.gang import Gang
from app.models.gang_set import GangSet
from app.models.member import Member
from app.schemas.gang import GangCreate, GangUpdate


def _slugify(s: str) -> str:
    return slugify(s, "gang")


async def _unique_slug(
    session: AsyncSession, universe_id: uuid.UUID, base: str, exclude_id: uuid.UUID | None = None
) -> str:
    slug, n = base, 2
    while True:
        q = select(Gang).where(Gang.universe_id == universe_id, Gang.slug == slug)
        if exclude_id:
            q = q.where(Gang.id != exclude_id)
        if (await session.execute(q)).scalar_one_or_none() is None:
            return slug
        slug, n = f"{base}-{n}", n + 1


async def create_gang(session: AsyncSession, data: GangCreate, actor_id: uuid.UUID) -> Gang:
    base = _slugify(data.name)
    slug = await _unique_slug(session, data.universe_id, base)
    obj = Gang(
        universe_id=data.universe_id,
        name=data.name,
        aliases=data.aliases,
        description=data.description,
        slug=slug,
        created_by_id=actor_id,
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def get_gang(session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID) -> Gang | None:
    result = await session.execute(
        select(Gang).where(Gang.id == id, Gang.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def get_gang_by_slug(session: AsyncSession, slug: str, universe_id: uuid.UUID) -> Gang | None:
    result = await session.execute(
        select(Gang).where(Gang.slug == slug, Gang.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def list_gangs(
    session: AsyncSession, universe_id: uuid.UUID, offset: int = 0, limit: int = 200
) -> tuple[list[Gang], int]:
    count_result = await session.execute(
        select(func.count()).select_from(Gang).where(Gang.universe_id == universe_id)
    )
    total = count_result.scalar_one()
    result = await session.execute(
        select(Gang)
        .where(Gang.universe_id == universe_id)
        .order_by(Gang.name)
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all(), total


async def update_gang(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, data: GangUpdate
) -> Gang | None:
    obj = await get_gang(session, id, universe_id)
    if obj is None:
        return None
    dump = data.model_dump(exclude_unset=True)
    if "name" in dump:
        base = _slugify(dump["name"])
        dump["slug"] = await _unique_slug(session, universe_id, base, exclude_id=id)
    for k, v in dump.items():
        setattr(obj, k, v)
    obj.updated_at = datetime.now(UTC)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_gang(session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID) -> bool:
    obj = await get_gang(session, id, universe_id)
    if obj is None:
        return False
    # Detach references (FK is ON DELETE SET NULL, but we explicitly clear so
    # audit listeners observe the change).
    await session.execute(
        GangSet.__table__.update().where(GangSet.gang_id == id).values(gang_id=None)
    )
    await session.execute(
        Alliance.__table__.update().where(Alliance.gang_id == id).values(gang_id=None)
    )
    await session.execute(
        Member.__table__.update().where(Member.gang_id == id).values(gang_id=None)
    )
    await session.delete(obj)
    await session.commit()
    return True


async def gang_usage_counts(session: AsyncSession, id: uuid.UUID) -> dict[str, int]:
    sets_count = (
        await session.execute(
            select(func.count()).select_from(GangSet).where(GangSet.gang_id == id)
        )
    ).scalar_one()
    alliances_count = (
        await session.execute(
            select(func.count()).select_from(Alliance).where(Alliance.gang_id == id)
        )
    ).scalar_one()
    members_count = (
        await session.execute(select(func.count()).select_from(Member).where(Member.gang_id == id))
    ).scalar_one()
    return {"sets": sets_count, "alliances": alliances_count, "members": members_count}
