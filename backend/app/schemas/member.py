import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, computed_field

from app.core.enums import MemberStatus
from app.schemas.common import FuzzyDateField


class MemberCreate(BaseModel):
    universe_id: uuid.UUID
    nickname: Optional[str] = None
    legal_name: Optional[str] = None
    nickname_unknown: bool = False
    aliases: Optional[list[str]] = None
    biography: str = ""
    photo_url: Optional[str] = None
    set_id: Optional[uuid.UUID] = None
    alliance_id: Optional[uuid.UUID] = None
    status: MemberStatus = MemberStatus.UNKNOWN
    dob: FuzzyDateField = None
    date_of_death: FuzzyDateField = None
    release_date: FuzzyDateField = None
    family: Optional[dict[str, Any]] = None
    social_media: Optional[dict[str, Any]] = None
    source_ids: list[uuid.UUID] = []


class MemberUpdate(BaseModel):
    nickname: Optional[str] = None
    legal_name: Optional[str] = None
    nickname_unknown: Optional[bool] = None
    aliases: Optional[list[str]] = None
    biography: Optional[str] = None
    photo_url: Optional[str] = None
    set_id: Optional[uuid.UUID] = None
    alliance_id: Optional[uuid.UUID] = None
    status: Optional[MemberStatus] = None
    dob: FuzzyDateField = None
    date_of_death: FuzzyDateField = None
    release_date: FuzzyDateField = None
    family: Optional[dict[str, Any]] = None
    social_media: Optional[dict[str, Any]] = None
    source_ids: Optional[list[uuid.UUID]] = None


class MemberRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    nickname: Optional[str]
    legal_name: Optional[str]
    nickname_unknown: bool
    aliases: Optional[list[str]]
    biography: str
    photo_url: Optional[str]
    set_id: Optional[uuid.UUID]
    alliance_id: Optional[uuid.UUID]
    status: MemberStatus
    dob: FuzzyDateField
    date_of_death: FuzzyDateField
    release_date: FuzzyDateField
    family: Optional[dict[str, Any]]
    social_media: Optional[dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    display_name: str


class MemberReadDetail(MemberRead):
    source_ids: list[uuid.UUID]


class MemberListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    display_name: str
    status: MemberStatus
    set_id: Optional[uuid.UUID]
    universe_id: uuid.UUID
    slug: Optional[str] = None
    photo_url: Optional[str] = None
    aliases: Optional[list[str]] = None
    date_of_death: FuzzyDateField = None


class MemberStats(BaseModel):
    member_id: uuid.UUID
    shootings: int
    assists: int
    kills: int
    times_shot_survived: int
