import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, computed_field

from app.core.enums import MemberStatus, SetRank
from app.schemas.common import FuzzyDateField


class MemberCreate(BaseModel):
    universe_id: uuid.UUID
    nickname: Optional[str] = None
    legal_name: Optional[str] = None
    nickname_unknown: bool = False
    aliases: Optional[list[str]] = None
    biography: str = ""
    set_id: Optional[uuid.UUID] = None
    set_rank: Optional[SetRank] = None
    alliance_id: Optional[uuid.UUID] = None
    gang_id: Optional[uuid.UUID] = None
    status: MemberStatus = MemberStatus.UNKNOWN
    dob: FuzzyDateField = None
    date_of_death: FuzzyDateField = None
    family: Optional[dict[str, Any]] = None
    social_media: Optional[dict[str, Any]] = None
    death_incident_id: Optional[uuid.UUID] = None
    source_ids: list[uuid.UUID] = []


class MemberUpdate(BaseModel):
    nickname: Optional[str] = None
    legal_name: Optional[str] = None
    nickname_unknown: Optional[bool] = None
    aliases: Optional[list[str]] = None
    biography: Optional[str] = None
    set_id: Optional[uuid.UUID] = None
    set_rank: Optional[SetRank] = None
    alliance_id: Optional[uuid.UUID] = None
    gang_id: Optional[uuid.UUID] = None
    status: Optional[MemberStatus] = None
    dob: FuzzyDateField = None
    date_of_death: FuzzyDateField = None
    family: Optional[dict[str, Any]] = None
    social_media: Optional[dict[str, Any]] = None
    death_incident_id: Optional[uuid.UUID] = None
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
    set_id: Optional[uuid.UUID]
    set_rank: Optional[SetRank] = None
    alliance_id: Optional[uuid.UUID]
    gang_id: Optional[uuid.UUID] = None
    status: MemberStatus
    dob: FuzzyDateField
    date_of_death: FuzzyDateField
    family: Optional[dict[str, Any]]
    social_media: Optional[dict[str, Any]]
    death_incident_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime
    display_name: str
    primary_photo_url: Optional[str] = None
    primary_photo_thumb_url: Optional[str] = None


class MemberKilledInSummary(BaseModel):
    incident_id: uuid.UUID
    type: str
    date: FuzzyDateField = None
    municipality_id: Optional[uuid.UUID] = None
    municipality_name: Optional[str] = None


class MemberReadDetail(MemberRead):
    source_ids: list[uuid.UUID]
    set_name: Optional[str] = None
    set_slug: Optional[str] = None
    alliance_name: Optional[str] = None
    alliance_slug: Optional[str] = None
    aliases_detail: list["MemberAliasRead"] = []
    incarcerations: list["MemberIncarcerationRead"] = []
    stats: Optional["MemberStats"] = None
    killed_in: Optional[MemberKilledInSummary] = None


class MemberListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    display_name: str
    status: MemberStatus
    set_id: Optional[uuid.UUID]
    set_rank: Optional[SetRank] = None
    alliance_id: Optional[uuid.UUID] = None
    gang_id: Optional[uuid.UUID] = None
    universe_id: uuid.UUID
    slug: Optional[str] = None
    primary_photo_url: Optional[str] = None
    primary_photo_thumb_url: Optional[str] = None
    aliases: Optional[list[str]] = None
    date_of_death: FuzzyDateField = None


class MemberIncarcerationCreate(BaseModel):
    from_date: FuzzyDateField = None
    earliest_release_date: FuzzyDateField = None
    max_discharge_date: FuzzyDateField = None
    life_sentence: bool = False
    facility: Optional[str] = None
    case_id: Optional[str] = None
    notes: Optional[str] = None


class MemberIncarcerationUpdate(BaseModel):
    from_date: FuzzyDateField = None
    earliest_release_date: FuzzyDateField = None
    max_discharge_date: FuzzyDateField = None
    life_sentence: Optional[bool] = None
    facility: Optional[str] = None
    case_id: Optional[str] = None
    notes: Optional[str] = None


class MemberIncarcerationRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    member_id: uuid.UUID
    from_date: FuzzyDateField
    earliest_release_date: FuzzyDateField
    max_discharge_date: FuzzyDateField
    life_sentence: bool
    facility: Optional[str]
    case_id: Optional[str]
    notes: Optional[str]
    created_at: datetime


class MemberReleaseEvent(BaseModel):
    spell_id: uuid.UUID
    member_id: uuid.UUID
    member_display_name: str
    member_slug: Optional[str]
    facility: Optional[str]
    earliest_release_date: FuzzyDateField = None
    max_discharge_date: FuzzyDateField = None
    life_sentence: bool


class MemberAliasCreate(BaseModel):
    alias: str
    from_date: FuzzyDateField = None
    until_date: FuzzyDateField = None
    source_id: Optional[uuid.UUID] = None


class MemberAliasRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    member_id: uuid.UUID
    alias: str
    from_date: FuzzyDateField
    until_date: FuzzyDateField
    source_id: Optional[uuid.UUID]
    created_at: datetime


class MemberStats(BaseModel):
    member_id: uuid.UUID
    shootings: int
    assists: int
    kills: int
    times_shot_survived: int


MemberReadDetail.model_rebuild()
