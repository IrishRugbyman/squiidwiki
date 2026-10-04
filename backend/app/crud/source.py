"""Sources: the documents, pages and records the research cites.

A source is the document; a citation (app/crud/citation.py) is one record
citing it, with what it supports. Everything that lists, finds, counts,
merges or deletes sources is here.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core.enums import SourceReliability
from app.core.errors import ApiError
from app.core.sources import (
    classify_kind,
    domain_of,
    lookup_locator,
    lookup_system,
    normalise_url,
)
from app.models.alliance import Alliance
from app.models.business import Business
from app.models.citation import CITATION_TARGETS, TARGET_COLUMN, Citation
from app.models.court_case import CourtCase
from app.models.gang_set import GangSet
from app.models.incident import Incident
from app.models.media import Media
from app.models.member import Member, MemberAlias, MemberCustodyId
from app.models.municipality import Municipality
from app.models.source import Source
from app.models.universe import Universe
from app.schemas.source import SourceCounts, SourceCreate, SourceLookup, SourceUpdate

_RELIABILITY_RANK = {
    SourceReliability.HIGH: 0,
    SourceReliability.MEDIUM: 1,
    SourceReliability.LOW: 2,
    SourceReliability.UNVERIFIED: 3,
}


def _fuzzy_to_dict(fd) -> dict | None:
    if fd is None:
        return None
    return fd.model_dump()


def _derived(url: str) -> dict[str, Any]:
    system = lookup_system(url)
    return {
        "url_norm": normalise_url(url),
        "lookup_system": system.value if system else None,
    }


# --- create / read / update --------------------------------------------------


async def create_source(session: AsyncSession, data: SourceCreate, actor_id: uuid.UUID) -> Source:
    """Insert a source. No duplicate check here: the router does that, so the
    research tree's seed scripts, which call this directly, behave as before."""
    dump = data.model_dump(exclude={"allow_duplicate", "kind"})
    dump["published_at"] = _fuzzy_to_dict(data.published_at)
    dump.update(_derived(data.url))
    dump["kind"] = (data.kind or classify_kind(data.url)).value
    obj = Source(**dump, created_by_id=actor_id)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def find_by_url(session: AsyncSession, universe_id: uuid.UUID, url: str) -> list[Source]:
    rows = await session.execute(
        select(Source)
        .where(Source.universe_id == universe_id, Source.url_norm == normalise_url(url))
        .order_by(Source.created_at)
    )
    return list(rows.scalars().all())


async def lookup_source(
    session: AsyncSession, universe_id: uuid.UUID, system: str
) -> Source | None:
    return (
        await session.execute(
            select(Source).where(Source.universe_id == universe_id, Source.lookup_system == system)
        )
    ).scalar_one_or_none()


async def check_new_url(
    session: AsyncSession, universe_id: uuid.UUID, url: str, allow_duplicate: bool
) -> None:
    """Refuse a URL the universe already holds, with what to cite instead."""
    system = lookup_system(url)
    if system:
        canonical = await lookup_source(session, universe_id, system.value)
        if canonical is not None:
            raise ApiError(
                409,
                "lookup_source",
                f"{canonical.title} is already a source: cite it with the record "
                "number as the locator rather than adding another.",
                existing_id=canonical.id,
                suggested_locator=lookup_locator(url),
            )
    if allow_duplicate:
        return
    same = await find_by_url(session, universe_id, url)
    if same:
        raise ApiError(
            409,
            "duplicate_url",
            "A source with this URL is already on file.",
            existing_id=same[0].id,
            existing_title=same[0].title,
        )


