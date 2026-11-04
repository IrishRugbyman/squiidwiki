import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.core.enums import (
    IncidentType,
    MemberStatus,
    ParticipantOutcome,
    ParticipantRole,
)
from app.schemas.citation import CitationRead
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
    # The member's own universe, which may not be the incident's: a Michigan
    # member can take part in an Ohio incident. His page link is built from it.
    member_universe_slug: Optional[str] = None
    # Also filled by the detail endpoint, so the page draws each participant
    # (photo, status, set) without downloading the whole universe's members.
    member_status: Optional[MemberStatus] = None
    member_photo_url: Optional[str] = None
    # The member's current set: primary when there is one. Membership is not
    # dated to the incident, so this is who they run with now.
    set_id: Optional[uuid.UUID] = None
    set_name: Optional[str] = None
    set_slug: Optional[str] = None


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


def _once_each(items: list | None, key: str, what: str) -> list | None:
    """Refuse a list naming the same member (or set) twice.

    incident_participant is keyed on (incident_id, member_id) and
    incident_set_participant on (incident_id, set_id): one role and one
    outcome each. A second row for the same one is bad input, which the
    database would only report as a primary-key violation (a 500).
    """
    if not items:
        return items
    seen: set = set()
    twice: list[str] = []
    for item in items:
        value = getattr(item, key)
        if value in seen and str(value) not in twice:
            twice.append(str(value))
        seen.add(value)
    if twice:
        raise ValueError(f"{what} listed more than once: {', '.join(twice)}")
    return items


class _ParticipantLists(BaseModel):
    @field_validator("participants", check_fields=False)
    @classmethod
    def _members_once(cls, v):
        return _once_each(v, "member_id", "member")

    @field_validator("set_participants", check_fields=False)
    @classmethod
    def _sets_once(cls, v):
        return _once_each(v, "set_id", "set")


class IncidentCreate(_ParticipantLists):
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


class IncidentUpdate(_ParticipantLists):
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
    universe_slug: Optional[str] = None


class IncidentReadDetail(IncidentRead):
    participants: list[ParticipantRead]
    set_participants: list[SetParticipantRead]
    citations: list[CitationRead] = []


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
    # Where the incident's page lives. A member's or set's list can hold
    # incidents from another universe, so a link cannot assume the current one.
    universe_slug: Optional[str] = None
    victim_names: list[str] = []
    shooter_names: list[str] = []
    # The role held by the member this list was filtered on, when it was. A member's
    # own page otherwise shows an incident with no hint of what he did in it, so a
    # murder he assisted reads exactly like one he committed.
    viewer_role: Optional[ParticipantRole] = None
    viewer_outcome: Optional[ParticipantOutcome] = None
