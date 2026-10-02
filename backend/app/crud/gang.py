import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from fastapi import HTTPException, status
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core.slug import slugify
from app.crud.media import attach_primary_photos_sets
from app.models.alliance import Alliance
from app.models.gang import Gang, GangCard
from app.models.gang_set import GangSet, SetGang
from app.models.member import Member, MemberSet
from app.models.municipality import Municipality
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


def _fuzzy_to_dict(fd) -> dict | None:
    return fd.model_dump() if fd is not None else None


async def _check_parent(
    session: AsyncSession, universe_id: uuid.UUID, gang_id: uuid.UUID | None, parent_id
) -> None:
    """A parent must be a card of the same universe and must not close a loop.

    Walking up from the proposed parent: meeting the card itself means the new
    link would make it its own ancestor.
    """
    if parent_id is None:
        return
    if gang_id is not None and parent_id == gang_id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "A gang cannot be its own parent"
        )
    seen: set[uuid.UUID] = set()
    cursor: uuid.UUID | None = parent_id
    while cursor is not None:
        row = (
            await session.execute(
                select(Gang.id, Gang.parent_id, Gang.universe_id).where(Gang.id == cursor)
            )
        ).one_or_none()
        if row is None or row[2] != universe_id:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, "parent_id is not a gang in this universe"
            )
        if gang_id is not None and row[1] == gang_id:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                "That parent would make the gang its own ancestor",
            )
        if cursor in seen:  # a loop already on file; stop rather than spin
            break
        seen.add(cursor)
        cursor = row[1]


# What a gang *is*: kept on its card and mirrored onto every linked gang row.
REF_FIELDS = ("color", "color_secondary", "nation", "origin", "founded_at", "symbols")


async def _unique_card_slug(session: AsyncSession, base: str) -> str:
    slug, n = base, 2
    while (
        await session.execute(select(GangCard.id).where(GangCard.slug == slug))
    ).scalar_one_or_none() is not None:
        slug, n = f"{base}-{n}", n + 1
    return slug


async def _check_card_parent(session: AsyncSession, card_id: uuid.UUID, parent_id) -> None:
    """A card must not end up among its own ancestors."""
    cursor, seen = parent_id, set()
    while cursor is not None and cursor not in seen:
        if cursor == card_id:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                "That parent would make the gang its own ancestor",
            )
        seen.add(cursor)
        cursor = (
            await session.execute(select(GangCard.parent_id).where(GangCard.id == cursor))
        ).scalar_one_or_none()


async def sync_hierarchy(session: AsyncSession) -> None:
    """Every linked gang sits under the gang of its own universe that holds its
    card's parent card, and under nothing when that universe has none.

    Set-based on purpose: one card's parent changing moves its gang in every
    universe at once, and a gang created in one universe can adopt branches
    already on file there.
    """
    await session.execute(
        sa.text(
            """
            UPDATE gang g SET parent_id = p.id
            FROM gang_card c, gang p
            WHERE g.card_id = c.id AND p.card_id = c.parent_id
              AND p.universe_id = g.universe_id
              AND g.parent_id IS DISTINCT FROM p.id
            """
        )
    )
    await session.execute(
        sa.text(
            """
            UPDATE gang g SET parent_id = NULL
            FROM gang_card c
            WHERE g.card_id = c.id AND g.parent_id IS NOT NULL
              AND (c.parent_id IS NULL OR NOT EXISTS (
                  SELECT 1 FROM gang p
                  WHERE p.card_id = c.parent_id AND p.universe_id = g.universe_id))
            """
        )
    )


async def sync_card_to_gangs(session: AsyncSession, card: GangCard) -> None:
    """Copy the card's reference fields onto every gang linked to it."""
    await session.execute(
        Gang.__table__.update()
        .where(Gang.card_id == card.id)
        .values(**{f: getattr(card, f) for f in REF_FIELDS}, updated_at=datetime.now(UTC))
    )


async def _card_parent_from_gang(session: AsyncSession, parent_gang_id) -> uuid.UUID | None:
    if parent_gang_id is None:
        return None
    return (
        await session.execute(select(Gang.card_id).where(Gang.id == parent_gang_id))
    ).scalar_one_or_none()


