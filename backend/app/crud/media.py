import uuid
from io import BytesIO
from typing import Optional

from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core import storage
from app.core.database import get_db_mode
from app.core.enums import MediaKind
from app.models.media import Media
from app.schemas.media import MediaUpdate


THUMB_MAX_WIDTH = 400
THUMB_QUALITY = 85


def _ensure_exactly_one(member_id, incident_id, source_id, set_id, alliance_id) -> str:
    set_count = sum(x is not None for x in (member_id, incident_id, source_id, set_id, alliance_id))
    if set_count != 1:
        raise ValueError("Exactly one of member_id, incident_id, source_id, set_id, alliance_id must be set")
    if member_id is not None:
        return "member"
    if incident_id is not None:
        return "incident"
    if source_id is not None:
        return "source"
    if set_id is not None:
        return "set"
    return "alliance"


def _entity_id(media: Media) -> uuid.UUID:
    return media.member_id or media.incident_id or media.source_id or media.set_id or media.alliance_id  # type: ignore[return-value]


_ENTITY_COL = {
    "member": Media.member_id,
    "incident": Media.incident_id,
    "source": Media.source_id,
    "set": Media.set_id,
    "alliance": Media.alliance_id,
}


def _entity_filter(entity_type: str, entity_id: uuid.UUID):
    return _ENTITY_COL[entity_type] == entity_id


def _entity_type_for(media: Media) -> str:
    if media.member_id is not None:
        return "member"
    if media.incident_id is not None:
        return "incident"
    if media.source_id is not None:
        return "source"
    if media.set_id is not None:
        return "set"
    return "alliance"


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
) -> Optional[Media]:
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
    member_id: Optional[uuid.UUID] = None,
    incident_id: Optional[uuid.UUID] = None,
    source_id: Optional[uuid.UUID] = None,
    set_id: Optional[uuid.UUID] = None,
    alliance_id: Optional[uuid.UUID] = None,
    file_bytes: bytes,
    original_filename: Optional[str],
    content_type: str,
    caption: Optional[str],
    actor_id: uuid.UUID,
) -> Media:
    entity_type = _ensure_exactly_one(member_id, incident_id, source_id, set_id, alliance_id)
    entity_id = member_id or incident_id or source_id or set_id or alliance_id

    width, height = _image_dimensions(file_bytes)
    thumb_bytes = _make_thumb(file_bytes)

    media_id = uuid.uuid4()
    env_prefix = get_db_mode()  # "prod" | "test"
    ext = _ext_from_content_type(content_type)
    r2_key = f"{env_prefix}/{entity_type}/{entity_id}/{media_id}.{ext}"
    thumb_r2_key = f"{env_prefix}/{entity_type}/{entity_id}/{media_id}_thumb.jpg"

    await storage.upload_object(r2_key, file_bytes, content_type)
    await storage.upload_object(thumb_r2_key, thumb_bytes, "image/jpeg")

    is_primary = (await _existing_primary(session, entity_type, entity_id)) is None

    obj = Media(
        id=media_id,
        universe_id=universe_id,
        member_id=member_id,
        incident_id=incident_id,
        source_id=source_id,
        set_id=set_id,
        alliance_id=alliance_id,
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


async def get_media(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> Optional[Media]:
    result = await session.execute(
        select(Media).where(Media.id == id, Media.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def list_media(
    session: AsyncSession,
    universe_id: uuid.UUID,
    *,
    member_id: Optional[uuid.UUID] = None,
    incident_id: Optional[uuid.UUID] = None,
    source_id: Optional[uuid.UUID] = None,
    set_id: Optional[uuid.UUID] = None,
    alliance_id: Optional[uuid.UUID] = None,
) -> list[Media]:
    entity_type = _ensure_exactly_one(member_id, incident_id, source_id, set_id, alliance_id)
    entity_id = member_id or incident_id or source_id or set_id or alliance_id
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
) -> Optional[Media]:
    obj = await get_media(session, id, universe_id)
    if obj is None:
        return None

    dump = data.model_dump(exclude_unset=True)
    if dump.get("is_primary") is True and not obj.is_primary:
        # Demote any existing primary on the same entity in the same tx.
        entity_type = _entity_type_for(obj)
        entity_id = _entity_id(obj)
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


async def delete_media(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> bool:
    obj = await get_media(session, id, universe_id)
    if obj is None:
        return False

    was_primary = obj.is_primary
    entity_type = _entity_type_for(obj)
    entity_id = _entity_id(obj)

    if obj.kind == MediaKind.R2:
        if obj.r2_key:
            try:
                await storage.delete_object(obj.r2_key)
            except Exception:
                pass  # don't block deletion of the row on a stale R2 object
        if obj.thumb_r2_key:
            try:
                await storage.delete_object(obj.thumb_r2_key)
            except Exception:
                pass

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
