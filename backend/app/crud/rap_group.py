import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core.audit import record_link_change
from app.core.enums import RapGroupKind, RapGroupStatus, SetRelationshipType
from app.core.slug import slugify
from app.crud import incident as incident_crud
from app.crud import member as member_crud
from app.crud.media import attach_primary_photos_rap_groups, delete_media
from app.models.media import Media
from app.models.member import Member
from app.models.municipality import Municipality
from app.models.rap_group import RapGroup, RapGroupMember, RapGroupRelationship
from app.schemas.incident import IncidentListItem
from app.schemas.rap_group import (
    RapGroupCreate,
    RapGroupListItem,
    RapGroupMemberIn,
    RapGroupMemberOut,
    RapGroupMunicipality,
    RapGroupRelationshipOut,
    RapGroupSetRef,
    RapGroupSetRepresented,
    RapGroupUpdate,
)


def _fuzzy_to_dict(fd) -> dict | None:
    if fd is None:
        return None
    return fd.model_dump()


def _slugify(s: str) -> str:
    return slugify(s, "rap-group")


async def _unique_slug(
    session: AsyncSession, universe_id: uuid.UUID, base: str, exclude_id: uuid.UUID | None = None
) -> str:
    slug, n = base, 2
    while True:
        q = select(RapGroup).where(RapGroup.universe_id == universe_id, RapGroup.slug == slug)
        if exclude_id:
            q = q.where(RapGroup.id != exclude_id)
        if (await session.execute(q)).scalar_one_or_none() is None:
            return slug
        slug, n = f"{base}-{n}", n + 1


async def _check_municipality(
    session: AsyncSession, municipality_id: uuid.UUID | None, universe_id: uuid.UUID
) -> None:
    if municipality_id is None:
        return
    found = (
        await session.execute(
            select(Municipality.id).where(
                Municipality.id == municipality_id, Municipality.universe_id == universe_id
            )
        )
    ).first()
    if found is None:
        raise HTTPException(422, detail="municipality_id is not in this universe")


async def _check_members(
    session: AsyncSession, member_ids: list[uuid.UUID], universe_id: uuid.UUID
) -> None:
    """Every member must live in the group's universe. Unlike an incident's
    participants, a rap group does not cross universes."""
    if not member_ids:
        return
    found = set(
        (
            await session.execute(
                select(Member.id).where(
                    Member.id.in_(member_ids), Member.universe_id == universe_id
                )
            )
        ).scalars()
    )
    missing = [str(i) for i in member_ids if i not in found]
    if missing:
        raise HTTPException(422, detail=f"members not in this universe: {', '.join(missing)}")


async def _sync_members(
    session: AsyncSession, group: RapGroup, members: list[RapGroupMemberIn]
) -> None:
    """Make the group hold exactly `members`, in that order.

    Reconciles by diff and goes through the ORM, so an unchanged member writes
    nothing and the audit log sees each row that does change.
    """
    await _check_members(session, [m.member_id for m in members], group.universe_id)
    current = {
        r.member_id: r
        for r in (
            await session.execute(
                select(RapGroupMember).where(RapGroupMember.rap_group_id == group.id)
            )
        )
        .scalars()
        .all()
    }
    fields = ["member_id", "role", "since", "until", "position"]
    # rap_group_member is audited row by row, but a deleted row is logged as
    # {"deleted": true} under no id of its own, so History records the list
    # on the group like every other join table (backend/CLAUDE.md).
    record_link_change(
        session,
        entity_type="rap_group",
        entity_id=group.id,
        link="members",
        key="member_id",
        before=[{f: getattr(r, f) for f in fields} for r in current.values()],
        after=[
            {
                "member_id": m.member_id,
                "role": m.role,
                "since": _fuzzy_to_dict(m.since),
                "until": _fuzzy_to_dict(m.until),
                "position": position,
            }
            for position, m in enumerate(members)
        ],
    )
    wanted = {m.member_id for m in members}
    for member_id, row in current.items():
        if member_id not in wanted:
            await session.delete(row)
    for position, m in enumerate(members):
        since, until = _fuzzy_to_dict(m.since), _fuzzy_to_dict(m.until)
        row = current.get(m.member_id)
        if row is None:
            session.add(
                RapGroupMember(
                    rap_group_id=group.id,
                    member_id=m.member_id,
                    role=m.role,
                    since=since,
                    until=until,
                    position=position,
                )
            )
            continue
        for field, value in (
            ("role", m.role),
            ("since", since),
            ("until", until),
            ("position", position),
        ):
            if getattr(row, field) != value:
                setattr(row, field, value)
                session.add(row)
    await session.flush()