async def create_gang(session: AsyncSession, data: GangCreate, actor_id: uuid.UUID) -> Gang:
    """Create a universe's gang, linked to the shared card of the same name.

    An existing card keeps its reference fields, except any the caller sends,
    which update it for every universe. With no card of that name, one is made
    from what the caller sends.
    """
    await _check_parent(session, data.universe_id, None, data.parent_id)
    base = _slugify(data.name)
    slug = await _unique_slug(session, data.universe_id, base)
    fields = data.model_dump(exclude={"founded_at", "card_description", "universe_id", "name"})
    fields["founded_at"] = _fuzzy_to_dict(data.founded_at)
    ref = {f: fields.pop(f) for f in REF_FIELDS}

    card = (
        await session.execute(
            select(GangCard)
            .where(func.lower(GangCard.name) == data.name.strip().lower())
            # Oldest first: cards backfilled for look-alike local groups can
            # share a name, and the first one made is the one others joined.
            .order_by(GangCard.created_at, GangCard.id)
            .limit(1)
        )
    ).scalar_one_or_none()
    parent_card = await _card_parent_from_gang(session, data.parent_id)
    if card is None:
        card = GangCard(
            slug=await _unique_card_slug(session, base),
            name=data.name.strip(),
            description=data.card_description,
            parent_id=parent_card,
            **ref,
        )
        session.add(card)
        await session.flush()
    else:
        for k, v in ref.items():
            if v is not None:
                setattr(card, k, v)
        if data.card_description is not None:
            card.description = data.card_description
        if data.parent_id is not None and parent_card is not None:
            await _check_card_parent(session, card.id, parent_card)
            card.parent_id = parent_card
        card.updated_at = datetime.now(UTC)
        session.add(card)
        await session.flush()

    obj = Gang(
        universe_id=data.universe_id,
        name=data.name,
        slug=slug,
        card_id=card.id,
        created_by_id=actor_id,
        **{k: v for k, v in fields.items() if k != "parent_id"},
        **{f: getattr(card, f) for f in REF_FIELDS},
    )
    session.add(obj)
    await session.flush()
    await sync_card_to_gangs(session, card)
    await sync_hierarchy(session)
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
    items = list(result.scalars().all())
    await attach_gang_counts(session, universe_id, items)
    return items, total


async def attach_gang_counts(
    session: AsyncSession, universe_id: uuid.UUID, items: list[Gang]
) -> None:
    """Attach set_count, alliance_count and member_count to each card.

    member_count follows the alliance definition: members tagged to the card
    directly plus the current members of every set claiming it (as primary or
    secondary gang), each person counted once.
    """
    if not items:
        return
    ids = [g.id for g in items]
    set_counts = dict(
        (
            await session.execute(
                select(SetGang.gang_id, func.count())
                .where(SetGang.gang_id.in_(ids))
                .group_by(SetGang.gang_id)
            )
        ).all()
    )
    alliance_counts = dict(
        (
            await session.execute(
                select(Alliance.gang_id, func.count())
                .where(Alliance.gang_id.in_(ids))
                .group_by(Alliance.gang_id)
            )
        ).all()
    )
    member_counts = dict(
        (
            await session.execute(
                sa.text(
                    """
                    SELECT gang_id, count(DISTINCT member_id) FROM (
                        SELECT m.gang_id, m.id AS member_id
                        FROM member m
                        WHERE m.universe_id = :uid AND m.gang_id IS NOT NULL
                        UNION
                        SELECT sg.gang_id, ms.member_id
                        FROM set_gang sg
                        JOIN member_set ms ON ms.set_id = sg.set_id
                        JOIN sets s ON s.id = sg.set_id
                        WHERE s.universe_id = :uid AND ms.until_date IS NULL
                    ) x
                    GROUP BY gang_id
                    """
                ),
                {"uid": universe_id},
            )
        ).all()
    )
    card_ids = {g.card_id for g in items if g.card_id}
    cards = {}
    if card_ids:
        cards = {
            c.id: c
            for c in (
                await session.execute(select(GangCard).where(GangCard.id.in_(card_ids)))
            ).scalars()
        }
    for g in items:
        card = cards.get(g.card_id) if g.card_id else None
        object.__setattr__(g, "card_description", card.description if card else None)
        object.__setattr__(g, "card_aliases", card.aliases if card else None)
        object.__setattr__(g, "card_slug", card.slug if card else None)
        object.__setattr__(g, "set_count", int(set_counts.get(g.id, 0)))
        object.__setattr__(g, "alliance_count", int(alliance_counts.get(g.id, 0)))
        object.__setattr__(g, "member_count", int(member_counts.get(g.id, 0)))


