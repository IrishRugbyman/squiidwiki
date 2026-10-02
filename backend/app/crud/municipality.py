import uuid

from shapely.errors import ShapelyError
from shapely.geometry import shape
from sqlalchemy import delete, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import MunicipalityKind
from app.crud.media import delete_media
from app.models.media import Media
from app.models.municipality import Municipality, MunicipalityOverlap, MunicipalitySource
from app.models.source import Source
from app.schemas.municipality import MunicipalityCreate, MunicipalityUpdate

# A neighborhood share below this is where the city's neighborhood map and the
# ZIP map disagree at an edge (Brightmoor's 0.2% outside 48223), not an overlap.
OVERLAP_MIN_SHARE = 0.02


def _polygon(geometry):
    """A valid shapely geometry, or None for a missing or unusable one."""
    if not geometry or geometry == "null":
        return None
    try:
        g = shape(geometry)
        g = g if g.is_valid else g.buffer(0)
    except (ShapelyError, KeyError, TypeError, ValueError):
        return None
    return g if not g.is_empty and g.area > 0 else None


async def sync_overlaps(session: AsyncSession, parent_id: uuid.UUID | None) -> None:
    """Recompute which districts each neighborhood of one city lies in.

    The whole city at once rather than one row: a city holds a few dozen
    sub-areas, and recomputing all of them is what keeps a moved district from
    leaving stale rows on neighborhoods nobody touched. Shares are ratios of
    areas in degrees, which the latitude scaling cancels out of at city scale.
    Flushes; the caller commits.
    """
    if parent_id is None:
        return
    children = (
        (await session.execute(select(Municipality).where(Municipality.parent_id == parent_id)))
        .scalars()
        .all()
    )
    await session.execute(
        delete(MunicipalityOverlap).where(
            or_(
                MunicipalityOverlap.neighborhood_id.in_([c.id for c in children]),
                MunicipalityOverlap.district_id.in_([c.id for c in children]),
            )
        )
    )
    shapes = {c.id: _polygon(c.geometry) for c in children}
    districts = [c for c in children if c.kind == MunicipalityKind.DISTRICT and shapes[c.id]]
    for hood in children:
        hg = shapes[hood.id]
        if hood.kind != MunicipalityKind.NEIGHBORHOOD or hg is None:
            continue
        for d in districts:
            dg = shapes[d.id]
            if not hg.intersects(dg):
                continue
            inter = hg.intersection(dg).area
            if inter / hg.area < OVERLAP_MIN_SHARE:
                continue
            session.add(
                MunicipalityOverlap(
                    neighborhood_id=hood.id,
                    district_id=d.id,
                    share_of_neighborhood=min(1.0, inter / hg.area),
                    share_of_district=min(1.0, inter / dg.area),
                )
            )
    await session.flush()


class MunicipalityError(ValueError):
    """A write the schema accepts but the data cannot hold."""


def _resolve_kind(
    parent_id: uuid.UUID | None,
    requested: MunicipalityKind | None,
    current: MunicipalityKind | None = None,
) -> MunicipalityKind:
    """The kind a row takes, given its parent: CITY exactly at the top level.

    Without an explicit kind, a row keeps the one it has when that still fits
    its parent, and otherwise becomes a CITY or a DISTRICT. This mirrors the
    ck_municipality_kind_parent CHECK, which would refuse the write anyway, so
    the caller gets a message instead of an IntegrityError.
    """
    if parent_id is None:
        if requested not in (None, MunicipalityKind.CITY):
            raise MunicipalityError(f"A {requested.value.lower()} needs a parent municipality")
        return MunicipalityKind.CITY
    if requested == MunicipalityKind.CITY:
        raise MunicipalityError("A city cannot have a parent municipality")
    if requested is not None:
        return requested
    if current not in (None, MunicipalityKind.CITY):
        return current
    return MunicipalityKind.DISTRICT


async def _check_parent(
    session: AsyncSession, universe_id: uuid.UUID, id: uuid.UUID | None, parent_id: uuid.UUID
) -> None:
    parent = (
        await session.execute(
            select(Municipality).where(
                Municipality.id == parent_id, Municipality.universe_id == universe_id
            )
        )
    ).scalar_one_or_none()
    if parent is None:
        raise MunicipalityError("Parent municipality not found in this universe")
    if parent.id == id:
        raise MunicipalityError("A municipality cannot be its own parent")
    # One level only: the maps, the rollups and the breadcrumbs all assume it.
    if parent.parent_id is not None:
        raise MunicipalityError(f"{parent.name} is itself inside a city; pick the city")


