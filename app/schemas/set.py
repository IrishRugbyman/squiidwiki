"""Set schemas."""
from pydantic import BaseModel
from typing import Optional, List
from app.models.set import SetStatus


class SetBase(BaseModel):
    """Base set schema."""
    primary_name: str
    names: List[str] = []
    status: SetStatus = SetStatus.ACTIVE
    territory: Optional[str] = None
    colors: Optional[str] = None
    bio: Optional[str] = None
    alliance_id: Optional[str] = None


class SetCreate(SetBase):
    """Schema for creating a set."""
    founded_year: Optional[int] = None
    founded_month: Optional[int] = None
    founded_day: Optional[int] = None


class SetUpdate(BaseModel):
    """Schema for updating a set."""
    primary_name: Optional[str] = None
    names: Optional[List[str]] = None
    status: Optional[SetStatus] = None
    territory: Optional[str] = None
    colors: Optional[str] = None
    bio: Optional[str] = None
    alliance_id: Optional[str] = None
    founded_year: Optional[int] = None
    founded_month: Optional[int] = None
    founded_day: Optional[int] = None


class SetRead(SetBase):
    """Schema for reading a set."""
    id: str
    founded_year: Optional[int] = None
    founded_month: Optional[int] = None
    founded_day: Optional[int] = None
    
    class Config:
        from_attributes = True