async def _sync_relationships(
    session: AsyncSession,
    group: RapGroup,
    friend_ids: list[uuid.UUID],
    enemy_ids: list[uuid.UUID],
) -> None:
    """Make the group's friends and enemies exactly these lists.

    Each pair is stored once, smaller id first. Diffed rather than rebuilt, for
    the reason `_sync_set_relationships` gives: INSERTs flush before DELETEs.
    """
    others = list(dict.fromkeys([*friend_ids, *enemy_ids]))
    if others:
        found = set(
            (
                await session.execute(
                    select(RapGroup.id).where(
                        RapGroup.id.in_(others), RapGroup.universe_id == group.universe_id
                    )
                )
            ).scalars()
        )
        missing = [str(i) for i in others if i not in found]
        if missing:
            raise HTTPException(
                422, detail=f"rap groups not in this universe: {', '.join(missing)}"
            )

    def _pair(other: uuid.UUID) -> tuple[uuid.UUID, uuid.UUID]:
        return (group.id, other) if group.id < other else (other, group.id)

    desired: dict[tuple[uuid.UUID, uuid.UUID], SetRelationshipType] = {}
    for fid in friend_ids:
        desired[_pair(fid)] = SetRelationshipType.FRIEND
    for eid in enemy_ids:
        # An id in both lists is contradictory; enemy wins, as for sets.
        desired[_pair(eid)] = SetRelationshipType.ENEMY
    desired.pop((group.id, group.id), None)

    existing = (
        (
            await session.execute(
                select(RapGroupRelationship).where(
                    (RapGroupRelationship.rap_group_a_id == group.id)
                    | (RapGroupRelationship.rap_group_b_id == group.id)
                )
            )
        )
        .scalars()
        .all()
    )

    def _other(a: uuid.UUID, b: uuid.UUID) -> uuid.UUID:
        return b if a == group.id else a

    for link, rel_type in (
        ("allies", SetRelationshipType.FRIEND),
        ("enemies", SetRelationshipType.ENEMY),
    ):
        record_link_change(
            session,
            entity_type="rap_group",
            entity_id=group.id,
            link=link,
            key="rap_group_id",
            before=[
                {"rap_group_id": _other(r.rap_group_a_id, r.rap_group_b_id)}
                for r in existing
                if r.relationship_type == rel_type
            ],
            after=[
                {"rap_group_id": _other(a, b)} for (a, b), t in desired.items() if t == rel_type
            ],
        )
    kept: set[tuple[uuid.UUID, uuid.UUID]] = set()
    for rel in existing:
        key = (rel.rap_group_a_id, rel.rap_group_b_id)
        if desired.get(key) == rel.relationship_type:
            kept.add(key)
            continue
        await session.delete(rel)
    await session.flush()
    for (a, b), rel_type in desired.items():
        if (a, b) not in kept:
            session.add(
                RapGroupRelationship(rap_group_a_id=a, rap_group_b_id=b, relationship_type=rel_type)
            )
    await session.flush()


async def list_relationship_ids(
    session: AsyncSession, group_id: uuid.UUID
) -> tuple[list[uuid.UUID], list[uuid.UUID]]:
    """(friend ids, enemy ids) of the group."""
    rows = (
        (
            await session.execute(
                select(RapGroupRelationship).where(
                    (RapGroupRelationship.rap_group_a_id == group_id)
                    | (RapGroupRelationship.rap_group_b_id == group_id)
                )
            )
        )
        .scalars()
        .all()
    )
    friends, enemies = [], []
    for r in rows:
        other = r.rap_group_b_id if r.rap_group_a_id == group_id else r.rap_group_a_id
        (friends if r.relationship_type == SetRelationshipType.FRIEND else enemies).append(other)
    return friends, enemies


