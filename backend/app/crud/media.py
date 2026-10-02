import logging
import uuid
from io import BytesIO

from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core import storage
from app.core.database import get_db_mode
from app.core.enums import MediaKind
from app.models.media import Media
from app.schemas.media import MediaUpdate

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
    municipality_id: uuid.UUID | None = None,
) -> list[Media]:
    entity_type, entity_id = _ensure_exactly_one(
        member_id=member_id,
        incident_id=incident_id,
        source_id=source_id,
        set_id=set_id,
        alliance_id=alliance_id,
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