async def _set_sources(
    session: AsyncSession,
    municipality_id: uuid.UUID,
    universe_id: uuid.UUID,
    source_ids: list[uuid.UUID],
) -> None:
    wanted = list(dict.fromkeys(source_ids))
    if wanted:
        found = set(
            (
                await session.execute(
                    select(Source.id).where(
                        Source.id.in_(wanted), Source.universe_id == universe_id
                    )
                )
            )
            .scalars()
            .all()
        )
        missing = [str(s) for s in wanted if s not in found]
        if missing:
            raise MunicipalityError(f"Sources not found in this universe: {', '.join(missing)}")
    await session.execute(
        delete(MunicipalitySource).where(MunicipalitySource.municipality_id == municipality_id)
    )
    for sid in wanted:
        session.add(MunicipalitySource(municipality_id=municipality_id, source_id=sid))


async def create_municipality(
    session: AsyncSession, data: MunicipalityCreate, actor_id: uuid.UUID
) -> Municipality:
    fields = data.model_dump(exclude={"source_ids", "kind"})
    if data.parent_id is not None:
        await _check_parent(session, data.universe_id, None, data.parent_id)
    obj = Municipality(**fields, kind=_resolve_kind(data.parent_id, data.kind))
    session.add(obj)
    await session.flush()
    if data.source_ids:
        await _set_sources(session, obj.id, obj.universe_id, data.source_ids)
    await sync_overlaps(session, obj.parent_id)
    await session.commit()
    await session.refresh(obj)
    return obj


