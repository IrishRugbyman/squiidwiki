import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.core.enums import SetRelationshipType, SetStatus


class SetCreate(BaseModel):
    universe_id: uuid.UUID
    name: str
    alias: Optional[str] = None
    bio: Optional[str] = None
    status: SetStatus = SetStatus.ACTIVE
    alliance_id: Optional[uuid.UUID] = None
    founder_id: Optional[uuid.UUID] = None
    territory_ids: list[uuid.UUID] = []
    friend_ids: list[uuid.UUID] = []
    enemy_ids: list[uuid.UUID] = []


class SetUpdate(BaseModel):
    name: Optional[str] = None
    alias: Optional[str] = None
    bio: Optional[str] = None
    status: Optional[SetStatus] = None
    alliance_id: Optional[uuid.UUID] = None
    founder_id: Optional[uuid.UUID] = None
    territory_ids: Optional[list[uuid.UUID]] = None
    friend_ids: Optional[list[uuid.UUID]] = None
    enemy_ids: Optional[list[uuid.UUID]] = None


class SetRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    name: str
    slug: Optional[str]
    alias: Optional[str]
    bio: Optional[str]
    status: SetStatus
    alliance_id: Optional[uuid.UUID]
    founder_id: Optional[uuid.UUID]
    created_at: datetime


class SetReadDetail(SetRead):
    territory_ids: list[uuid.UUID]
    friend_ids: list[uuid.UUID]
    enemy_ids: list[uuid.UUID]


class SetListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: Optional[str]
    status: SetStatus
    universe_id: uuid.UUID
    alliance_id: Optional[uuid.UUID]


class SetRelationshipCreate(BaseModel):
    target_id: uuid.UUID
    type: SetRelationshipType


class SetStats(BaseModel):
    set_id: uuid.UUID
    member_count: int
    dead_members: int
    total_shootings: int
    total_assists: int
    total_kills: int
