import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GangCreate(BaseModel):
    universe_id: uuid.UUID
    name: str
    aliases: Optional[list[str]] = None
    description: Optional[str] = None


class GangUpdate(BaseModel):
    name: Optional[str] = None
    aliases: Optional[list[str]] = None
    description: Optional[str] = None


class GangRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    name: str
    slug: Optional[str] = None
    aliases: Optional[list[str]] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class GangListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    name: str
    slug: Optional[str] = None
    aliases: Optional[list[str]] = None
    description: Optional[str] = None