async def get_source(session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID) -> Source | None:
    result = await session.execute(
        select(Source).where(Source.id == id, Source.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def update_source(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, data: SourceUpdate
) -> Source | None:
    obj = await get_source(session, id, universe_id)
    if obj is None:
        return None
    dump = data.model_dump(exclude_unset=True)
    if "published_at" in dump:
        dump["published_at"] = _fuzzy_to_dict(data.published_at)
    new_url = dump.get("url")
    if new_url and new_url != obj.url:
        dump.update(_derived(new_url))
        # A kind set by hand survives a URL edit; one the URL implied follows it.
        if "kind" not in dump and obj.kind == classify_kind(obj.url).value:
            dump["kind"] = classify_kind(new_url).value
    if dump.get("kind") is not None:
        dump["kind"] = getattr(dump["kind"], "value", dump["kind"])
    for k, v in dump.items():
        setattr(obj, k, v)
    obj.updated_at = datetime.now(UTC)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def bulk_update(
    session: AsyncSession,
    universe_id: uuid.UUID,
    ids: list[uuid.UUID],
    reliability: SourceReliability | None,
    kind: str | None,
) -> int:
    rows = (
        (
            await session.execute(
                select(Source).where(Source.id.in_(ids), Source.universe_id == universe_id)
            )
        )
        .scalars()
        .all()
    )
    now = datetime.now(UTC)
    for s in rows:
        if reliability is not None:
            s.reliability = reliability
        if kind is not None:
            s.kind = kind
        s.updated_at = now
        session.add(s)
    await session.commit()
    return len(rows)


# --- counts -------------------------------------------------------------------


async def counts_for(session: AsyncSession, ids: list[uuid.UUID]) -> dict[uuid.UUID, SourceCounts]:
    """Per source: citations by record type, plus custody numbers, aliases, photos."""
    if not ids:
        return {}
    out = {i: SourceCounts() for i in ids}
    cols = [
        func.count().filter(getattr(Citation, column).is_not(None)).label(entity)
        for entity, column, _ in CITATION_TARGETS
    ]
    rows = await session.execute(
        select(Citation.source_id, *cols)
        .where(Citation.source_id.in_(ids))
        .group_by(Citation.source_id)
    )
    for row in rows.mappings():
        for entity, _, _ in CITATION_TARGETS:
            setattr(out[row["source_id"]], entity, int(row[entity]))
    for key, model in (("custody_id", MemberCustodyId), ("alias", MemberAlias), ("media", Media)):
        rows = await session.execute(
            select(model.source_id, func.count())
            .where(model.source_id.in_(ids))
            .group_by(model.source_id)
        )
        for sid, n in rows.all():
            setattr(out[sid], key, int(n))
    return out


async def attach_counts(session: AsyncSession, items: list[Source]) -> None:
    counts = await counts_for(session, [s.id for s in items])
    for s in items:
        # SQLModel rejects unknown attributes through __setattr__; bypass it.
        object.__setattr__(s, "counts", counts.get(s.id, SourceCounts()))


# --- listing and search -----------------------------------------------------------


def _cited_expr():
    """How many citations, custody numbers, aliases and photos point at a source."""
    return (
        select(func.count()).select_from(Citation).where(Citation.source_id == Source.id)
    ).scalar_subquery()


def _uncited_clause():
    def none_of(model):
        return ~sa.exists().where(model.source_id == Source.id)

    return sa.and_(
        none_of(Citation), none_of(MemberCustodyId), none_of(MemberAlias), none_of(Media)
    )


def _text_clause(q: str):
    pattern = f"%{q}%"
    return sa.or_(
        Source.title.ilike(pattern),
        Source.publication.ilike(pattern),
        Source.url.ilike(pattern),
        Source.notes.ilike(pattern),
    )


def _rank_expr(q: str):
    return func.greatest(
        func.similarity(Source.title, q),
        func.similarity(func.coalesce(Source.publication, ""), q),
        func.similarity(Source.url, q),
    )


async def list_sources(
    session: AsyncSession,
    universe_id: uuid.UUID,
    *,
    q: str | None = None,
    kind: str | None = None,
    reliability: SourceReliability | None = None,
    publication: str | None = None,
    uncited: bool = False,
    sort: str = "added",
    order: str = "desc",
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[Source], int, dict[str, dict[str, int]]]:
    """A page of sources, the total, and facet counts.

    Each facet is counted under every other filter but its own, so picking a
    kind shows how many of each reliability that kind holds, and vice versa.
    """
    q = (q or "").strip()
    base = [Source.universe_id == universe_id]
    if q:
        base.append(_text_clause(q))
    if publication == "__none__":
        base.append(sa.or_(Source.publication.is_(None), Source.publication == ""))
    elif publication:
        base.append(Source.publication == publication)
    if uncited:
        base.append(_uncited_clause())
    kind_clause = [Source.kind == kind] if kind else []
    rel_clause = [Source.reliability == reliability] if reliability else []

    facets: dict[str, dict[str, int]] = {}
    for name, col, others in (
        ("kind", Source.kind, rel_clause),
        ("reliability", Source.reliability, kind_clause),
    ):
        rows = await session.execute(select(col, func.count()).where(*base, *others).group_by(col))
        facets[name] = {getattr(k, "value", k): int(n) for k, n in rows.all()}

    where = [*base, *kind_clause, *rel_clause]
    total = (
        await session.execute(select(func.count()).select_from(Source).where(*where))
    ).scalar_one()

    desc = order != "asc"

    def direction(expr):
        return expr.desc().nulls_last() if desc else expr.asc().nulls_last()

    if sort == "title":
        ordering = [direction(func.lower(Source.title))]
    elif sort == "published":
        ordering = [
            direction(Source.published_at["year"].astext.cast(sa.Integer)),
            direction(Source.published_at["month"].astext.cast(sa.Integer)),
            direction(Source.published_at["day"].astext.cast(sa.Integer)),
        ]
    elif sort == "cited":
        ordering = [direction(_cited_expr())]
    elif sort == "reliability":
        rank = sa.case(
            *((Source.reliability == r, n) for r, n in _RELIABILITY_RANK.items()), else_=9
        )
        # "desc" means most reliable first.
        ordering = [rank.asc() if desc else rank.desc()]
    elif q and sort == "relevance":
        ordering = [_rank_expr(q).desc()]
    else:
        ordering = [direction(Source.created_at)]
    ordering.append(Source.id)

    rows = await session.execute(
        select(Source).where(*where).order_by(*ordering).offset(offset).limit(limit)
    )
    items = list(rows.scalars().all())
    await attach_counts(session, items)
    return items, int(total), facets


async def search_sources(
    session: AsyncSession, universe_id: uuid.UUID, q: str, limit: int = 20
) -> list[Source]:
    """Best matches first, over title, publication and URL.

    A pasted URL puts its exact match, or its custody lookup source, first.
    """
    q = q.strip()
    pinned: list[Source] = []
    if "://" in q or q.startswith("www."):
        pinned = await find_by_url(session, universe_id, q)
        system = lookup_system(q)
        if system:
            canonical = await lookup_source(session, universe_id, system.value)
            if canonical is not None and canonical not in pinned:
                pinned.insert(0, canonical)
    rows = await session.execute(
        select(Source)
        .where(Source.universe_id == universe_id, _text_clause(q))
        .order_by(_rank_expr(q).desc(), Source.created_at.desc())
        .limit(limit)
    )
    seen = {s.id for s in pinned}
    items = pinned + [s for s in rows.scalars().all() if s.id not in seen]
    items = items[:limit]
    await attach_counts(session, items)
    return items


async def lookup_url(session: AsyncSession, universe_id: uuid.UUID, url: str) -> SourceLookup:
    """What the wiki holds for a URL about to be cited or added."""
    exact = await find_by_url(session, universe_id, url)
    system = lookup_system(url)
    canonical = await lookup_source(session, universe_id, system.value) if system else None
    same_host: list[Source] = []
    host = domain_of(url)
    if host and not exact and canonical is None:
        rows = await session.execute(
            select(Source)
            .where(Source.universe_id == universe_id, Source.url_norm.ilike(f"%://{host}%"))
            .order_by(Source.created_at.desc())
            .limit(5)
        )
        same_host = list(rows.scalars().all())
    await attach_counts(session, [*exact[:1], *([canonical] if canonical else []), *same_host])
    return SourceLookup(
        exact=exact[0] if exact else None,
        lookup={"source": canonical, "suggested_locator": lookup_locator(url)}
        if canonical
        else None,
        same_host=same_host,
    )


# --- who cites a source -----------------------------------------------------------


async def _universe_slug(session: AsyncSession, universe_id: uuid.UUID) -> str | None:
    return (
        await session.execute(select(Universe.slug).where(Universe.id == universe_id))
    ).scalar_one_or_none()


def _member_label(m: Member) -> str:
    return m.display_name


async def list_source_citations(
    session: AsyncSession,
    source: Source,
    entity_type: str,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[dict], int]:
    """One page of the records citing `source`, of one type, with the citation.

    Each row is the citation's fields plus a uniform `entity` reference
    (type, id, slug, label, detail, universe_slug), so the source page renders
    every record type with one component.
    """
    column = TARGET_COLUMN[entity_type]
    model = {
        "member": Member,
        "incident": Incident,
        "set": GangSet,
        "alliance": Alliance,
        "court_case": CourtCase,
        "municipality": Municipality,
        "business": Business,
    }[entity_type]
    fk = getattr(Citation, column)
    where = [Citation.source_id == source.id, fk.is_not(None)]
    total = (
        await session.execute(select(func.count()).select_from(Citation).where(*where))
    ).scalar_one()

    if entity_type == "incident":
        ordering = [Incident.sortable_date.desc().nulls_last(), Incident.created_at.desc()]
    elif entity_type == "member":
        ordering = [func.lower(func.coalesce(Member.nickname, Member.legal_name))]
    else:
        ordering = [func.lower(model.name)]
    rows = await session.execute(
        select(Citation, model)
        .join(model, model.id == fk)
        .where(*where)
        .order_by(*ordering, Citation.id)
        .offset(offset)
        .limit(limit)
    )
    slug = await _universe_slug(session, source.universe_id)
    out = []
    for c, e in rows.all():
        if entity_type == "member":
            ref = {"slug": e.slug, "label": _member_label(e), "detail": e.status.value}
        elif entity_type == "incident":
            ref = {
                "slug": None,
                "label": e.location_text or e.type.value.title(),
                "detail": e.type.value,
                "date": e.date,
            }
        elif entity_type == "court_case":
            ref = {"slug": e.slug, "label": e.name, "detail": e.docket}
        elif entity_type == "municipality":
            ref = {"slug": None, "label": e.name, "detail": getattr(e.kind, "value", e.kind)}
        else:
            ref = {"slug": e.slug, "label": e.name, "detail": None}
        out.append(
            {
                "id": c.id,
                "source_id": c.source_id,
                "position": c.position,
                "locator": c.locator,
                "quote": c.quote,
                "note": c.note,
                "accessed_at": c.accessed_at,
                "created_at": c.created_at,
                "entity": {
                    "type": entity_type,
                    "id": e.id,
                    "universe_slug": slug,
                    "date": None,
                    **ref,
                },
            }
        )
    return out, int(total)


async def list_source_custody_ids(session: AsyncSession, source_id: uuid.UUID) -> list[dict]:
    rows = await session.execute(
        select(MemberCustodyId, Member)
        .join(Member, Member.id == MemberCustodyId.member_id)
        .where(MemberCustodyId.source_id == source_id)
        .order_by(MemberCustodyId.system, MemberCustodyId.number)
    )
    return [
        {
            "id": c.id,
            "system": c.system,
            "number": c.number,
            "retrieved_at": c.retrieved_at,
            "member_id": m.id,
            "member_slug": m.slug,
            "member_label": m.display_name,
        }
        for c, m in rows.all()
    ]


# --- merge and delete ---------------------------------------------------------------


def _join(a: str | None, b: str | None, sep: str) -> str | None:
    parts = [p for p in (a, b) if p]
    return sep.join(dict.fromkeys(parts)) or None


async def merge_into(
    session: AsyncSession, from_source: Source, into: Source, commit: bool = True
) -> dict[str, int]:
    """Move everything citing `from_source` onto `into`, then delete it.

    A record citing both keeps one citation: locators and notes are joined,
    the later reading date wins, and the target's quote and position stay.
    """
    if from_source.id == into.id:
        raise ApiError(422, "merge_self", "A source cannot be merged into itself.")
    if from_source.universe_id != into.universe_id:
        raise ApiError(422, "merge_universe", "Sources from different universes cannot merge.")
    moved = combined = 0
    citing = (
        (await session.execute(select(Citation).where(Citation.source_id == from_source.id)))
        .scalars()
        .all()
    )
    for c in citing:
        entity, entity_id = c.target()
        column = TARGET_COLUMN[entity]
        other = (
            await session.execute(
                select(Citation).where(
                    getattr(Citation, column) == entity_id, Citation.source_id == into.id
                )
            )
        ).scalar_one_or_none()
        if other is None:
            c.source_id = into.id
            c.updated_at = datetime.now(UTC)
            session.add(c)
            moved += 1
        else:
            other.locator = _join(other.locator, c.locator, "; ")
            other.note = _join(other.note, c.note, "\n\n")
            other.quote = other.quote or c.quote
            dates = [d for d in (other.accessed_at, c.accessed_at) if d]
            other.accessed_at = max(dates) if dates else None
            other.updated_at = datetime.now(UTC)
            session.add(other)
            await session.delete(c)
            combined += 1
    await session.flush()
    for model in (MemberCustodyId, MemberAlias, Media):
        rows = (
            (await session.execute(select(model).where(model.source_id == from_source.id)))
            .scalars()
            .all()
        )
        for r in rows:
            r.source_id = into.id
            session.add(r)
            moved += 1
    await session.flush()
    await session.delete(from_source)
    if commit:
        await session.commit()
    return {"moved": moved, "combined": combined}


async def delete_source(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, force: bool = False
) -> bool:
    """Delete a source. In use, it needs `force`, which detaches everything first.

    Citations are deleted one by one through the ORM so the audit log keeps
    what each linked; custody numbers and aliases lose their source; photos go
    through the media delete, which also removes the stored files.
    """
    from app.crud.media import delete_media

    obj = await get_source(session, id, universe_id)
    if obj is None:
        return False
    counts = (await counts_for(session, [id]))[id]
    if counts.total and not force:
        raise ApiError(
            409,
            "source_in_use",
            "This source is cited; delete with force to detach it everywhere.",
            counts=counts.model_dump(),
        )
    media_ids = (
        (await session.execute(select(Media.id).where(Media.source_id == id))).scalars().all()
    )
    for mid in media_ids:
        await delete_media(session, mid, universe_id)
    for c in (await session.execute(select(Citation).where(Citation.source_id == id))).scalars():
        await session.delete(c)
    for model in (MemberCustodyId, MemberAlias):
        for r in (await session.execute(select(model).where(model.source_id == id))).scalars():
            r.source_id = None
            session.add(r)
    await session.flush()
    await session.delete(obj)
    await session.commit()
    return True
