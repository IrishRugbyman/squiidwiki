import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.models.alliance import Alliance, AllianceMunicipality, AllianceSet
from app.schemas.alliance import AllianceCreate, AllianceUpdate


def _fuzzy_to_dict(fd) -> dict | None:
    if fd is None:
        return None
    return fd.model_dump()


def _slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-") or "alliance"


async def _unique_slug(
    session: AsyncSession, universe_id: uuid.UUID, base: str, exclude_id: uuid.UUID | None = None
) -> str:
    slug, n = base, 2
    while True:
        q = select(Alliance).where(Alliance.universe_id == universe_id, Alliance.slug == slug)
        if exclude_id:
            q = q.where(Alliance.id != exclude_id)
        if (await session.execute(q)).scalar_one_or_none() is None:
            return slug
        slug, n = f"{base}-{n}", n + 1


async def _sync_alliance_municipalities(
    session: AsyncSession, alliance_id: uuid.UUID, territory_ids: list[uuid.UUID]
) -> None:
    await session.execute(
        AllianceMunicipality.__table__.delete().where(
            AllianceMunicipality.alliance_id == alliance_id
        )
    )
    for mid in territory_ids:
        session.add(AllianceMunicipality(alliance_id=alliance_id, municipality_id=mid))


async def _sync_alliance_sets(
    session: AsyncSession, alliance_id: uuid.UUID, set_ids: list[uuid.UUID]
) -> None:
    await session.execute(
        AllianceSet.__table__.delete().where(AllianceSet.alliance_id == alliance_id)
    )
    for sid in set_ids:
        session.add(AllianceSet(alliance_id=alliance_id, set_id=sid))


async def create_alliance(
    session: AsyncSession, data: AllianceCreate, actor_id: uuid.UUID
) -> Alliance:
    dump = data.model_dump(exclude={"territory_ids", "set_ids"})
    dump["founded_at"] = _fuzzy_to_dict(data.founded_at)
    base = _slugify(data.name)
    dump["slug"] = await _unique_slug(session, data.universe_id, base)
    obj = Alliance(**dump, created_by_id=actor_id)
    session.add(obj)
    await session.flush()
    await _sync_alliance_municipalities(session, obj.id, data.territory_ids)
    await _sync_alliance_sets(session, obj.id, data.set_ids)
    await session.commit()
    await session.refresh(obj)
    return obj


async def get_alliance(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> Alliance | None:
    result = await session.execute(
        select(Alliance).where(Alliance.id == id, Alliance.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def get_alliance_by_slug(
    session: AsyncSession, slug: str, universe_id: uuid.UUID
) -> Alliance | None:
    result = await session.execute(
        select(Alliance).where(Alliance.slug == slug, Alliance.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def list_alliances(
    session: AsyncSession, universe_id: uuid.UUID, offset: int = 0, limit: int = 50
) -> tuple[list[Alliance], int]:
    count_result = await session.execute(
        select(func.count()).select_from(Alliance).where(Alliance.universe_id == universe_id)
    )
    total = count_result.scalar_one()
    result = await session.execute(
        select(Alliance).where(Alliance.universe_id == universe_id).offset(offset).limit(limit)
    )
    return result.scalars().all(), total


async def update_alliance(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, data: AllianceUpdate
) -> Alliance | None:
    obj = await get_alliance(session, id, universe_id)
    if obj is None:
        return None
    dump = data.model_dump(exclude_unset=True, exclude={"territory_ids", "set_ids"})
    if "founded_at" in dump:
        dump["founded_at"] = _fuzzy_to_dict(data.founded_at)
    if "name" in dump:
        base = _slugify(dump["name"])
        dump["slug"] = await _unique_slug(session, universe_id, base, exclude_id=id)
    for k, v in dump.items():
        setattr(obj, k, v)
    session.add(obj)
    if data.territory_ids is not None:
        await _sync_alliance_municipalities(session, obj.id, data.territory_ids)
    if data.set_ids is not None:
        await _sync_alliance_sets(session, obj.id, data.set_ids)
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_alliance(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> bool:
    obj = await get_alliance(session, id, universe_id)
    if obj is None:
        return False
    await session.delete(obj)
    await session.commit()
    return True


async def list_alliance_territory_ids(
    session: AsyncSession, alliance_id: uuid.UUID
) -> list[uuid.UUID]:
    result = await session.execute(
        select(AllianceMunicipality.municipality_id).where(
            AllianceMunicipality.alliance_id == alliance_id
        )
    )
    return result.scalars().all()


async def list_alliance_set_ids(
    session: AsyncSession, alliance_id: uuid.UUID
) -> list[uuid.UUID]:
    result = await session.execute(
        select(AllianceSet.set_id).where(AllianceSet.alliance_id == alliance_id)
    )
    return result.scalars().all()


async def search_alliances(
    session: AsyncSession, universe_id: uuid.UUID, q: str
) -> list[Alliance]:
    result = await session.execute(
        select(Alliance).where(
            Alliance.universe_id == universe_id,
            Alliance.name.ilike(f"%{q}%"),
        )
    )
    return result.scalars().all()
