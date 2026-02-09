"""Incident schemas."""
from pydantic import BaseModel, field_validator
from typing import Optional, List
from app.models.incident import IncidentType, ParticipantRole, VictimOutcome


class IncidentParticipantBase(BaseModel):
    """Base incident participant schema."""
    member_id: str
    role: ParticipantRole
    outcome: Optional[VictimOutcome] = None
    notes: Optional[str] = None
    
    @field_validator('outcome')
    @classmethod
    def validate_outcome(cls, v, info):
        """Outcome required for victims."""
        role = info.data.get('role')
        if role == ParticipantRole.VICTIM and v is None:
            raise ValueError("Outcome is required for victims")
        if role != ParticipantRole.VICTIM and v is not None:
            raise ValueError("Outcome should only be set for victims")
        return v


class IncidentParticipantCreate(IncidentParticipantBase):
    """Schema for creating an incident participant."""
    pass


class IncidentParticipantRead(IncidentParticipantBase):
    """Schema for reading an incident participant."""
    id: str
    incident_id: str
    
    class Config:
        from_attributes = True


class IncidentBase(BaseModel):
    """Base incident schema."""
    type: IncidentType
    location: Optional[str] = None
    description: Optional[str] = None


class IncidentCreate(IncidentBase):
    """Schema for creating an incident."""
    date_year: Optional[int] = None
    date_month: Optional[int] = None
    date_day: Optional[int] = None
    participants: List[IncidentParticipantCreate] = []


class IncidentUpdate(BaseModel):
    """Schema for updating an incident."""
    type: Optional[IncidentType] = None
    location: Optional[str] = None
    description: Optional[str] = None
    date_year: Optional[int] = None
    date_month: Optional[int] = None
    date_day: Optional[int] = None


class IncidentRead(IncidentBase):
    """Schema for reading an incident."""
    id: str
    date_year: Optional[int] = None
    date_month: Optional[int] = None
    date_day: Optional[int] = None
    
    class Config:
        from_attributes = True
