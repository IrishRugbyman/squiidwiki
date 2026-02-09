"""Alliance schemas."""
from pydantic import BaseModel
from typing import Optional, List
from app.models.alliance import AllianceStatus


class AllianceBase(BaseModel):
    """Base alliance schema."""
    name: str
    status: AllianceStatus = AllianceStatus.ACTIVE
    bio: Optional[str] = None


class AllianceCreate(AllianceBase):
    """Schema for creating an alliance."""
    founded_year: Optional[int] = None
    founded_month: Optional[int] = None
    founded_day: Optional[int] = None


class AllianceUpdate(BaseModel):
    """Schema for updating an alliance."""
    name: Optional[str] = None
    status: Optional[AllianceStatus] = None
    bio: Optional[str] = None
    founded_year: Optional[int] = None
    founded_month: Optional[int] = None
    founded_day: Optional[int] = None


class AllianceRead(AllianceBase):
    """Schema for reading an alliance."""
    id: str
    founded_year: Optional[int] = None
    founded_month: Optional[int] = None
    founded_day: Optional[int] = None
    
    class Config:
        from_attributes = True
