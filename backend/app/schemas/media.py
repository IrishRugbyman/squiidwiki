import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.core.enums import MediaKind


class MediaUpdate(BaseModel):
    caption: Optional[str] = None
    is_primary: Optional[bool] = None


class MediaRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    member_id: Optional[uuid.UUID]
    incident_id: Optional[uuid.UUID]
    source_id: Optional[uuid.UUID]
    set_id: Optional[uuid.UUID]
    alliance_id: Optional[uuid.UUID]
    kind: MediaKind
    r2_key: Optional[str]
    thumb_r2_key: Optional[str]
    external_url: Optional[str]
    original_filename: Optional[str]
    content_type: Optional[str]
    size_bytes: Optional[int]
    width: Optional[int]
    height: Optional[int]
    caption: Optional[str]
    is_primary: bool
    created_at: datetime


class MediaReadWithUrls(MediaRead):
    """List/detail variant that includes signed GET URLs for the original and
    thumbnail. The router fills these in at response time so the frontend
    can render images directly without a per-tile round trip."""
    url: Optional[str] = None
    thumb_url: Optional[str] = None
