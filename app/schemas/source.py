"""Source schemas."""
from pydantic import BaseModel
from typing import Optional
from app.models.source import SourceType
from app.schemas.fuzzy_date import FuzzyDateSchema


class SourceBase(BaseModel):
    """Base source schema."""
    type: SourceType
    title: Optional[str] = None
    url: Optional[str] = None
    notes: Optional[str] = None


class SourceCreate(SourceBase):
    """Schema for creating a source."""
    date_year: Optional[int] = None
    date_month: Optional[int] = None
    date_day: Optional[int] = None


class SourceUpdate(SourceBase):
    """Schema for updating a source."""
    type: Optional[SourceType] = None
    date_year: Optional[int] = None
    date_month: Optional[int] = None
    date_day: Optional[int] = None


class SourceRead(SourceBase):
    """Schema for reading a source."""
    id: str
    date_year: Optional[int] = None
    date_month: Optional[int] = None
    date_day: Optional[int] = None
    
    class Config:
        from_attributes = True