async def get_gang_detail(session: AsyncSession, gang: Gang) -> dict:
    """Everything the gang page shows: lineage, branches, sets, alliances."""
    await attach_gang_counts(session, gang.universe_id, [gang])

    def summary(g: Gang) -> dict:
        return {
            "id": g.id,
            "name": g.name,
            "slug": g.slug,
            "color": g.color,
            "color_secondary": g.color_secondary,
        }

    ancestors: list[dict] = []
    seen = {gang.id}
    cursor = gang.parent_id
    while cursor is not None and cursor not in seen:
        parent = await get_gang(session, cursor, gang.universe_id)
        if parent is None:
            break
        ancestors.append(summary(parent))
        seen.add(parent.id)
        cursor = parent.parent_id

    branches = list(
        (
            await session.execute(select(Gang).where(Gang.parent_id == gang.id).order_by(Gang.name))
        ).scalars()
    )
    await attach_gang_counts(session, gang.universe_id, branches)

    member_count_sq = (
        select(MemberSet.set_id, func.count(func.distinct(MemberSet.member_id)).label("n"))
        .where(MemberSet.until_date.is_(None))
        .group_by(MemberSet.set_id)
        .subquery()
    )
    set_rows = (
        await session.execute(
            select(
                GangSet,
                SetGang.position,
                func.coalesce(member_count_sq.c.n, 0),
                Municipality.name,
                Alliance.name,
                Alliance.slug,
            )
            .join(SetGang, SetGang.set_id == GangSet.id)
            .join(member_count_sq, member_count_sq.c.set_id == GangSet.id, isouter=True)
            .join(Municipality, Municipality.id == GangSet.municipality_id, isouter=True)
            .join(Alliance, Alliance.id == GangSet.alliance_id, isouter=True)
            .where(SetGang.gang_id == gang.id)
            .order_by(func.coalesce(member_count_sq.c.n, 0).desc(), GangSet.name)
        )
    ).all()
    set_objs = [r[0] for r in set_rows]
    await attach_primary_photos_sets(session, set_objs)
    sets = [
        {
            "id": s.id,
            "name": s.name,
            "slug": s.slug,
            "status": s.status,
            "is_primary": position == 0,
            "member_count": int(n),
            "municipality_name": muni,
            "alliance_name": a_name,
            "alliance_slug": a_slug,
            "primary_photo_thumb_url": getattr(s, "primary_photo_thumb_url", None),
        }
        for s, position, n, muni, a_name, a_slug in set_rows
    ]
    alliances = [
        {"id": a.id, "name": a.name, "slug": a.slug, "status": a.status}
        for a in (
            await session.execute(
                select(Alliance).where(Alliance.gang_id == gang.id).order_by(Alliance.name)
            )
        ).scalars()
    ]
    return {
        "parent": ancestors[0] if ancestors else None,
        "ancestors": ancestors,
        "branches": branches,
        "sets": sets,
        "alliances": alliances,
    }


async def update_gang(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, data: GangUpdate
) -> Gang | None:
    """Local fields change here only; a linked gang's reference fields, parent
    and national description change on its card, for every universe."""
    obj = await get_gang(session, id, universe_id)
    if obj is None:
        return None
    dump = data.model_dump(exclude_unset=True)
    if "founded_at" in dump:
        dump["founded_at"] = _fuzzy_to_dict(data.founded_at)
    card_description = dump.pop("card_description", None)
    card_description_sent = "card_description" in data.model_fields_set
    card = await session.get(GangCard, obj.card_id) if obj.card_id else None

    if "parent_id" in dump:
        await _check_parent(session, universe_id, id, dump["parent_id"])
    if card is not None:
        ref = {f: dump.pop(f) for f in REF_FIELDS if f in dump}
        for k, v in ref.items():
            setattr(card, k, v)
        if card_description_sent:
            card.description = card_description
        if "parent_id" in dump:
            parent_card = await _card_parent_from_gang(session, dump["parent_id"])
            if dump["parent_id"] is None or parent_card is not None:
                await _check_card_parent(session, card.id, parent_card)
                card.parent_id = parent_card
                dump.pop("parent_id")
        card.updated_at = datetime.now(UTC)
        session.add(card)

    if "name" in dump:
        base = _slugify(dump["name"])
        dump["slug"] = await _unique_slug(session, universe_id, base, exclude_id=id)
    for k, v in dump.items():
        setattr(obj, k, v)
    obj.updated_at = datetime.now(UTC)
    session.add(obj)
    await session.flush()
    if card is not None:
        await sync_card_to_gangs(session, card)
        await sync_hierarchy(session)
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_gang(session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID) -> bool:
    obj = await get_gang(session, id, universe_id)
    if obj is None:
        return False
    # Detach references (FK is ON DELETE SET NULL, but we explicitly clear so
    # audit listeners observe the change).
    # A set that claims this gang among others keeps the others, and whichever
    # is next in line becomes its primary (the mirror in sets.gang_id).
    affected = list(
        (await session.execute(select(SetGang.set_id).where(SetGang.gang_id == id))).scalars()
    )
    await session.execute(delete(SetGang).where(SetGang.gang_id == id))
    for set_id in affected:
        next_gang = (
            await session.execute(
                select(SetGang.gang_id)
                .where(SetGang.set_id == set_id)
                .order_by(SetGang.position)
                .limit(1)
            )
        ).scalar_one_or_none()
        await session.execute(
            GangSet.__table__.update().where(GangSet.id == set_id).values(gang_id=next_gang)
        )
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
            select(func.count()).select_from(SetGang).where(SetGang.gang_id == id)
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
