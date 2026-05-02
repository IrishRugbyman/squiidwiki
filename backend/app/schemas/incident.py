import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.core.enums import IncidentType, ParticipantOutcome, ParticipantRole
from app.schemas.common import FuzzyDateField


class ParticipantCreate(BaseModel):
    member_id: uuid.UUID
    role: ParticipantRole
    outcome: ParticipantOutcome = ParticipantOutcome.UNKNOWN
    notes: Optional[str] = None


class ParticipantRead(BaseModel):
    model_config = {"from_attributes": True}

    member_id: uuid.UUID
    role: ParticipantRole
    outcome: ParticipantOutcome
    notes: Optional[str]


class SetParticipantCreate(BaseModel):
    set_id: uuid.UUID
    role: ParticipantRole
    outcome: ParticipantOutcome = ParticipantOutcome.UNKNOWN
    notes: Optional[str] = None


class SetParticipantRead(BaseModel):
    model_config = {"from_attributes": True}

    set_id: uuid.UUID
    role: ParticipantRole
    outcome: ParticipantOutcome
    notes: Optional[str]


class IncidentCreate(BaseModel):
    universe_id: uuid.UUID
    type: IncidentType
    date: FuzzyDateField = None
    municipality_id: Optional[uuid.UUID] = None
    location_text: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    narrative: Optional[str] = None
    verified: bool = False
    participants: list[ParticipantCreate] = []
    set_participants: list[SetParticipantCreate] = []
    source_ids: list[uuid.UUID] = []


class IncidentUpdate(BaseModel):
    type: Optional[IncidentType] = None
    date: FuzzyDateField = None
    municipality_id: Optional[uuid.UUID] = None
    location_text: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    narrative: Optional[str] = None
    verified: Optional[bool] = None
    participants: Optional[list[ParticipantCreate]] = None
    set_participants: Optional[list[SetParticipantCreate]] = None
    source_ids: Optional[list[uuid.UUID]] = None


class IncidentRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    type: IncidentType
    date: FuzzyDateField
    municipality_id: Optional[uuid.UUID]
    location_text: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    narrative: Optional[str]
    verified: bool
    created_at: datetime
    updated_at: datetime


class IncidentReadDetail(IncidentRead):
    participants: list[ParticipantRead]
    set_participants: list[SetParticipantRead]
    source_ids: list[uuid.UUID]


class IncidentListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    type: IncidentType
    date: FuzzyDateField
    municipality_id: Optional[uuid.UUID]
    lat: Optional[float]
    lng: Optional[float]
    verified: bool
    universe_id: uuid.UUID
    victim_names: list[str] = []
