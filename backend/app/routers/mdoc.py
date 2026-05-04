from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.core.database import get_session
from app.crud import media as media_crud
from app.schemas.mdoc import (
    MdocLookupRequest,
    MdocPhotoImportRequest,
    MdocProfileResponse,
)
from app.schemas.media import MediaReadWithUrls
from app.services.mdoc import (
    MdocFetchError,
    MdocParseError,
    fetch_mdoc_image,
    fetch_mdoc_profile,
)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_PHOTO_BYTES = 10 * 1024 * 1024

router = APIRouter(prefix="/mdoc", tags=["mdoc"])


@router.post("/lookup", response_model=MdocProfileResponse)
async def lookup_mdoc(body: MdocLookupRequest, _: CurrentUser):
    try:
        profile = await fetch_mdoc_profile(body.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except MdocFetchError as e:
        raise HTTPException(status_code=502, detail=f"Couldn't fetch MDOC page: {e}")
    except MdocParseError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return MdocProfileResponse(
        legal_name=profile.legal_name,
        dob=profile.dob,
        earliest_release_date=profile.earliest_release_date,
        max_discharge_date=profile.max_discharge_date,
        facility=profile.facility,
        photo_url=profile.photo_url,
    )


@router.post("/import-photo", response_model=MediaReadWithUrls, status_code=201)
async def import_mdoc_photo(
    body: MdocPhotoImportRequest,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    try:
        file_bytes, content_type = await fetch_mdoc_image(body.photo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except MdocFetchError as e:
        raise HTTPException(status_code=502, detail=f"Couldn't fetch MDOC photo: {e}")

    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported photo content-type: {content_type}")
    if not file_bytes:
        raise HTTPException(status_code=502, detail="MDOC photo response was empty")
    if len(file_bytes) > MAX_PHOTO_BYTES:
        raise HTTPException(status_code=413, detail=f"MDOC photo exceeds {MAX_PHOTO_BYTES} byte limit")

    obj = await media_crud.create_media(
        session,
        universe_id=body.universe_id,
        member_id=body.member_id,
        file_bytes=file_bytes,
        original_filename="mdoc-photo.jpg",
        content_type=content_type,
        caption="Imported from MDOC OTIS",
        actor_id=current_user.id,
    )
    # Reuse the same signed-URL helper used by the media router.
    from app.routers.media import _attach_signed_urls
    return await _attach_signed_urls(obj)
