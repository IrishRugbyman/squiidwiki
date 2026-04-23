import uuid
from typing import Optional

from pydantic import BaseModel


class MunicipalityCreate(BaseModel):
    universe_id: uuid.UUID
    name: str
    parent_id: Optional[uuid.UUID] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class MunicipalityUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class MunicipalityRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    name: str
    parent_id: Optional[uuid.UUID]
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class MunicipalityListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    parent_id: Optional[uuid.UUID]
    universe_id: uuid.UUID
    incident_count: int = 0
    child_count: int = 0
    latitude: Optional[float] = None
    longitude: Optional[float] = None