async def get_municipality(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> dict | None:
    row = (
        (
            await session.execute(
                text("""
        SELECT
            m.id, m.name, m.parent_id, m.universe_id, m.geometry, m.kind,
            COALESCE(m.aliases, '[]'::jsonb) AS aliases, m.region, m.description,
            m.population, m.population_year, m.population_source,
            (m.geometry IS NOT NULL AND m.geometry != 'null'::jsonb) AS has_geometry,
            COUNT(DISTINCT i.id)::int AS incident_count,
            COUNT(DISTINCT c.id)::int AS child_count
        FROM municipality m
        LEFT JOIN incident i ON i.municipality_id = m.id
        LEFT JOIN municipality c ON c.parent_id = m.id
        WHERE m.id = :id AND m.universe_id = :uid
        GROUP BY m.id
    """),
                {"id": str(id), "uid": str(universe_id)},
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        return None
    sources = (
        (
            await session.execute(
                select(Source)
                .join(MunicipalitySource, MunicipalitySource.source_id == Source.id)
                .where(MunicipalitySource.municipality_id == id)
                .order_by(Source.title)
            )
        )
        .scalars()
        .all()
    )
    if row["kind"] == MunicipalityKind.NEIGHBORHOOD.value:
        mine, theirs = MunicipalityOverlap.neighborhood_id, MunicipalityOverlap.district_id
    else:
        mine, theirs = MunicipalityOverlap.district_id, MunicipalityOverlap.neighborhood_id
    overlaps = [
        {
            "id": m.id,
            "name": m.name,
            "kind": m.kind,
            "share_of_neighborhood": o.share_of_neighborhood,
            "share_of_district": o.share_of_district,
        }
        for o, m in (
            await session.execute(
                select(MunicipalityOverlap, Municipality)
                .join(Municipality, Municipality.id == theirs)
                .where(mine == id)
                .order_by(MunicipalityOverlap.share_of_neighborhood.desc(), Municipality.name)
            )
        ).all()
    ]
    return {**row, "sources": sources, "overlaps": overlaps}


async def list_municipalities(
    session: AsyncSession, universe_id: uuid.UUID, offset: int = 0, limit: int = 100
) -> tuple[list, int]:
    # Counts come from correlated subqueries rather than one GROUP BY over
    # joined incidents and children, which multiplied rows between the two.
    # total_incident_count adds a city's sub-districts to its own: incidents
    # are usually filed under the district, so the city's own count alone
    # read Detroit as 23 incidents when it held 42.
    rows = (
        (
            await session.execute(
                text("""
        SELECT
            m.id,
            m.name,
            m.parent_id,
            m.universe_id,
            m.kind,
            COALESCE(m.aliases, '[]'::jsonb) AS aliases,
            m.region,
            m.population,
            m.population_year,
            (m.geometry IS NOT NULL AND m.geometry != 'null'::jsonb) AS has_geometry,
            (SELECT count(*) FROM incident i WHERE i.municipality_id = m.id)::int
                AS incident_count,
            (SELECT count(*) FROM incident i
               WHERE i.municipality_id = m.id
                  OR i.municipality_id IN (SELECT c.id FROM municipality c WHERE c.parent_id = m.id)
            )::int AS total_incident_count,
            (SELECT count(*) FROM municipality c WHERE c.parent_id = m.id)::int AS child_count,
            -- A set belongs to a city through its anchor column and to a
            -- district through the territory table.
            (SELECT count(DISTINCT s.id) FROM sets s
               LEFT JOIN set_municipality sm ON sm.set_id = s.id
               WHERE NOT s.is_reserved
                 AND (s.municipality_id = m.id OR sm.municipality_id = m.id)
            )::int AS set_count
        FROM municipality m
        WHERE m.universe_id = :uid
        ORDER BY m.name, m.id
        LIMIT :lim OFFSET :off
    """),
                {"uid": str(universe_id), "lim": limit, "off": offset},
            )
        )
        .mappings()
        .all()
    )

    total_row = (
        await session.execute(
            text("SELECT count(*) FROM municipality WHERE universe_id = :uid"),
            {"uid": str(universe_id)},
        )
    ).scalar_one()

    items = [
        {
            "id": r["id"],
            "name": r["name"],
            "parent_id": r["parent_id"],
            "universe_id": r["universe_id"],
            "kind": r["kind"],
            "aliases": r["aliases"],
            "region": r["region"],
            "population": r["population"],
            "population_year": r["population_year"],
            "has_geometry": r["has_geometry"],
            "incident_count": r["incident_count"],
            "total_incident_count": r["total_incident_count"],
            "child_count": r["child_count"],
            "set_count": r["set_count"],
        }
        for r in rows
    ]
    return items, total_row


async def get_municipality_geojson(
    session: AsyncSession,
    universe_id: uuid.UUID,
    *,
    parent_filter: str | uuid.UUID | None = None,
    kind: MunicipalityKind | None = None,
) -> dict:
    """Return a GeoJSON FeatureCollection for municipalities that have geometry.

    parent_filter:
      - None      → all municipalities (legacy behavior)
      - "top"     → only top-level (parent_id IS NULL)
      - UUID      → only children of that municipality

    kind narrows the children of a UUID filter to one kind, since districts
    partition a city and neighborhoods overlap them: drawn together, the
    choropleth stacks one polygon over another.

    Each feature carries `incident_count` and `set_count` on its properties.
    For top-level rows the counts are rolled up to include any descendant —
    so the main-map choropleth reflects activity in sub-districts even though
    those polygons are hidden.
    """
    params: dict = {"uid": str(universe_id)}

    # Set count counts a set as "in" municipality m when EITHER:
    #   (a) sets.municipality_id matches (the new primary anchor), or
    #   (b) the set has a set_municipality row pointing here (sub-district claim)
    # Top-level rollup also includes any descendant of m on both legs.
    if parent_filter == "top":
        sql = """
            SELECT
                m.id,
                m.name,
                m.parent_id,
                m.kind,
                m.geometry,
                COALESCE((
                    SELECT COUNT(DISTINCT i.id)::int
                    FROM incident i
                    LEFT JOIN municipality c ON c.id = i.municipality_id
                    WHERE i.universe_id = :uid
                      AND (i.municipality_id = m.id OR c.parent_id = m.id)
                ), 0) AS incident_count,
                COALESCE((
                    SELECT COUNT(DISTINCT s.id)::int
                    FROM sets s
                    LEFT JOIN municipality smu ON smu.id = s.municipality_id
                    LEFT JOIN set_municipality sm ON sm.set_id = s.id
                    LEFT JOIN municipality cm ON cm.id = sm.municipality_id
                    WHERE s.universe_id = :uid
                      AND (
                        s.municipality_id = m.id
                        OR smu.parent_id = m.id
                        OR sm.municipality_id = m.id
                        OR cm.parent_id = m.id
                      )
                ), 0) AS set_count
            FROM municipality m
            WHERE m.universe_id = :uid
              AND m.parent_id IS NULL
              AND m.geometry IS NOT NULL
              AND m.geometry != 'null'::jsonb
            ORDER BY m.name
        """
    elif parent_filter is not None:
        params["pid"] = str(parent_filter)
        params["kind"] = kind.value if kind else None
        sql = """
            SELECT
                m.id,
                m.name,
                m.parent_id,
                m.kind,
                m.geometry,
                COUNT(DISTINCT i.id)::int AS incident_count,
                COALESCE((
                    SELECT COUNT(DISTINCT s.id)::int
                    FROM sets s
                    LEFT JOIN set_municipality sm
                      ON sm.set_id = s.id AND sm.municipality_id = m.id
                    WHERE s.universe_id = :uid
                      AND (s.municipality_id = m.id OR sm.set_id IS NOT NULL)
                ), 0) AS set_count
            FROM municipality m
            LEFT JOIN incident i ON i.municipality_id = m.id
            WHERE m.universe_id = :uid
              AND m.parent_id = :pid
              AND (CAST(:kind AS varchar) IS NULL OR m.kind = :kind)
              AND m.geometry IS NOT NULL
              AND m.geometry != 'null'::jsonb
            GROUP BY m.id
            ORDER BY m.name
        """
    else:
        sql = """
            SELECT
                m.id,
                m.name,
                m.parent_id,
                m.kind,
                m.geometry,
                COUNT(DISTINCT i.id)::int AS incident_count,
                COALESCE((
                    SELECT COUNT(DISTINCT s.id)::int
                    FROM sets s
                    LEFT JOIN set_municipality sm
                      ON sm.set_id = s.id AND sm.municipality_id = m.id
                    WHERE s.universe_id = :uid
                      AND (s.municipality_id = m.id OR sm.set_id IS NOT NULL)
                ), 0) AS set_count
            FROM municipality m
            LEFT JOIN incident i ON i.municipality_id = m.id
            WHERE m.universe_id = :uid
              AND m.geometry IS NOT NULL
              AND m.geometry != 'null'::jsonb
            GROUP BY m.id
            ORDER BY m.name
        """

    rows = (await session.execute(text(sql), params)).mappings().all()

    features = [
        {
            "type": "Feature",
            "id": str(r["id"]),
            "geometry": r["geometry"],
            "properties": {
                "id": str(r["id"]),
                "name": r["name"],
                "parent_id": str(r["parent_id"]) if r["parent_id"] else None,
                "kind": r["kind"],
                "incident_count": r["incident_count"],
                "set_count": r["set_count"],
            },
        }
        for r in rows
    ]
    return {"type": "FeatureCollection", "features": features}


async def update_municipality(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, data: MunicipalityUpdate
) -> dict | None:
    result = await session.execute(
        select(Municipality).where(Municipality.id == id, Municipality.universe_id == universe_id)
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        return None
    dump = data.model_dump(exclude_unset=True)
    source_ids = dump.pop("source_ids", None)
    requested_kind = dump.pop("kind", None)
    if "parent_id" in dump or requested_kind is not None:
        parent_id = dump.get("parent_id", obj.parent_id)
        if parent_id is not None and parent_id != obj.parent_id:
            await _check_parent(session, universe_id, obj.id, parent_id)
        if parent_id is not None and obj.parent_id is None:
            children = (
                await session.execute(
                    select(Municipality.id).where(Municipality.parent_id == obj.id).limit(1)
                )
            ).first()
            if children is not None:
                raise MunicipalityError(f"{obj.name} has sub-districts; it has to stay a city")
        obj.kind = _resolve_kind(parent_id, requested_kind, obj.kind)
    old_parent, old_kind, old_geometry = obj.parent_id, obj.kind, obj.geometry
    for k, v in dump.items():
        setattr(obj, k, v)
    session.add(obj)
    if source_ids is not None:
        await _set_sources(session, obj.id, universe_id, source_ids)
    if (obj.parent_id, obj.kind, obj.geometry) != (old_parent, old_kind, old_geometry):
        await session.flush()
        for parent in {old_parent, obj.parent_id}:
            await sync_overlaps(session, parent)
    await session.commit()
    return await get_municipality(session, id, universe_id)


async def delete_municipality(session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID) -> bool:
    result = await session.execute(
        select(Municipality).where(Municipality.id == id, Municipality.universe_id == universe_id)
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        return False
    # Through the media CRUD rather than the FK cascade, so the R2 objects go too.
    photos = (await session.execute(select(Media).where(Media.municipality_id == id))).scalars()
    for photo in photos.all():
        await delete_media(session, photo.id, photo.universe_id)
    await session.delete(obj)
    await session.commit()
    return True


async def search_municipalities(
    session: AsyncSession, universe_id: uuid.UUID, q: str
) -> list[dict]:
    rows = (
        (
            await session.execute(
                text("""
        SELECT
            m.id, m.name, m.parent_id, m.universe_id, m.kind,
            COALESCE(m.aliases, '[]'::jsonb) AS aliases, m.region,
            (m.geometry IS NOT NULL AND m.geometry != 'null'::jsonb) AS has_geometry,
            COUNT(DISTINCT i.id)::int AS incident_count,
            COUNT(DISTINCT c.id)::int AS child_count
        FROM municipality m
        LEFT JOIN incident i ON i.municipality_id = m.id
        LEFT JOIN municipality c ON c.parent_id = m.id
        WHERE m.universe_id = :uid
          AND (m.name ILIKE :q
               OR EXISTS (SELECT 1 FROM jsonb_array_elements_text(m.aliases) a
                          WHERE a ILIKE :q))
        GROUP BY m.id
        ORDER BY (m.name ILIKE :q) DESC, m.name
    """),
                {"uid": str(universe_id), "q": f"%{q}%"},
            )
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]
