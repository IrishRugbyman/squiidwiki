import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.models.business import BusinessSource
from app.models.gang_set import SetSource
from app.models.incident import IncidentSource
from app.models.member import MemberAlias, MemberCustodyId, MemberSource
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceUpdate


def _fuzzy_to_dict(fd) -> dict | None:
    if fd is None:
        return None
    return fd.model_dump()


async def create_source(session: AsyncSession, data: SourceCreate, actor_id: uuid.UUID) -> Source:
    dump = data.model_dump()
    dump["published_at"] = _fuzzy_to_dict(data.published_at)
    obj = Source(**dump, created_by_id=actor_id)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def get_source(session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID) -> Source | None:
    result = await session.execute(
        select(Source).where(Source.id == id, Source.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def list_sources(
    session: AsyncSession, universe_id: uuid.UUID, offset: int = 0, limit: int = 50
) -> tuple[list[Source], int]:
    count_result = await session.execute(
        select(func.count()).select_from(Source).where(Source.universe_id == universe_id)
    )
    total = count_result.scalar_one()
    # Newest first, with a tiebreak: unordered offset pages repeat and skip rows.
    result = await session.execute(
        select(Source)
        .where(Source.universe_id == universe_id)
        .order_by(Source.created_at.desc(), Source.id)
        .offset(offset)
        .limit(limit)
    )
    items = list(result.scalars().all())
    await attach_citation_counts(session, items)
    return items, total


async def attach_citation_counts(session: AsyncSession, items: list[Source]) -> None:
    """Attach how many incidents, members, sets, businesses, custody numbers and aliases cite each source."""
    if not items:
        return
    ids = [s.id for s in items]
    counts: dict[str, dict[uuid.UUID, int]] = {}
    for key, table in (
        ("incident_count", IncidentSource),
        ("member_count", MemberSource),
        ("set_count", SetSource),
        ("business_count", BusinessSource),
        # Custody numbers and aliases cite a source through a nullable column.
        ("custody_count", MemberCustodyId),
        ("alias_count", MemberAlias),
    ):
        rows = await session.execute(
            select(table.source_id, func.count())
            .where(table.source_id.in_(ids))
            .group_by(table.source_id)
        )
        counts[key] = dict(rows.all())
    for s in items:
        # SQLModel rejects unknown attributes through __setattr__; bypass it.
        for key, by_id in counts.items():
            object.__setattr__(s, key, int(by_id.get(s.id, 0)))


async def update_source(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, data: SourceUpdate
) -> Source | None:
    obj = await get_source(session, id, universe_id)
    if obj is None:
        return None
    dump = data.model_dump(exclude_unset=True)
    if "published_at" in dump:
        dump["published_at"] = _fuzzy_to_dict(data.published_at)
    for k, v in dump.items():
        setattr(obj, k, v)
    obj.updated_at = datetime.now(UTC)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_source(session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID) -> bool:
    obj = await get_source(session, id, universe_id)
    if obj is None:
        return False
    # Citations first: these foreign keys have no ON DELETE, so any source an
    # incident, member, set or custody number cited could not be deleted at all
    # (media, business and alias links cascade or null in the schema itself).
    for table in (IncidentSource, MemberSource, SetSource):
        await session.execute(sa.delete(table).where(table.source_id == id))
    await session.execute(
        sa.update(MemberCustodyId).where(MemberCustodyId.source_id == id).values(source_id=None)
    )
    await session.delete(obj)
    await session.commit()
    return True


async def search_sources(session: AsyncSession, universe_id: uuid.UUID, q: str) -> list[Source]:
    result = await session.execute(
        select(Source).where(
            Source.universe_id == universe_id,
            Source.title.ilike(f"%{q}%"),
        )
    )
    return result.scalars().all()
