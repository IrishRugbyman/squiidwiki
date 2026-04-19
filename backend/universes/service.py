from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Universe, UniverseRole, UserUniverseAccess
from backend.universes.schemas import UniverseCreate, UniverseUpdate


async def create_universe(
    db: AsyncSession,
    payload: UniverseCreate,
    created_by_id: Optional[int] = None,
) -> Universe:
    universe = Universe(
        name=payload.name,
        slug=payload.slug,
        created_by_id=created_by_id,
    )
    db.add(universe)
    await db.flush()
    return universe


async def get_universe_by_slug(db: AsyncSession, slug: str) -> Optional[Universe]:
    result = await db.execute(
        select(Universe).where(Universe.slug == slug, Universe.deleted_at.is_(None))
    )
    return result.scalars().first()


async def get_universe_by_id(db: AsyncSession, universe_id: int) -> Optional[Universe]:
    result = await db.execute(
        select(Universe).where(Universe.id == universe_id, Universe.deleted_at.is_(None))
    )
    return result.scalars().first()


async def list_universes(db: AsyncSession) -> list[Universe]:
    result = await db.execute(
        select(Universe).where(Universe.deleted_at.is_(None)).order_by(Universe.name)
    )
    return list(result.scalars().all())


async def list_user_universes(db: AsyncSession, user_id: int) -> list[Universe]:
    result = await db.execute(
        select(Universe)
        .join(UserUniverseAccess, UserUniverseAccess.universe_id == Universe.id)
        .where(
            UserUniverseAccess.user_id == user_id,
            Universe.deleted_at.is_(None),
        )
        .order_by(Universe.name)
    )
    return list(result.scalars().all())


async def grant_access(
    db: AsyncSession,
    universe_id: int,
    user_id: int,
    role: UniverseRole,
) -> UserUniverseAccess:
    result = await db.execute(
        select(UserUniverseAccess).where(
            UserUniverseAccess.universe_id == universe_id,
            UserUniverseAccess.user_id == user_id,
        )
    )
    access = result.scalars().first()
    if access:
        access.role = role
    else:
        access = UserUniverseAccess(universe_id=universe_id, user_id=user_id, role=role)
        db.add(access)
    await db.flush()
    return access


async def soft_delete_universe(db: AsyncSession, universe: Universe) -> None:
    from datetime import datetime, timezone
    universe.deleted_at = datetime.now(timezone.utc)
    await db.flush()
