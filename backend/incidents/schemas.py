from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from backend.database.models import IncidentOutcome, IncidentRole, IncidentType, LocationType


class IncidentParticipantCreate(BaseModel):
    member_id: int
    role: IncidentRole
    outcome: IncidentOutcome = IncidentOutcome.UNKNOWN


class IncidentParticipantRead(BaseModel):
    id: int
    member_id: int
    role: IncidentRole
    outcome: IncidentOutcome

    model_config = {"from_attributes": True}


class IncidentCreate(BaseModel):
    incident_type: IncidentType
    date: Optional[dict] = None
    date_sortable: Optional[date] = None
    location_type: LocationType = LocationType.STREET
    narrative: Optional[str] = None
    verified: bool = False
    universe_id: Optional[int] = None
    participants: List[IncidentParticipantCreate] = []


class IncidentUpdate(BaseModel):
    incident_type: Optional[IncidentType] = None
    date: Optional[dict] = None
    date_sortable: Optional[date] = None
    location_type: Optional[LocationType] = None
    narrative: Optional[str] = None
    verified: Optional[bool] = None


class IncidentRead(BaseModel):
    id: int
    incident_type: IncidentType
    date: Optional[dict] = None
    date_sortable: Optional[date] = None
    location_type: LocationType
    narrative: Optional[str] = None
    verified: bool
    universe_id: Optional[int] = None
    participants: List[IncidentParticipantRead] = []

    model_config = {"from_attributes": True}
