import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.core.enums import (
    IncidentType,
    MemberStatus,
    ParticipantOutcome,
    ParticipantRole,
    SourceReliability,
)
from app.schemas.common import FuzzyDateField


class ParticipantCreate(BaseModel):
    member_id: uuid.UUID
    role: ParticipantRole
    outcome: ParticipantOutcome = ParticipantOutcome.UNKNOWN
    acquitted: bool = False
    notes: Optional[str] = None


class ParticipantRead(BaseModel):
    model_config = {"from_attributes": True}

    member_id: uuid.UUID
    role: ParticipantRole
    outcome: ParticipantOutcome
    acquitted: bool
    notes: Optional[str]
    # Filled by the detail endpoint so the client never joins against a
    # truncated member dump (4,600+ members; list endpoints cap at 500).
    member_name: Optional[str] = None
    member_slug: Optional[str] = None
    # Also filled by the detail endpoint, so the page draws each participant
    # (photo, status, set) without downloading the whole universe's members.
    member_status: Optional[MemberStatus] = None
    member_photo_url: Optional[str] = None
    # The member's current set: primary when there is one. Membership is not
    # dated to the incident, so this is who they run with now.
    set_id: Optional[uuid.UUID] = None
    set_name: Optional[str] = None
    set_slug: Optional[str] = None


class IncidentSourceBrief(BaseModel):
    """A cited source as the incident page shows it."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    url: str
    publication: Optional[str] = None
    reliability: SourceReliability


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
    set_name: Optional[str] = None
    set_slug: Optional[str] = None


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
    sources: list[IncidentSourceBrief] = []


class IncidentListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    type: IncidentType
    date: FuzzyDateField
    location_text: Optional[str] = None
    municipality_id: Optional[uuid.UUID]
    municipality_name: Optional[str] = None
    lat: Optional[float]
    lng: Optional[float]
    verified: bool
    universe_id: uuid.UUID
    victim_names: list[str] = []
    shooter_names: list[str] = []
    # The role held by the member this list was filtered on, when it was. A member's
    # own page otherwise shows an incident with no hint of what he did in it, so a
    # murder he assisted reads exactly like one he committed.
    viewer_role: Optional[ParticipantRole] = None
    viewer_outcome: Optional[ParticipantOutcome] = None
