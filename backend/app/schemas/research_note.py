import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

from app.core.enums import NoteKind
from app.schemas.common import refuse_null

PinKind = Literal["member", "set", "incident", "alliance"]


class PinRef(BaseModel):
    kind: PinKind
    id: uuid.UUID


class PinRead(BaseModel):
    kind: PinKind
    id: uuid.UUID
    # None for incidents, which have no slug.
    slug: Optional[str] = None
    # Display name; for an incident, a label from its date and location.
    name: str


class ResearchNoteCreate(BaseModel):
    universe_id: uuid.UUID
    title: str
    content: str = ""
    kind: NoteKind = NoteKind.INBOX
    pins: list[PinRef] = []


class ResearchNoteUpdate(BaseModel):
    _required = refuse_null("title", "content", "kind")
    title: Optional[str] = None
    content: Optional[str] = None
    kind: Optional[NoteKind] = None
    # When present, replaces the whole list of pins.
    pins: Optional[list[PinRef]] = None


class ResearchNoteRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    title: str
    content: str
    kind: NoteKind
    pins: list[PinRead] = []
    created_at: datetime
    updated_at: datetime


class ResearchNoteListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    content: str  # full content; client truncates to a preview
    kind: NoteKind
    pins: list[PinRead] = []
    updated_at: datetime
