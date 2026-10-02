import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core import storage
from app.core.database import get_prod_session, get_session, resolve_prod_universe
from app.core.enums import GlobalRole, MediaKind
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
    thumb_url = await storage.signed_get_url(media.thumb_r2_key) if media.thumb_r2_key else url
    return MediaReadWithUrls(**base.model_dump(), url=url, thumb_url=thumb_url)


def _validate_attach_query(**ids: Optional[uuid.UUID]) -> None:
    if sum(v is not None for v in ids.values()) != 1:
        raise HTTPException(400, f"Exactly one of {', '.join(crud.ENTITY_FIELDS)} must be provided")


async def _scope(
    municipality_id: Optional[uuid.UUID],
    universe_id: uuid.UUID,
    session: AsyncSession,
    prod_session: AsyncSession,
) -> tuple[AsyncSession, uuid.UUID]:
    """The session and universe a media row lives under.

    Municipalities always live in prod (see routers/municipality.py), and a
    photo has to sit in the same database as the row its FK points at, so
    municipality media is read and written through the prod session whatever
    the DB mode.
    """
    if municipality_id is None:
        return session, universe_id
    uid = await resolve_prod_universe(session, prod_session, universe_id)
    if uid is None:
        raise HTTPException(404, f"Universe {universe_id} not found in prod DB")
    return prod_session, uid


async def _find(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    session: AsyncSession,
    prod_session: AsyncSession,
) -> tuple[AsyncSession, uuid.UUID]:
    """Where media row `id` lives: the active DB, or prod for a municipality photo."""
    if await crud.get_media(session, id, universe_id) is not None:
        return session, universe_id
    uid = await resolve_prod_universe(session, prod_session, universe_id)
    if uid is not None:
        obj = await crud.get_media(prod_session, id, uid)
        if obj is not None and obj.municipality_id is not None:
            return prod_session, uid
    raise HTTPException(404)


@router.post("/", response_model=MediaReadWithUrls, status_code=201)
async def upload_media(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    prod_session: Annotated[AsyncSession, Depends(get_prod_session)],
    file: UploadFile = File(...),
    universe_id: uuid.UUID = Form(...),
    member_id: Optional[uuid.UUID] = Form(None),
    incident_id: Optional[uuid.UUID] = Form(None),
    source_id: Optional[uuid.UUID] = Form(None),
    set_id: Optional[uuid.UUID] = Form(None),
    alliance_id: Optional[uuid.UUID] = Form(None),
    municipality_id: Optional[uuid.UUID] = Form(None),
    caption: Optional[str] = Form(None),
):
    ids = dict(
        member_id=member_id,
        incident_id=incident_id,
        source_id=source_id,
        set_id=set_id,
        alliance_id=alliance_id,
        municipality_id=municipality_id,
    )
    _validate_attach_query(**ids)
    session, universe_id = await _scope(municipality_id, universe_id, session, prod_session)

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
        **ids,
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
    prod_session: Annotated[AsyncSession, Depends(get_prod_session)],
    member_id: Optional[uuid.UUID] = Query(None),
    incident_id: Optional[uuid.UUID] = Query(None),
    source_id: Optional[uuid.UUID] = Query(None),
    set_id: Optional[uuid.UUID] = Query(None),
    alliance_id: Optional[uuid.UUID] = Query(None),
    municipality_id: Optional[uuid.UUID] = Query(None),
):
    ids = dict(
        member_id=member_id,
        incident_id=incident_id,
        source_id=source_id,
        set_id=set_id,
        alliance_id=alliance_id,
        municipality_id=municipality_id,
    )
    _validate_attach_query(**ids)
    session, universe_id = await _scope(municipality_id, universe_id, session, prod_session)
    items = await crud.list_media(session, universe_id, **ids)
    return [await _attach_signed_urls(m) for m in items]


@router.get("/{id}", response_model=MediaReadWithUrls)
async def get_media(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    prod_session: Annotated[AsyncSession, Depends(get_prod_session)],
):
    session, universe_id = await _find(id, universe_id, session, prod_session)
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
    prod_session: Annotated[AsyncSession, Depends(get_prod_session)],
):
    session, universe_id = await _find(id, universe_id, session, prod_session)
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
    prod_session: Annotated[AsyncSession, Depends(get_prod_session)],
    __: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    session, universe_id = await _find(id, universe_id, session, prod_session)
    ok = await crud.delete_media(session, id, universe_id)
    if not ok:
        raise HTTPException(404)
