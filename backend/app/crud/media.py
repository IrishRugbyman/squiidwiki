import logging
import uuid
from io import BytesIO

from PIL import Image
from sqlalchemy import case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core import storage
from app.core.database import get_db_mode
from app.core.enums import MediaKind
from app.core.errors import ApiError
from app.models.alliance import Alliance
from app.models.gang_set import GangSet
from app.models.incident import Incident
from app.models.media import Media, MediaMember
from app.models.member import Member
from app.models.municipality import Municipality
from app.models.rap_group import RapGroup
from app.models.source import Source
from app.schemas.media import MediaOwner, MediaPerson, MediaPersonInput, MediaUpdate

logger = logging.getLogger(__name__)

THUMB_MAX_WIDTH = 400
THUMB_QUALITY = 85


# The entity a media row attaches to, as (type name, column). Exactly one of
# these columns is non-null on every row (CHECK media_attaches_to_exactly_one_entity).
_ENTITY_COL = {
    "member": Media.member_id,
    "incident": Media.incident_id,
    "source": Media.source_id,
    "set": Media.set_id,
    "alliance": Media.alliance_id,
    "rap_group": Media.rap_group_id,
    "municipality": Media.municipality_id,
}
ENTITY_FIELDS = tuple(f"{t}_id" for t in _ENTITY_COL)


def _ensure_exactly_one(**ids: uuid.UUID | None) -> tuple[str, uuid.UUID]:
    """The (entity type, id) that `ids` names, or ValueError unless exactly one is set."""
    given = [(f.removesuffix("_id"), v) for f, v in ids.items() if v is not None]
    if len(given) != 1:
        raise ValueError(f"Exactly one of {', '.join(ENTITY_FIELDS)} must be set")
    return given[0]


def _entity_filter(entity_type: str, entity_id: uuid.UUID):
    return _ENTITY_COL[entity_type] == entity_id


def _entity_of(media: Media) -> tuple[str, uuid.UUID]:
    return _ensure_exactly_one(**{f: getattr(media, f) for f in ENTITY_FIELDS})


def _make_thumb(file_bytes: bytes) -> bytes:
    img = Image.open(BytesIO(file_bytes))
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGB")
    if img.width > THUMB_MAX_WIDTH:
        ratio = THUMB_MAX_WIDTH / img.width
        new_size = (THUMB_MAX_WIDTH, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=THUMB_QUALITY, optimize=True)
    return buf.getvalue()


def _image_dimensions(file_bytes: bytes) -> tuple[int, int]:
    img = Image.open(BytesIO(file_bytes))
    return img.size  # (width, height)


def _ext_from_content_type(content_type: str) -> str:
    return {
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/gif": "gif",
    }.get(content_type.lower(), "bin")


