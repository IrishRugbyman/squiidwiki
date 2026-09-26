import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, model_validator

from app.core.enums import AllianceStatus, SetRelationshipType
from app.schemas.common import FuzzyDateField


class AllianceCreate(BaseModel):
    universe_id: uuid.UUID
    name: str
    aliases: Optional[list[str]] = None
    description: Optional[str] = None
    status: AllianceStatus = AllianceStatus.ACTIVE
    gang_id: Optional[uuid.UUID] = None
    founded_at: FuzzyDateField = None
    territory_ids: list[uuid.UUID] = []
    set_ids: list[uuid.UUID] = []


class AllianceUpdate(BaseModel):
    name: Optional[str] = None
    aliases: Optional[list[str]] = None
    description: Optional[str] = None
    status: Optional[AllianceStatus] = None
    gang_id: Optional[uuid.UUID] = None
    founded_at: FuzzyDateField = None
    territory_ids: Optional[list[uuid.UUID]] = None
    set_ids: Optional[list[uuid.UUID]] = None


class AllianceRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    name: str
    slug: Optional[str] = None
    aliases: Optional[list[str]] = None
    description: Optional[str]
    status: AllianceStatus
    gang_id: Optional[uuid.UUID] = None
    founded_at: FuzzyDateField
    created_at: datetime
    updated_at: datetime
    primary_photo_url: Optional[str] = None
    primary_photo_thumb_url: Optional[str] = None


class AllianceReadDetail(AllianceRead):
    territory_ids: list[uuid.UUID]
    set_ids: list[uuid.UUID]


class AllianceListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    aliases: Optional[list[str]] = None
    status: AllianceStatus
    gang_id: Optional[uuid.UUID] = None
    universe_id: uuid.UUID
    slug: Optional[str] = None
    primary_photo_url: Optional[str] = None
    primary_photo_thumb_url: Optional[str] = None
    # Filled on list rows only (crud.attach_alliance_list_stats); zero elsewhere.
    set_count: int = 0
    member_count: int = 0
    gang_name: Optional[str] = None
    gang_color: Optional[str] = None


class AllianceRelationshipCreate(BaseModel):
    """Open a link from this alliance to another alliance or to one set.

    Exactly one of the two targets. A set that belongs to this alliance is
    refused: its ties to its own alliance are what membership already says.
    """

    target_alliance_id: Optional[uuid.UUID] = None
    target_set_id: Optional[uuid.UUID] = None
    type: SetRelationshipType
    # Null is not the same claim as a dated start: it reads as "for as long as
    # anyone recorded", so set it whenever the date is known.
    from_date: FuzzyDateField = None

    @model_validator(mode="after")
    def _one_target(self) -> "AllianceRelationshipCreate":
        if (self.target_alliance_id is None) == (self.target_set_id is None):
            raise ValueError("Give exactly one of target_alliance_id and target_set_id")
        return self


class AllianceRelationshipEnd(BaseModel):
    """Close a relationship spell as of a date."""

    until_date: FuzzyDateField = None


class AllianceRelationshipItem(BaseModel):
    """One alliance-level link, read from the point of view of one entity.

    `other_*` is the far side. `via_alliance_*` is set only when a set reads a
    link held by its alliance rather than by the set itself: the set is at war
    because its alliance is.
    """

    id: uuid.UUID
    type: SetRelationshipType
    other_kind: Literal["alliance", "set"]
    other_id: uuid.UUID
    other_name: str
    other_slug: Optional[str] = None
    via_alliance_id: Optional[uuid.UUID] = None
    via_alliance_name: Optional[str] = None
    via_alliance_slug: Optional[str] = None
    from_date: Optional[dict[str, Any]] = None
    until_date: Optional[dict[str, Any]] = None
    is_current: bool
