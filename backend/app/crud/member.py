import re
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core import storage
from app.core.enums import MediaKind
from app.models.member import Member, MemberAlias, MemberIncarceration, MemberSource
from app.models.incident import IncidentParticipant
from app.models.gang_set import GangSet
from app.models.media import Media
from app.schemas.common import make_cursor, parse_cursor
from app.schemas.member import MemberAliasCreate, MemberCreate, MemberIncarcerationCreate, MemberIncarcerationUpdate, MemberUpdate


INVERSE_REL: dict[str, str] = {
    "father": "son",
    "son": "father",
    "uncle": "nephew",
    "nephew": "uncle",
    "brother": "brother",
    "cousin": "cousin",
}
SINGLE_RELS = {"father"}


def _family_ids(family: dict | None, rel: str) -> set[str]:
    if not family:
        return set()
    val = family.get(rel)
    if val is None:
        return set()
    if isinstance(val, list):
        return {str(v) for v in val}
    return {str(val)}


def _set_family_ids(family: dict, rel: str, ids: set[str]) -> None:
    if not ids:
        family.pop(rel, None)
    elif rel in SINGLE_RELS:
        family[rel] = next(iter(ids))
    else:
        family[rel] = list(ids)


async def _sync_bilateral_family(
    session: AsyncSession,
    member_id: uuid.UUID,
    universe_id: uuid.UUID,
    old_family: dict | None,
    new_family: dict | None,
) -> None:
    old_family = old_family or {}
    new_family = new_family or {}
    for rel, inv_rel in INVERSE_REL.items():
        added = _family_ids(new_family, rel) - _family_ids(old_family, rel)
        removed = _family_ids(old_family, rel) - _family_ids(new_family, rel)
        for rid in added | removed:
            try:
                related = await get_member(session, uuid.UUID(rid), universe_id)
            except ValueError:
                continue
            if not related:
                continue
            rel_family = dict(related.family or {})
            inv_ids = _family_ids(rel_family, inv_rel)
            if rid in added:
                inv_ids.add(str(member_id))
            else:
                inv_ids.discard(str(member_id))
            _set_family_ids(rel_family, inv_rel, inv_ids)
            related.family = rel_family or None
            related.updated_at = datetime.utcnow()
            session.add(related)


def _fuzzy_to_dict(fd) -> dict | None:
    if fd is None:
        return None
    return fd.model_dump()


def _slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-") or "member"


async def _unique_slug(
    session: AsyncSession, universe_id: uuid.UUID, base: str, exclude_id: uuid.UUID | None = None
) -> str:
    slug, n = base, 2
    while True:
        q = select(Member).where(Member.universe_id == universe_id, Member.slug == slug)
        if exclude_id:
            q = q.where(Member.id != exclude_id)
        if (await session.execute(q)).scalar_one_or_none() is None:
            return slug
        slug, n = f"{base}-{n}", n + 1


async def attach_primary_photos(session: AsyncSession, members: list[Member]) -> None:
    """Populate member.primary_photo_url + primary_photo_thumb_url for serialization.

    Single batched query fetches the is_primary media row per member; signed
    URLs are generated for R2-kind rows, external_url passes through for
    backfilled photo_url rows. Attributes are set on the ORM instance so
    Pydantic from_attributes picks them up.
    """
    if not members:
        return
    member_ids = [m.id for m in members]
    result = await session.execute(
        select(Media).where(
            Media.member_id.in_(member_ids),
            Media.is_primary == True,  # noqa: E712
        )
    )
    by_member: dict[uuid.UUID, Media] = {m.member_id: m for m in result.scalars().all()}
    for m in members:
        primary = by_member.get(m.id)
        if primary is None:
            url = None
            thumb = None
        elif primary.kind == MediaKind.EXTERNAL_URL:
            url = primary.external_url
            thumb = primary.external_url
        else:  # R2
            url = await storage.signed_get_url(primary.r2_key) if primary.r2_key else None
            thumb = (
                await storage.signed_get_url(primary.thumb_r2_key)
                if primary.thumb_r2_key
                else url
            )
        object.__setattr__(m, 'primary_photo_url', url)
        object.__setattr__(m, 'primary_photo_thumb_url', thumb)


async def _sync_member_sources(
    session: AsyncSession, member_id: uuid.UUID, source_ids: list[uuid.UUID]
) -> None:
    await session.execute(
        MemberSource.__table__.delete().where(MemberSource.member_id == member_id)
    )
    for sid in source_ids:
        session.add(MemberSource(member_id=member_id, source_id=sid))


