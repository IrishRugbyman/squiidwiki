import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

from app.core.enums import SourceReliability
from app.schemas.common import FuzzyDateField


class SourceCreate(BaseModel):
    universe_id: uuid.UUID
    url: str
    title: str
    publication: Optional[str] = None
    published_at: FuzzyDateField = None
    accessed_at: Optional[date] = None
    reliability: SourceReliability = SourceReliability.UNVERIFIED
    notes: Optional[str] = None
    archive_url: Optional[str] = None


class SourceUpdate(BaseModel):
    url: Optional[str] = None
    title: Optional[str] = None
    publication: Optional[str] = None
    published_at: FuzzyDateField = None
    accessed_at: Optional[date] = None
    reliability: Optional[SourceReliability] = None
    notes: Optional[str] = None
    archive_url: Optional[str] = None


class SourceRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    url: str
    title: str
    publication: Optional[str]
    published_at: FuzzyDateField
    accessed_at: Optional[date]
    reliability: SourceReliability
    notes: Optional[str]
    archive_url: Optional[str]
    created_at: datetime
    updated_at: datetime


class SourceListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    url: str
    reliability: SourceReliability
