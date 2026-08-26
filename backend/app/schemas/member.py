import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, computed_field, model_validator

from app.core.enums import MemberStatus, SetRank
from app.schemas.common import FuzzyDateField


class MemberSetAffiliationIn(BaseModel):
    """One *current* affiliation. Closing a spell is a separate dated action,
    so there is deliberately no until_date here."""

    set_id: uuid.UUID
    rank: Optional[SetRank] = None
    is_primary: bool = False
    from_date: FuzzyDateField = None


class MemberSetAffiliationOut(BaseModel):
    id: Optional[uuid.UUID] = None
    set_id: uuid.UUID
    set_name: Optional[str] = None
    set_slug: Optional[str] = None
    rank: Optional[SetRank] = None
    is_primary: bool = False
    from_date: Optional[dict[str, Any]] = None
    until_date: Optional[dict[str, Any]] = None

    @computed_field
    @property
    def is_current(self) -> bool:
        return self.until_date is None


class AffiliationEnd(BaseModel):
    """Close an affiliation spell as of a date."""

    until_date: FuzzyDateField = None


class MemberCreate(BaseModel):
    universe_id: uuid.UUID
    nickname: Optional[str] = None
    legal_name: Optional[str] = None
    # The MDOC offender number, when known: OTIS's only stable handle
    # since the rebuilt site gives profiles no URL.
    mdoc_number: Optional[str] = None
    nickname_unknown: bool = False
    is_rapper: bool = False
    aliases: Optional[list[str]] = None
    biography: str = ""
    affiliations: list[MemberSetAffiliationIn] = []
    alliance_id: Optional[uuid.UUID] = None
    gang_id: Optional[uuid.UUID] = None
    status: MemberStatus = MemberStatus.UNKNOWN
    dob: FuzzyDateField = None
    date_of_death: FuzzyDateField = None
    family: Optional[dict[str, Any]] = None
    social_media: Optional[dict[str, Any]] = None
    death_incident_id: Optional[uuid.UUID] = None
    source_ids: list[uuid.UUID] = []

    @model_validator(mode="after")
    def _fix_primary(self) -> "MemberCreate":
        _ensure_single_primary(self.affiliations)
        return self


class MemberUpdate(BaseModel):
    nickname: Optional[str] = None
    legal_name: Optional[str] = None
    mdoc_number: Optional[str] = None
    nickname_unknown: Optional[bool] = None
    is_rapper: Optional[bool] = None
    aliases: Optional[list[str]] = None
    biography: Optional[str] = None
    affiliations: Optional[list[MemberSetAffiliationIn]] = None
    alliance_id: Optional[uuid.UUID] = None
    gang_id: Optional[uuid.UUID] = None
    status: Optional[MemberStatus] = None
    dob: FuzzyDateField = None
    date_of_death: FuzzyDateField = None
    family: Optional[dict[str, Any]] = None
    social_media: Optional[dict[str, Any]] = None
    death_incident_id: Optional[uuid.UUID] = None
    source_ids: Optional[list[uuid.UUID]] = None

    @model_validator(mode="after")
    def _fix_primary(self) -> "MemberUpdate":
        if self.affiliations is not None:
            _ensure_single_primary(self.affiliations)
        return self


def _ensure_single_primary(affiliations: list[MemberSetAffiliationIn]) -> None:
    """Auto-promote first affiliation to primary if none is marked."""
    if not affiliations:
        return
    primaries = [a for a in affiliations if a.is_primary]
    if not primaries:
        affiliations[0].is_primary = True


class MemberRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    nickname: Optional[str]
    legal_name: Optional[str]
    # Defaulted, unlike its neighbours: MemberRead is assembled from dicts in
    # several places, and a required field breaks every one that predates it.
    mdoc_number: Optional[str] = None
    nickname_unknown: bool
    is_rapper: bool = False
    aliases: Optional[list[str]]
    biography: str
    affiliations: list[MemberSetAffiliationOut] = []
    primary_set_id: Optional[uuid.UUID] = None
    primary_set_name: Optional[str] = None
    primary_set_slug: Optional[str] = None
    # The member's own slug, not the set's. Its absence here meant every consumer
    # reading a member through the detail endpoint had to fall back to the UUID for
    # links, while the list endpoint returned it all along.
    slug: Optional[str] = None
    primary_set_rank: Optional[SetRank] = None
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
    affiliations: list[MemberSetAffiliationOut] = []
    primary_set_id: Optional[uuid.UUID] = None
    primary_set_name: Optional[str] = None
    primary_set_slug: Optional[str] = None
    primary_set_rank: Optional[SetRank] = None
    alliance_id: Optional[uuid.UUID] = None
    gang_id: Optional[uuid.UUID] = None
    universe_id: uuid.UUID
    slug: Optional[str] = None
    primary_photo_url: Optional[str] = None
    primary_photo_thumb_url: Optional[str] = None
    aliases: Optional[list[str]] = None
    date_of_death: FuzzyDateField = None
    is_rapper: bool = False


class MemberIncarcerationCreate(BaseModel):
    from_date: FuzzyDateField = None
    # When the spell ended. Set means historical; see the model for why that is
    # not the same field as max_discharge_date.
    to_date: FuzzyDateField = None
    earliest_release_date: FuzzyDateField = None
    max_discharge_date: FuzzyDateField = None
    life_sentence: bool = False
    facility: Optional[str] = None
    case_id: Optional[str] = None
    notes: Optional[str] = None


class MemberIncarcerationUpdate(BaseModel):
    from_date: FuzzyDateField = None
    to_date: FuzzyDateField = None
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
    to_date: FuzzyDateField
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
