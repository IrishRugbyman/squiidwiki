from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime


class AllianceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class AllianceOption(BaseModel):
    """Schema for Alliance id and name only (for dropdowns/options)"""
    id: int
    name: str


class AllianceBase(BaseModel):
    """Base schema for Alliance with common attributes"""
    name: str
    description: Optional[str] = None
    status: Optional[str] = "active"


class AllianceCreate(AllianceBase):
    """Schema for creating an Alliance"""
    set_ids: Optional[List[int]] = None


class AllianceUpdate(BaseModel):
    """Schema for updating an Alliance"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    set_ids: Optional[List[int]] = None


class Alliance(AllianceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    sets: List["SetInAlliance"] = []

    class Config:
        from_attributes = True


class SetInAlliance(BaseModel):
    """Schema for Set information within an Alliance"""
    id: int
    name: str
    
    class Config:
        from_attributes = True


class AllianceResponse(AllianceBase):
    """Schema for Alliance responses"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    sets: List[SetInAlliance] = []
    
    class Config:
        from_attributes = True


class AllianceListResponse(BaseModel):
    alliances: List[Alliance]
    total: int = Field(..., description="Total number of alliances")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of alliances per page")
    pages: int = Field(..., description="Total number of pages")

# Update forward references
Alliance.update_forward_refs() 