async def _existing_primary(
    session: AsyncSession, entity_type: str, entity_id: uuid.UUID
) -> Media | None:
    result = await session.execute(
        select(Media).where(
            _entity_filter(entity_type, entity_id),
            Media.is_primary == True,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def create_media(
    session: AsyncSession,
    *,
    universe_id: uuid.UUID,
    member_id: uuid.UUID | None = None,
    incident_id: uuid.UUID | None = None,
    source_id: uuid.UUID | None = None,
    set_id: uuid.UUID | None = None,
    alliance_id: uuid.UUID | None = None,
    rap_group_id: uuid.UUID | None = None,
    municipality_id: uuid.UUID | None = None,
    file_bytes: bytes,
    original_filename: str | None,
    content_type: str,
    caption: str | None,
    actor_id: uuid.UUID,
) -> Media:
    entity_type, entity_id = _ensure_exactly_one(
        member_id=member_id,
        incident_id=incident_id,
        source_id=source_id,
        set_id=set_id,
        alliance_id=alliance_id,
        rap_group_id=rap_group_id,
        municipality_id=municipality_id,
    )

    width, height = _image_dimensions(file_bytes)
    thumb_bytes = _make_thumb(file_bytes)

    media_id = uuid.uuid4()
    # Municipalities are prod-only data, so their photos are too, in any mode.
    env_prefix = "prod" if entity_type == "municipality" else get_db_mode()
    ext = _ext_from_content_type(content_type)
    r2_key = f"{env_prefix}/{entity_type}/{entity_id}/{media_id}.{ext}"
    thumb_r2_key = f"{env_prefix}/{entity_type}/{entity_id}/{media_id}_thumb.jpg"

    await storage.upload_object(r2_key, file_bytes, content_type)
    await storage.upload_object(thumb_r2_key, thumb_bytes, "image/jpeg")

    is_primary = (await _existing_primary(session, entity_type, entity_id)) is None

    obj = Media(
        id=media_id,
        universe_id=universe_id,
        **{f"{entity_type}_id": entity_id},
        kind=MediaKind.R2,
        r2_key=r2_key,
        thumb_r2_key=thumb_r2_key,
        original_filename=original_filename,
        content_type=content_type,
        size_bytes=len(file_bytes),
        width=width,
        height=height,
        caption=caption,
        is_primary=is_primary,
        created_by_id=actor_id,
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def get_media(session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID) -> Media | None:
    result = await session.execute(
        select(Media).where(Media.id == id, Media.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def list_media(
    session: AsyncSession,
    universe_id: uuid.UUID,
    *,
    member_id: uuid.UUID | None = None,
    incident_id: uuid.UUID | None = None,
    source_id: uuid.UUID | None = None,
    set_id: uuid.UUID | None = None,
    alliance_id: uuid.UUID | None = None,
    rap_group_id: uuid.UUID | None = None,
    municipality_id: uuid.UUID | None = None,
) -> list[Media]:
    entity_type, entity_id = _ensure_exactly_one(
        member_id=member_id,
        incident_id=incident_id,
        source_id=source_id,
        set_id=set_id,
        alliance_id=alliance_id,
        rap_group_id=rap_group_id,
        municipality_id=municipality_id,
    )
    result = await session.execute(
        select(Media)
        .where(Media.universe_id == universe_id, _entity_filter(entity_type, entity_id))
        .order_by(Media.is_primary.desc(), Media.created_at.desc())
    )
    return result.scalars().all()


async def update_media(
    session: AsyncSession,
    id: uuid.UUID,
    universe_id: uuid.UUID,
    data: MediaUpdate,
) -> Media | None:
    obj = await get_media(session, id, universe_id)
    if obj is None:
        return None

    dump = data.model_dump(exclude_unset=True)
    if dump.get("is_primary") is True and not obj.is_primary:
        # Demote any existing primary on the same entity in the same tx.
        entity_type, entity_id = _entity_of(obj)
        existing = await _existing_primary(session, entity_type, entity_id)
        if existing is not None and existing.id != obj.id:
            existing.is_primary = False
            session.add(existing)

    for k, v in dump.items():
        setattr(obj, k, v)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_media(session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID) -> bool:
    obj = await get_media(session, id, universe_id)
    if obj is None:
        return False

    was_primary = obj.is_primary
    entity_type, entity_id = _entity_of(obj)

    if obj.kind == MediaKind.R2:
        if obj.r2_key:
            try:
                await storage.delete_object(obj.r2_key)
            except Exception:
                logger.warning(
                    "R2 delete failed for key %s (media %s)", obj.r2_key, id, exc_info=True
                )
        if obj.thumb_r2_key:
            try:
                await storage.delete_object(obj.thumb_r2_key)
            except Exception:
                logger.warning(
                    "R2 delete failed for key %s (media %s)", obj.thumb_r2_key, id, exc_info=True
                )

    await session.delete(obj)
    await session.flush()

    if was_primary:
        # Promote the most recently created remaining row on the same entity.
        result = await session.execute(
            select(Media)
            .where(_entity_filter(entity_type, entity_id))
            .order_by(Media.created_at.desc())
            .limit(1)
        )
        next_primary = result.scalar_one_or_none()
        if next_primary is not None:
            next_primary.is_primary = True
            session.add(next_primary)

    await session.commit()
    return True


async def _attach_photos_generic(
    session: AsyncSession,
    items: list,
    id_col,
    item_id_attr: str,
) -> None:
    if not items:
        return
    ids = [getattr(item, item_id_attr) for item in items]
    result = await session.execute(
        select(Media).where(id_col.in_(ids), Media.is_primary == True)  # noqa: E712
    )
    by_id: dict[uuid.UUID, Media] = {getattr(m, id_col.key): m for m in result.scalars().all()}
    for item in items:
        primary = by_id.get(getattr(item, item_id_attr))
        if primary is None:
            url = thumb = None
        elif primary.kind == MediaKind.EXTERNAL_URL:
            url = thumb = primary.external_url
        else:
            url = await storage.signed_get_url(primary.r2_key) if primary.r2_key else None
            thumb = (
                await storage.signed_get_url(primary.thumb_r2_key) if primary.thumb_r2_key else url
            )
        object.__setattr__(item, "primary_photo_url", url)
        object.__setattr__(item, "primary_photo_thumb_url", thumb)


async def attach_primary_photos_sets(session: AsyncSession, items: list) -> None:
    await _attach_photos_generic(session, items, Media.set_id, "id")


async def attach_primary_photos_alliances(session: AsyncSession, items: list) -> None:
    await _attach_photos_generic(session, items, Media.alliance_id, "id")


async def attach_primary_photos_rap_groups(session: AsyncSession, items: list) -> None:
    await _attach_photos_generic(session, items, Media.rap_group_id, "id")


async def get_primary_media_for_members(
    session: AsyncSession, member_ids: list[uuid.UUID]
) -> dict[uuid.UUID, Media]:
    if not member_ids:
        return {}
    result = await session.execute(
        select(Media).where(
            Media.member_id.in_(member_ids),
            Media.is_primary == True,  # noqa: E712
        )
    )
    return {m.member_id: m for m in result.scalars().all()}


# ── People in a photo ──────────────────────────────────────────────────────


def _person_sort_name():
    """The name a member is listed by: nickname, or legal name when it is unknown."""
    return func.lower(
        case(
            (
                Member.nickname_unknown.is_(False) & Member.nickname.is_not(None),
                Member.nickname,
            ),
            else_=func.coalesce(Member.legal_name, Member.nickname, ""),
        )
    )


async def people_for(
    session: AsyncSession, media_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[MediaPerson]]:
    """The members tagged in each photo, one query for the whole list.

    Ordered by position (null last), then by name, so an unordered photo reads
    alphabetically.
    """
    out: dict[uuid.UUID, list[MediaPerson]] = {mid: [] for mid in media_ids}
    if not media_ids:
        return out
    rows = await session.execute(
        select(MediaMember.media_id, MediaMember.position, Member)
        .join(Member, Member.id == MediaMember.member_id)
        .where(MediaMember.media_id.in_(media_ids))
        .order_by(MediaMember.position.asc().nulls_last(), _person_sort_name(), Member.id)
    )
    for media_id, position, member in rows.all():
        out[media_id].append(
            MediaPerson(
                member_id=member.id,
                slug=member.slug,
                nickname=member.nickname,
                legal_name=member.legal_name,
                display_name=member.display_name,
                position=position,
            )
        )
    return out


async def set_people(
    session: AsyncSession,
    media: Media,
    people: list[MediaPersonInput],
    actor_id: uuid.UUID,
) -> None:
    """Replace the members tagged in `media` with `people`.

    422 on a duplicate, on the photo's own member (the photo is already on his
    page) and on a member that is missing or in another universe. Rows that stay
    are updated in place and only the difference is inserted or deleted, so the
    audit log records what changed rather than a delete-and-recreate.
    """
    ids = [p.member_id for p in people]
    duplicated = sorted({str(i) for i in ids if ids.count(i) > 1})
    if duplicated:
        raise ApiError(
            422, "duplicate_person", "A member can be tagged once per photo.", member_ids=duplicated
        )
    if media.member_id is not None and media.member_id in ids:
        raise ApiError(
            422,
            "person_is_owner",
            "This photo is already on that member's page; it cannot also tag him.",
            member_id=media.member_id,
        )
    if ids:
        found = set(
            (
                await session.execute(
                    select(Member.id).where(
                        Member.id.in_(ids), Member.universe_id == media.universe_id
                    )
                )
            )
            .scalars()
            .all()
        )
        missing = sorted(str(i) for i in ids if i not in found)
        if missing:
            raise ApiError(
                422,
                "person_not_in_universe",
                "Every tagged member must exist in the photo's universe.",
                member_ids=missing,
            )

    existing = {
        r.member_id: r
        for r in (
            await session.execute(select(MediaMember).where(MediaMember.media_id == media.id))
        )
        .scalars()
        .all()
    }
    wanted = {p.member_id: p.position for p in people}
    for member_id, row in existing.items():
        if member_id not in wanted:
            await session.delete(row)
        elif row.position != wanted[member_id]:
            row.position = wanted[member_id]
            session.add(row)
    for member_id, position in wanted.items():
        if member_id not in existing:
            session.add(
                MediaMember(
                    media_id=media.id,
                    member_id=member_id,
                    position=position,
                    created_by_id=actor_id,
                )
            )
    await session.commit()


async def _owner_labels(session: AsyncSession, media: list[Media]) -> dict[uuid.UUID, MediaOwner]:
    """Who each photo belongs to, one query per entity type present."""
    from app.crud.research_note import _incident_label

    out: dict[uuid.UUID, MediaOwner] = {}
    by_type: dict[str, dict[uuid.UUID, list[uuid.UUID]]] = {}
    for m in media:
        entity_type, entity_id = _entity_of(m)
        by_type.setdefault(entity_type, {}).setdefault(entity_id, []).append(m.id)

    models = {
        "member": Member,
        "set": GangSet,
        "incident": Incident,
        "alliance": Alliance,
        "rap_group": RapGroup,
        "municipality": Municipality,
        "source": Source,
    }
    for entity_type, owners in by_type.items():
        model = models[entity_type]
        entities = await session.execute(select(model).where(model.id.in_(list(owners))))
        for e in entities.scalars().all():
            if entity_type == "member":
                name, slug = e.display_name, e.slug
            elif entity_type == "incident":
                name, slug = _incident_label(e), None
            elif entity_type == "municipality":
                name, slug = e.name, None
            elif entity_type == "source":
                name, slug = e.title, None
            else:
                name, slug = e.name, e.slug
            for media_id in owners[e.id]:
                out[media_id] = MediaOwner(type=entity_type, id=e.id, name=name, slug=slug)
    return out


async def list_appearances(
    session: AsyncSession, universe_id: uuid.UUID, member_id: uuid.UUID
) -> list[tuple[Media, MediaOwner]]:
    """Photos `member_id` is tagged in that are not his own, newest first, each with its owner."""
    result = await session.execute(
        select(Media)
        .join(MediaMember, MediaMember.media_id == Media.id)
        .where(
            MediaMember.member_id == member_id,
            Media.universe_id == universe_id,
            Media.member_id.is_distinct_from(member_id),
        )
        .order_by(Media.created_at.desc(), Media.id)
    )
    items = result.scalars().all()
    owners = await _owner_labels(session, items)
    return [(m, owners[m.id]) for m in items if m.id in owners]
