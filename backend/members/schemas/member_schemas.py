from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime

class MemberBase(BaseModel):
    """Base schema for Member data with common fields."""
    name: str
    description: Optional[str] = None
    status: str
    release_date: Optional[date] = None
    release_date_approx: Optional[str] = None
    death_date: Optional[date] = None
    death_date_approx: Optional[str] = None


class MemberCreate(MemberBase):
    """Schema for creating a new Member."""
    set_id: Optional[int] = None
    alliance_id: Optional[int] = None


class MemberUpdate(MemberBase):
    """Schema for updating an existing Member."""
    set_id: Optional[int] = None
    alliance_id: Optional[int] = None


class MemberResponse(MemberBase):
    """Schema for Member responses."""
    id: int
    set_id: Optional[int] = None
    alliance_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class MemberDetail(MemberResponse):
    """Detailed Member response including related entities."""
    set_name: Optional[str] = None
    alliance_name: Optional[str] = None
    activities: Optional[Dict[str, List[Dict[str, Any]]]] = Field(default_factory=lambda: {
        "shootings": [],
        "murders": [],
        "assists": []
    })
    
    class Config:
        from_attributes = True 