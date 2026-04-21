import uuid
from typing import Optional

from pydantic import BaseModel


class MunicipalityCreate(BaseModel):
    universe_id: uuid.UUID
    name: str
    parent_id: Optional[uuid.UUID] = None


class MunicipalityUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None


class MunicipalityRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    name: str
    parent_id: Optional[uuid.UUID]


class MunicipalityListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    parent_id: Optional[uuid.UUID]
    universe_id: uuid.UUID
    incident_count: int = 0
    child_count: int = 0
