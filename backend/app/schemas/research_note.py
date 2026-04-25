import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ResearchNoteCreate(BaseModel):
    universe_id: uuid.UUID
    title: str
    content: str = ""


class ResearchNoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class ResearchNoteRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    title: str
    content: str
    created_at: datetime
    updated_at: datetime


class ResearchNoteListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    content: str  # full content; client truncates to a preview
    updated_at: datetime