async def create_rap_group(
    session: AsyncSession, data: RapGroupCreate, actor_id: uuid.UUID
) -> RapGroup:
    await _check_municipality(session, data.municipality_id, data.universe_id)
    dump = data.model_dump(exclude={"members", "friend_ids", "enemy_ids"})
    dump["active_from"] = _fuzzy_to_dict(data.active_from)
    dump["active_to"] = _fuzzy_to_dict(data.active_to)
    dump["slug"] = await _unique_slug(session, data.universe_id, _slugify(data.name))
    obj = RapGroup(**dump, created_by_id=actor_id)
    session.add(obj)
    await session.flush()
    await _sync_members(session, obj, data.members)
    await _sync_relationships(session, obj, data.friend_ids, data.enemy_ids)
    await session.commit()
    await session.refresh(obj)
    return obj


async def get_rap_group(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> RapGroup | None:
    result = await session.execute(
        select(RapGroup).where(RapGroup.id == id, RapGroup.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def get_rap_group_by_slug(
    session: AsyncSession, slug: str, universe_id: uuid.UUID
) -> RapGroup | None:
    result = await session.execute(
        select(RapGroup).where(RapGroup.slug == slug, RapGroup.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


def _search_clause(q: str):
    """Match the name or any slot of any name variant."""
    pattern = f"%{q}%"
    return RapGroup.name.ilike(pattern) | sa.cast(RapGroup.name_variants, sa.Text).ilike(pattern)


async def list_rap_groups(
    session: AsyncSession,
    universe_id: uuid.UUID,
    *,
    q: str | None = None,
    status: RapGroupStatus | None = None,
    kind: RapGroupKind | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[RapGroup], int]:
    where = [RapGroup.universe_id == universe_id]
    if q and q.strip():
        where.append(_search_clause(q.strip()))
    if status is not None:
        where.append(RapGroup.status == status)
    if kind is not None:
        where.append(RapGroup.kind == kind)
    total = (
        await session.execute(select(func.count()).select_from(RapGroup).where(*where))
    ).scalar_one()
    # Ordered, with a tiebreak: unordered offset pages can repeat or skip rows.
    result = await session.execute(
        select(RapGroup)
        .where(*where)
        .order_by(RapGroup.name, RapGroup.id)
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all()), total


async def to_list_items(session: AsyncSession, groups: list[RapGroup]) -> list[RapGroupListItem]:
    """List rows: member count, home area and primary photo, in three batched queries."""
    if not groups:
        return []
    ids = [g.id for g in groups]
    counts = dict(
        (
            await session.execute(
                select(RapGroupMember.rap_group_id, func.count())
                .where(RapGroupMember.rap_group_id.in_(ids))
                .group_by(RapGroupMember.rap_group_id)
            )
        ).all()
    )
    muni_ids = [g.municipality_id for g in groups if g.municipality_id]
    munis = {}
    if muni_ids:
        rows = await session.execute(
            select(Municipality.id, Municipality.name).where(Municipality.id.in_(muni_ids))
        )
        munis = {i: RapGroupMunicipality(id=i, name=n) for i, n in rows.all()}
    await attach_primary_photos_rap_groups(session, groups)
    return [
        RapGroupListItem(
            id=g.id,
            slug=g.slug,
            name=g.name,
            name_variants=g.name_variants,
            kind=g.kind,
            status=g.status,
            active_from=g.active_from,
            active_to=g.active_to,
            municipality=munis.get(g.municipality_id) if g.municipality_id else None,
            member_count=int(counts.get(g.id, 0)),
            primary_photo_url=getattr(g, "primary_photo_url", None),
        )
        for g in groups
    ]


async def detail_extras(session: AsyncSession, group: RapGroup) -> dict:
    """What the group page shows beyond the list fields: members with their
    current sets, the sets they represent, relationships and incidents."""
    rows = (
        await session.execute(
            select(RapGroupMember, Member)
            .join(Member, Member.id == RapGroupMember.member_id)
            .where(RapGroupMember.rap_group_id == group.id)
            .order_by(RapGroupMember.position, RapGroupMember.member_id)
        )
    ).all()
    members = [m for _, m in rows]
    await member_crud.attach_primary_photos(session, members)
    affiliations = await member_crud.load_member_affiliations(session, [m.id for m in members])
    out_members: list[RapGroupMemberOut] = []
    represented: dict[uuid.UUID, RapGroupSetRepresented] = {}
    for link, m in rows:
        # Current spells only, primary first: the sets he stands in now.
        current = sorted(
            (a for a in affiliations.get(m.id, []) if a.until_date is None),
            key=lambda a: not a.is_primary,
        )
        sets = [RapGroupSetRef(id=a.set_id, slug=a.set_slug, name=a.set_name) for a in current]
        for s in sets:
            if s.id in represented:
                represented[s.id].count += 1
            else:
                represented[s.id] = RapGroupSetRepresented(**s.model_dump(), count=1)
        out_members.append(
            RapGroupMemberOut(
                member_id=m.id,
                slug=m.slug,
                display_name=m.display_name,
                role=link.role,
                since=link.since,
                until=link.until,
                primary_photo_thumb_url=getattr(m, "primary_photo_thumb_url", None),
                status=m.status,
                sets=sets,
            )
        )

    rel_rows = (
        await session.execute(
            select(RapGroupRelationship, RapGroup)
            .join(
                RapGroup,
                RapGroup.id
                == sa.case(
                    (
                        RapGroupRelationship.rap_group_a_id == group.id,
                        RapGroupRelationship.rap_group_b_id,
                    ),
                    else_=RapGroupRelationship.rap_group_a_id,
                ),
            )
            .where(
                (RapGroupRelationship.rap_group_a_id == group.id)
                | (RapGroupRelationship.rap_group_b_id == group.id)
            )
            .order_by(RapGroupRelationship.relationship_type, RapGroup.name)
        )
    ).all()
    relationships = [
        RapGroupRelationshipOut(
            rap_group_id=other.id,
            slug=other.slug,
            name=other.name,
            type=rel.relationship_type.value,
        )
        for rel, other in rel_rows
    ]

    incidents = await incident_crud.list_incidents_by_rap_group(session, group.id)
    incidents = await incident_crud.enrich_participant_names(session, incidents)
    return {
        "members": out_members,
        "sets_represented": sorted(
            represented.values(), key=lambda s: (-s.count, s.name.lower(), str(s.id))
        ),
        "relationships": relationships,
        "incidents": [IncidentListItem.model_validate(i) for i in incidents],
    }


async def update_rap_group(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, data: RapGroupUpdate
) -> RapGroup | None:
    obj = await get_rap_group(session, id, universe_id)
    if obj is None:
        return None
    dump = data.model_dump(exclude_unset=True, exclude={"members", "friend_ids", "enemy_ids"})
    if "municipality_id" in dump:
        await _check_municipality(session, dump["municipality_id"], universe_id)
    for field in ("active_from", "active_to"):
        if field in dump:
            dump[field] = _fuzzy_to_dict(getattr(data, field))
    old_name = obj.name
    for k, v in dump.items():
        setattr(obj, k, v)
    # JSONB values assigned through setattr are not seen as changed without this.
    for column in ("name_variants", "active_from", "active_to"):
        if column in dump:
            sa.orm.attributes.flag_modified(obj, column)
    # name is re-derived on every variants edit; only a real rename re-slugs,
    # so a link to the group survives an edit that leaves its name alone.
    if obj.name != old_name:
        obj.slug = await _unique_slug(session, universe_id, _slugify(obj.name), exclude_id=id)
    obj.updated_at = datetime.now(UTC)
    session.add(obj)
    if data.members is not None:
        await _sync_members(session, obj, data.members)
    if data.friend_ids is not None or data.enemy_ids is not None:
        # A list that was not sent stays as it is: sending only friend_ids must
        # not wipe the enemies.
        friends, enemies = await list_relationship_ids(session, obj.id)
        await _sync_relationships(
            session,
            obj,
            data.friend_ids if data.friend_ids is not None else friends,
            data.enemy_ids if data.enemy_ids is not None else enemies,
        )
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_rap_group(session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID) -> bool:
    obj = await get_rap_group(session, id, universe_id)
    if obj is None:
        return False
    # Photos cascade in the database, but only the media CRUD removes the R2
    # objects, so they go through it rather than being left orphaned.
    photos = (await session.execute(select(Media).where(Media.rap_group_id == id))).scalars()
    for photo in photos.all():
        await delete_media(session, photo.id, photo.universe_id)
    # Members, relationships and citations cascade in the database; their rows
    # are removed through the ORM first so the audit log records them.
    for model, col in (
        (RapGroupMember, RapGroupMember.rap_group_id),
        (RapGroupRelationship, RapGroupRelationship.rap_group_a_id),
        (RapGroupRelationship, RapGroupRelationship.rap_group_b_id),
    ):
        for row in (await session.execute(select(model).where(col == id))).scalars().all():
            await session.delete(row)
    await session.flush()
    await session.delete(obj)
    await session.commit()
    return True
