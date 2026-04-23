import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.municipality import Municipality
from app.schemas.municipality import MunicipalityCreate, MunicipalityUpdate


async def create_municipality(
    session: AsyncSession, data: MunicipalityCreate, actor_id: uuid.UUID
) -> Municipality:
    obj = Municipality(**data.model_dump())
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def get_municipality(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> dict | None:
    row = (await session.execute(text("""
        SELECT
            m.id, m.name, m.parent_id, m.universe_id, m.geometry,
            COUNT(DISTINCT i.id)::int AS incident_count,
            COUNT(DISTINCT c.id)::int AS child_count
        FROM municipality m
        LEFT JOIN incident i ON i.municipality_id = m.id
        LEFT JOIN municipality c ON c.parent_id = m.id
        WHERE m.id = :id AND m.universe_id = :uid
        GROUP BY m.id
    """), {"id": str(id), "uid": str(universe_id)})).mappings().one_or_none()
    return dict(row) if row else None


async def list_municipalities(
    session: AsyncSession, universe_id: uuid.UUID, offset: int = 0, limit: int = 100
) -> tuple[list, int]:
    rows = (await session.execute(text("""
        SELECT
            m.id,
            m.name,
            m.parent_id,
            m.universe_id,
            (m.geometry IS NOT NULL) AS has_geometry,
            COUNT(DISTINCT i.id)::int AS incident_count,
            COUNT(DISTINCT c.id)::int AS child_count
        FROM municipality m
        LEFT JOIN incident i ON i.municipality_id = m.id
        LEFT JOIN municipality c ON c.parent_id = m.id
        WHERE m.universe_id = :uid
        GROUP BY m.id
        ORDER BY m.name
        LIMIT :lim OFFSET :off
    """), {"uid": str(universe_id), "lim": limit, "off": offset})).mappings().all()

    total_row = (await session.execute(text(
        "SELECT count(*) FROM municipality WHERE universe_id = :uid"
    ), {"uid": str(universe_id)})).scalar_one()

    items = [
        {
            "id": r["id"],
            "name": r["name"],
            "parent_id": r["parent_id"],
            "universe_id": r["universe_id"],
            "has_geometry": r["has_geometry"],
            "incident_count": r["incident_count"],
            "child_count": r["child_count"],
        }
        for r in rows
    ]
    return items, total_row


async def get_municipality_geojson(
    session: AsyncSession, universe_id: uuid.UUID
) -> dict:
    """Return a GeoJSON FeatureCollection for all municipalities that have geometry."""
    rows = (await session.execute(text("""
        SELECT
            m.id,
            m.name,
            m.geometry,
            COUNT(DISTINCT i.id)::int AS incident_count
        FROM municipality m
        LEFT JOIN incident i ON i.municipality_id = m.id
        WHERE m.universe_id = :uid AND m.geometry IS NOT NULL
        GROUP BY m.id
        ORDER BY m.name
    """), {"uid": str(universe_id)})).mappings().all()

    features = [
        {
            "type": "Feature",
            "id": str(r["id"]),
            "geometry": r["geometry"],
            "properties": {
                "id": str(r["id"]),
                "name": r["name"],
                "incident_count": r["incident_count"],
            },
        }
        for r in rows
    ]
    return {"type": "FeatureCollection", "features": features}


async def update_municipality(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, data: MunicipalityUpdate
) -> dict | None:
    result = await session.execute(
        select(Municipality).where(
            Municipality.id == id, Municipality.universe_id == universe_id
        )
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    session.add(obj)
    await session.commit()
    return await get_municipality(session, id, universe_id)


async def delete_municipality(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> bool:
    result = await session.execute(
        select(Municipality).where(
            Municipality.id == id, Municipality.universe_id == universe_id
        )
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        return False
    await session.delete(obj)
    await session.commit()
    return True


async def search_municipalities(
    session: AsyncSession, universe_id: uuid.UUID, q: str
) -> list[dict]:
    rows = (await session.execute(text("""
        SELECT
            m.id, m.name, m.parent_id, m.universe_id,
            (m.geometry IS NOT NULL) AS has_geometry,
            COUNT(DISTINCT i.id)::int AS incident_count,
            COUNT(DISTINCT c.id)::int AS child_count
        FROM municipality m
        LEFT JOIN incident i ON i.municipality_id = m.id
        LEFT JOIN municipality c ON c.parent_id = m.id
        WHERE m.universe_id = :uid AND m.name ILIKE :q
        GROUP BY m.id
        ORDER BY m.name
    """), {"uid": str(universe_id), "q": f"%{q}%"})).mappings().all()
    return [dict(r) for r in rows]
