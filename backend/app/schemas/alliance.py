import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.core.enums import AllianceStatus
from app.schemas.common import FuzzyDateField


class AllianceCreate(BaseModel):
    universe_id: uuid.UUID
    name: str
    description: Optional[str] = None
    status: AllianceStatus = AllianceStatus.ACTIVE
    founded_at: FuzzyDateField = None
    territory_ids: list[uuid.UUID] = []
    set_ids: list[uuid.UUID] = []


class AllianceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[AllianceStatus] = None
    founded_at: FuzzyDateField = None
    territory_ids: Optional[list[uuid.UUID]] = None
    set_ids: Optional[list[uuid.UUID]] = None


class AllianceRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    name: str
    description: Optional[str]
    status: AllianceStatus
    founded_at: FuzzyDateField
    created_at: datetime


class AllianceReadDetail(AllianceRead):
    territory_ids: list[uuid.UUID]
    set_ids: list[uuid.UUID]


class AllianceListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    status: AllianceStatus
    universe_id: uuid.UUID
