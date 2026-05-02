import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UniverseCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None


class UniverseUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None


class UniverseRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str]
    created_at: datetime


class UniverseListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: str
