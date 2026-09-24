import uuid
from typing import Any, Optional

from pydantic import BaseModel


class MunicipalityCreate(BaseModel):
    universe_id: uuid.UUID
    name: str
    parent_id: Optional[uuid.UUID] = None
    geometry: Optional[Any] = None


class MunicipalityUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    geometry: Optional[Any] = None


class MunicipalityRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    name: str
    parent_id: Optional[uuid.UUID]
    geometry: Optional[Any] = None
    incident_count: int = 0
    child_count: int = 0


class MunicipalityListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    parent_id: Optional[uuid.UUID]
    universe_id: uuid.UUID
    incident_count: int = 0
    # Own incidents plus its sub-districts'; equal to incident_count for a district.
    total_incident_count: int = 0
    child_count: int = 0
    # Real sets anchored to it (a city) or claiming it as territory (a district).
    set_count: int = 0
    has_geometry: bool = False
