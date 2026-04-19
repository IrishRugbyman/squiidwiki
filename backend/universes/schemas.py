from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from backend.database.models import UniverseRole


class UniverseCreate(BaseModel):
    name: str
    slug: str


class UniverseUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None


class UniverseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    created_at: Optional[datetime] = None


class GrantAccessRequest(BaseModel):
    user_id: int
    role: UniverseRole = UniverseRole.VIEWER


class UniverseAccessResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    universe_id: int
    role: UniverseRole
