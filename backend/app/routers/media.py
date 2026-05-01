import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.core import storage
from app.core.database import get_session
from app.core.enums import MediaKind
from app.crud import media as crud
from app.models.media import Media
from app.schemas.media import MediaRead, MediaReadWithUrls, MediaUpdate

router = APIRouter(prefix="/media", tags=["media"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


async def _attach_signed_urls(media: Media) -> MediaReadWithUrls:
    base = MediaRead.model_validate(media)
    if media.kind == MediaKind.EXTERNAL_URL:
        return MediaReadWithUrls(
            **base.model_dump(),
            url=media.external_url,
            thumb_url=media.external_url,
        )
    url = await storage.signed_get_url(media.r2_key) if media.r2_key else None
    thumb_url = (
        await storage.signed_get_url(media.thumb_r2_key) if media.thumb_r2_key else url
    )
    return MediaReadWithUrls(**base.model_dump(), url=url, thumb_url=thumb_url)


def _validate_attach_query(
    member_id: Optional[uuid.UUID],
    incident_id: Optional[uuid.UUID],
    source_id: Optional[uuid.UUID],
    set_id: Optional[uuid.UUID],
    alliance_id: Optional[uuid.UUID],
) -> None:
    set_count = sum(x is not None for x in (member_id, incident_id, source_id, set_id, alliance_id))
    if set_count != 1:
        raise HTTPException(
            400, "Exactly one of member_id, incident_id, source_id, set_id, alliance_id must be provided"
        )


@router.post("/", response_model=MediaReadWithUrls, status_code=201)
async def upload_media(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    file: UploadFile = File(...),
    universe_id: uuid.UUID = Form(...),
    member_id: Optional[uuid.UUID] = Form(None),
    incident_id: Optional[uuid.UUID] = Form(None),
    source_id: Optional[uuid.UUID] = Form(None),
    set_id: Optional[uuid.UUID] = Form(None),
    alliance_id: Optional[uuid.UUID] = Form(None),
    caption: Optional[str] = Form(None),
):
    _validate_attach_query(member_id, incident_id, source_id, set_id, alliance_id)

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            400,
            f"Unsupported content type {file.content_type!r}; allowed: {sorted(ALLOWED_CONTENT_TYPES)}",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"File exceeds {MAX_UPLOAD_BYTES} byte limit")
    if not file_bytes:
        raise HTTPException(400, "Empty upload")

    obj = await crud.create_media(
        session,
        universe_id=universe_id,
        member_id=member_id,
        incident_id=incident_id,
        source_id=source_id,
        set_id=set_id,
        alliance_id=alliance_id,
        file_bytes=file_bytes,
        original_filename=file.filename,
        content_type=file.content_type,
        caption=caption,
        actor_id=current_user.id,
    )
    return await _attach_signed_urls(obj)


@router.get("/", response_model=list[MediaReadWithUrls])
async def list_media(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    member_id: Optional[uuid.UUID] = Query(None),
    incident_id: Optional[uuid.UUID] = Query(None),
    source_id: Optional[uuid.UUID] = Query(None),
    set_id: Optional[uuid.UUID] = Query(None),
    alliance_id: Optional[uuid.UUID] = Query(None),
):
    _validate_attach_query(member_id, incident_id, source_id, set_id, alliance_id)
    items = await crud.list_media(
        session,
        universe_id,
        member_id=member_id,
        incident_id=incident_id,
        source_id=source_id,
        set_id=set_id,
        alliance_id=alliance_id,
    )
    return [await _attach_signed_urls(m) for m in items]


@router.get("/{id}", response_model=MediaReadWithUrls)
async def get_media(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_media(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    return await _attach_signed_urls(obj)


@router.patch("/{id}", response_model=MediaReadWithUrls)
async def update_media(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    data: MediaUpdate,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.update_media(session, id, universe_id, data)
    if obj is None:
        raise HTTPException(404)
    return await _attach_signed_urls(obj)


@router.delete("/{id}", status_code=204)
async def delete_media(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    ok = await crud.delete_media(session, id, universe_id)
    if not ok:
        raise HTTPException(404)
