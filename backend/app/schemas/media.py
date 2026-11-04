import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.core.enums import MediaKind


class MediaUpdate(BaseModel):
    caption: Optional[str] = None
    is_primary: Optional[bool] = None


class MediaPerson(BaseModel):
    """A member who appears in a photo; `position` null means the order is unknown."""

    member_id: uuid.UUID
    slug: Optional[str] = None
    nickname: Optional[str] = None
    legal_name: Optional[str] = None
    # What the UI shows: the nickname, or the legal name when the nickname is unknown.
    display_name: str
    position: Optional[int] = None


class MediaPersonInput(BaseModel):
    member_id: uuid.UUID
    position: Optional[int] = Field(default=None, ge=0)


class MediaPeopleSet(BaseModel):
    """The complete set of members in a photo: it replaces what is on file."""

    universe_id: uuid.UUID
    people: list[MediaPersonInput] = Field(max_length=60)


class MediaRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    member_id: Optional[uuid.UUID]
    incident_id: Optional[uuid.UUID]
    source_id: Optional[uuid.UUID]
    set_id: Optional[uuid.UUID]
    alliance_id: Optional[uuid.UUID]
    rap_group_id: Optional[uuid.UUID] = None
    municipality_id: Optional[uuid.UUID] = None
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
    people: list[MediaPerson] = Field(default_factory=list)


MediaOwnerType = Literal[
    "member", "set", "incident", "alliance", "rap_group", "municipality", "source"
]


class MediaOwner(BaseModel):
    """The entity a photo belongs to, so the UI can link back to its page.

    An incident has no name, so `name` is a label from its date and place;
    incidents, municipalities and sources have no slug.
    """

    type: MediaOwnerType
    id: uuid.UUID
    name: str
    slug: Optional[str] = None


class MediaAppearance(MediaReadWithUrls):
    owner: MediaOwner
