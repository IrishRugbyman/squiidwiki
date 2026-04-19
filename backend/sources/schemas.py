from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, HttpUrl

from backend.database.models import SourceReliability


class SourceCreate(BaseModel):
    url: str
    title: Optional[str] = None
    publication: Optional[str] = None
    published_at: Optional[dict] = None
    published_at_sortable: Optional[date] = None
    accessed_at: Optional[date] = None
    reliability: SourceReliability = SourceReliability.UNVERIFIED
    archive_url: Optional[str] = None
    universe_id: Optional[int] = None


class SourceUpdate(BaseModel):
    url: Optional[str] = None
    title: Optional[str] = None
    publication: Optional[str] = None
    published_at: Optional[dict] = None
    published_at_sortable: Optional[date] = None
    accessed_at: Optional[date] = None
    reliability: Optional[SourceReliability] = None
    archive_url: Optional[str] = None


class SourceRead(BaseModel):
    id: int
    url: str
    title: Optional[str] = None
    publication: Optional[str] = None
    published_at: Optional[dict] = None
    published_at_sortable: Optional[date] = None
    accessed_at: Optional[date] = None
    reliability: SourceReliability
    archive_url: Optional[str] = None
    universe_id: Optional[int] = None

    model_config = {"from_attributes": True}
