"""Member schemas."""
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict
from app.models.member import MemberStatus, AffiliationType


class MemberBase(BaseModel):
    """Base member schema."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    nicknames: List[str] = []
    status: MemberStatus = MemberStatus.UNKNOWN
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    social_media: Optional[Dict[str, str]] = None
    affiliation_type: AffiliationType = AffiliationType.UNKNOWN
    set_id: Optional[str] = None
    alliance_id: Optional[str] = None
    
    @field_validator('first_name')
    @classmethod
    def validate_first_name(cls, v, info):
        """Ensure first_name or nicknames is provided."""
        if not v and not info.data.get('nicknames'):
            raise ValueError("Either first_name or nicknames must be provided")
        return v


class MemberCreate(MemberBase):
    """Schema for creating a member."""
    dob_year: Optional[int] = None
    dob_month: Optional[int] = None
    dob_day: Optional[int] = None
    dod_year: Optional[int] = None
    dod_month: Optional[int] = None
    dod_day: Optional[int] = None
    release_year: Optional[int] = None
    release_month: Optional[int] = None
    release_day: Optional[int] = None


class MemberUpdate(BaseModel):
    """Schema for updating a member."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    nicknames: Optional[List[str]] = None
    status: Optional[MemberStatus] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    social_media: Optional[Dict[str, str]] = None
    affiliation_type: Optional[AffiliationType] = None
    set_id: Optional[str] = None
    alliance_id: Optional[str] = None
    dob_year: Optional[int] = None
    dob_month: Optional[int] = None
    dob_day: Optional[int] = None
    dod_year: Optional[int] = None
    dod_month: Optional[int] = None
    dod_day: Optional[int] = None
    release_year: Optional[int] = None
    release_month: Optional[int] = None
    release_day: Optional[int] = None


class MemberRead(MemberBase):
    """Schema for reading a member."""
    id: str
    dob_year: Optional[int] = None
    dob_month: Optional[int] = None
    dob_day: Optional[int] = None
    dod_year: Optional[int] = None
    dod_month: Optional[int] = None
    dod_day: Optional[int] = None
    release_year: Optional[int] = None
    release_month: Optional[int] = None
    release_day: Optional[int] = None
    
    class Config:
        from_attributes = True