async def create_member(
    session: AsyncSession, data: MemberCreate, actor_id: uuid.UUID
) -> Member:
    dump = data.model_dump(exclude={"source_ids", "dob", "date_of_death", "release_date"})
    dump["dob"] = _fuzzy_to_dict(data.dob)
    dump["date_of_death"] = _fuzzy_to_dict(data.date_of_death)
    dump["release_date"] = _fuzzy_to_dict(data.release_date)
    display = data.nickname if not data.nickname_unknown and data.nickname else data.legal_name
    if display:
        base = _slugify(display)
        dump["slug"] = await _unique_slug(session, data.universe_id, base)
    obj = Member(**dump, created_by_id=actor_id)
    session.add(obj)
    await session.flush()
    await _sync_member_sources(session, obj.id, data.source_ids)
    if data.family:
        await _sync_bilateral_family(session, obj.id, data.universe_id, None, data.family)
    await session.commit()
    await session.refresh(obj)
    return obj


async def get_member(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> Member | None:
    result = await session.execute(
        select(Member).where(Member.id == id, Member.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def get_member_by_slug(
    session: AsyncSession, slug: str, universe_id: uuid.UUID
) -> Member | None:
    result = await session.execute(
        select(Member).where(Member.slug == slug, Member.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def list_members(
    session: AsyncSession,
    universe_id: uuid.UUID,
    limit: int = 50,
    cursor: str | None = None,
    set_id: uuid.UUID | None = None,
    alliance_id: uuid.UUID | None = None,
) -> tuple[list[Member], str | None]:
    stmt = select(Member).where(Member.universe_id == universe_id)
    if set_id is not None:
        stmt = stmt.where(Member.set_id == set_id)
    if alliance_id is not None:
        stmt = stmt.where(Member.alliance_id == alliance_id)

    if cursor:
        cursor_at, cursor_id = parse_cursor(cursor)
        stmt = stmt.where(
            (Member.created_at < cursor_at)
            | ((Member.created_at == cursor_at) & (Member.id < cursor_id))
        )

    stmt = stmt.order_by(Member.created_at.desc(), Member.id.desc()).limit(limit + 1)
    result = await session.execute(stmt)
    items = result.scalars().all()

    next_cursor = None
    if len(items) > limit:
        items = items[:limit]
        last = items[-1]
        next_cursor = make_cursor(last.created_at, last.id)

    return items, next_cursor


async def update_member(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, data: MemberUpdate
) -> Member | None:
    obj = await get_member(session, id, universe_id)
    if obj is None:
        return None
    dump = data.model_dump(
        exclude_unset=True, exclude={"source_ids", "dob", "date_of_death", "release_date"}
    )
    if "dob" in data.model_fields_set:
        dump["dob"] = _fuzzy_to_dict(data.dob)
    if "date_of_death" in data.model_fields_set:
        dump["date_of_death"] = _fuzzy_to_dict(data.date_of_death)
    if "release_date" in data.model_fields_set:
        dump["release_date"] = _fuzzy_to_dict(data.release_date)
    dump["updated_at"] = datetime.utcnow()

    nickname_changed = "nickname" in data.model_fields_set or "nickname_unknown" in data.model_fields_set
    legal_changed = "legal_name" in data.model_fields_set
    if nickname_changed or legal_changed:
        new_nickname = dump.get("nickname", obj.nickname)
        new_unknown = dump.get("nickname_unknown", obj.nickname_unknown)
        new_legal = dump.get("legal_name", obj.legal_name)
        display = new_nickname if not new_unknown and new_nickname else new_legal
        if display:
            base = _slugify(display)
            dump["slug"] = await _unique_slug(session, universe_id, base, exclude_id=id)

    old_family = dict(obj.family or {})
    for k, v in dump.items():
        setattr(obj, k, v)
    session.add(obj)
    if data.source_ids is not None:
        await _sync_member_sources(session, obj.id, data.source_ids)
    if "family" in data.model_fields_set:
        await _sync_bilateral_family(session, obj.id, universe_id, old_family, dump.get("family"))
    await session.commit()
    await session.refresh(obj)
    return obj


async def bulk_update_member_status(
    session: AsyncSession,
    universe_id: uuid.UUID,
    member_ids: list[uuid.UUID],
    status: str,
) -> int:
    count = 0
    for mid in member_ids:
        obj = await get_member(session, mid, universe_id)
        if obj:
            obj.status = status
            obj.updated_at = datetime.utcnow()
            session.add(obj)
            count += 1
    await session.commit()
    return count


async def delete_member(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> bool:
    obj = await get_member(session, id, universe_id)
    if obj is None:
        return False
    # Remove incident participations (no cascade on member_id FK)
    await session.execute(
        IncidentParticipant.__table__.delete().where(IncidentParticipant.member_id == id)
    )
    # Remove source citations (no cascade on member_id FK)
    await session.execute(
        MemberSource.__table__.delete().where(MemberSource.member_id == id)
    )
    # Null out founder_id on any set this member founded (no cascade on founder_id FK)
    await session.execute(
        GangSet.__table__.update().where(GangSet.founder_id == id).values(founder_id=None)
    )
    # Detach bilateral family references stored as JSONB on other members
    await _sync_bilateral_family(session, id, universe_id, obj.family, None)
    await session.delete(obj)
    await session.commit()
    return True


async def list_member_source_ids(
    session: AsyncSession, member_id: uuid.UUID
) -> list[uuid.UUID]:
    result = await session.execute(
        select(MemberSource.source_id).where(MemberSource.member_id == member_id)
    )
    return result.scalars().all()


async def list_members_by_source(
    session: AsyncSession, source_id: uuid.UUID, universe_id: uuid.UUID, limit: int = 100
) -> list[Member]:
    stmt = (
        select(Member)
        .join(MemberSource, MemberSource.member_id == Member.id)
        .where(MemberSource.source_id == source_id, Member.universe_id == universe_id)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def search_members(
    session: AsyncSession, universe_id: uuid.UUID, q: str
) -> list[Member]:
    pattern = f"%{q}%"
    alias_match = select(MemberAlias.member_id).where(MemberAlias.alias.ilike(pattern))
    result = await session.execute(
        select(Member).where(
            Member.universe_id == universe_id,
            Member.nickname.ilike(pattern)
            | Member.legal_name.ilike(pattern)
            | sa.cast(Member.aliases, sa.Text).ilike(pattern)
            | Member.id.in_(alias_match),
        ).distinct()
    )
    return result.scalars().all()


async def list_member_aliases(
    session: AsyncSession, member_id: uuid.UUID
) -> list[MemberAlias]:
    result = await session.execute(
        select(MemberAlias)
        .where(MemberAlias.member_id == member_id)
        .order_by(MemberAlias.created_at)
    )
    return result.scalars().all()


async def create_member_alias(
    session: AsyncSession, member_id: uuid.UUID, data: MemberAliasCreate
) -> MemberAlias:
    obj = MemberAlias(
        member_id=member_id,
        alias=data.alias,
        from_date=_fuzzy_to_dict(data.from_date),
        until_date=_fuzzy_to_dict(data.until_date),
        source_id=data.source_id,
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_member_alias(
    session: AsyncSession, alias_id: uuid.UUID, member_id: uuid.UUID
) -> bool:
    result = await session.execute(
        select(MemberAlias).where(
            MemberAlias.id == alias_id,
            MemberAlias.member_id == member_id,
        )
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        return False
    await session.delete(obj)
    await session.commit()
    return True


async def get_member_stats(session: AsyncSession, member_id: uuid.UUID) -> dict | None:
    try:
        result = await session.execute(
            text("SELECT * FROM member_stats WHERE member_id = :mid"),
            {"mid": member_id},
        )
        row = result.mappings().one_or_none()
        if row:
            return dict(row)
    except Exception:
        await session.rollback()
    return {
        "member_id": member_id,
        "shootings": 0,
        "assists": 0,
        "kills": 0,
        "times_shot_survived": 0,
    }


async def list_member_incarcerations(
    session: AsyncSession, member_id: uuid.UUID
) -> list[MemberIncarceration]:
    result = await session.execute(
        select(MemberIncarceration)
        .where(MemberIncarceration.member_id == member_id)
        .order_by(MemberIncarceration.created_at)
    )
    return result.scalars().all()


async def create_member_incarceration(
    session: AsyncSession, member_id: uuid.UUID, data: MemberIncarcerationCreate
) -> MemberIncarceration:
    obj = MemberIncarceration(
        member_id=member_id,
        from_date=_fuzzy_to_dict(data.from_date),
        to_date=_fuzzy_to_dict(data.to_date),
        facility=data.facility,
        case_id=data.case_id,
        notes=data.notes,
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def update_member_incarceration(
    session: AsyncSession, spell_id: uuid.UUID, member_id: uuid.UUID, data: MemberIncarcerationUpdate
) -> MemberIncarceration | None:
    result = await session.execute(
        select(MemberIncarceration).where(
            MemberIncarceration.id == spell_id,
            MemberIncarceration.member_id == member_id,
        )
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        return None
    for field in ("facility", "case_id", "notes"):
        v = getattr(data, field)
        if v is not None:
            setattr(obj, field, v)
    obj.from_date = _fuzzy_to_dict(data.from_date)
    obj.to_date = _fuzzy_to_dict(data.to_date)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_member_incarceration(
    session: AsyncSession, spell_id: uuid.UUID, member_id: uuid.UUID
) -> bool:
    result = await session.execute(
        select(MemberIncarceration).where(
            MemberIncarceration.id == spell_id,
            MemberIncarceration.member_id == member_id,
        )
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        return False
    await session.delete(obj)
    await session.commit()
    return True
