import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, model_validator

from app.core.enums import AllianceStatus, SetLineageKind, SetRelationshipType
from app.schemas.citation import CitationRead
from app.schemas.common import FuzzyDateField
from app.schemas.gang_set import IncidentsPerYear
from app.schemas.names import (
    NameVariant,
    dedupe_ids,
    derived_name,
    normalize_emojis,
    normalize_variants,
)


class AllianceCreate(BaseModel):
    # A stale field (`aliases`, the single `gang_id`) is refused, not dropped.
    model_config = {"extra": "forbid"}

    universe_id: uuid.UUID
    # Derived from the primary name variant; optional when variants are sent.
    # Sent alone, it becomes the primary variant's `name` slot.
    name: Optional[str] = None
    name_variants: Optional[list[NameVariant]] = None
    emojis: Optional[list[str]] = None
    description: Optional[str] = None
    status: AllianceStatus = AllianceStatus.ACTIVE
    # Every gang the bloc claims, primary first; mirrored into alliance.gang_id.
    gang_ids: list[uuid.UUID] = []
    founder_id: Optional[uuid.UUID] = None
    founded_at: FuzzyDateField = None
    # Cities and areas the bloc operates in.
    territory_ids: list[uuid.UUID] = []
    set_ids: list[uuid.UUID] = []

    @model_validator(mode="after")
    def _normalize(self):
        variants = normalize_variants(self.name_variants)
        if not variants:
            name = (self.name or "").strip()
            if not name:
                raise ValueError("an alliance needs a name or a primary name variant")
            variants = [NameVariant(name=name, is_primary=True)]
        self.name_variants = variants
        self.name = derived_name(self.name, variants, kind="alliance")
        self.emojis = normalize_emojis(self.emojis)
        self.gang_ids = dedupe_ids(self.gang_ids) or []
        return self


class AllianceUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    # Derived from the primary name variant, never set on its own: a rename is
    # a change to name_variants. May be sent alongside them if it agrees.
    name: Optional[str] = None
    name_variants: Optional[list[NameVariant]] = None
    emojis: Optional[list[str]] = None
    description: Optional[str] = None
    status: Optional[AllianceStatus] = None
    # The complete, ordered list of gangs; the first is the primary. [] clears.
    gang_ids: Optional[list[uuid.UUID]] = None
    founder_id: Optional[uuid.UUID] = None
    founded_at: FuzzyDateField = None
    territory_ids: Optional[list[uuid.UUID]] = None
    set_ids: Optional[list[uuid.UUID]] = None

    @model_validator(mode="after")
    def _normalize(self):
        # Only fields the caller sent: reassigning one marks it set and defeats
        # exclude_unset in the CRUD.
        fields_set = self.model_fields_set
        if "name_variants" in fields_set:
            if not self.name_variants:
                raise ValueError(
                    "name_variants cannot be cleared: an alliance needs a primary name"
                )
            self.name_variants = normalize_variants(self.name_variants)
            self.name = derived_name(
                self.name if "name" in fields_set else None, self.name_variants, kind="alliance"
            )
        elif "name" in fields_set:
            raise ValueError(
                "an alliance's name is derived from its primary name variant: "
                "send name_variants to rename it"
            )
        if "emojis" in fields_set:
            self.emojis = normalize_emojis(self.emojis)
        if "gang_ids" in fields_set:
            self.gang_ids = dedupe_ids(self.gang_ids) or []
        return self


class AllianceGangSummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: Optional[str] = None
    color: Optional[str] = None


class AllianceRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    name: str
    slug: Optional[str] = None
    name_variants: Optional[list[NameVariant]] = None
    emojis: Optional[list[str]] = None
    description: Optional[str]
    status: AllianceStatus
    gang_id: Optional[uuid.UUID] = None
    # Filled from alliance_gang by the CRUD layer, primary first.
    gang_ids: list[uuid.UUID] = []
    founder_id: Optional[uuid.UUID] = None
    founded_at: FuzzyDateField
    created_at: datetime
    updated_at: datetime
    primary_photo_url: Optional[str] = None
    primary_photo_thumb_url: Optional[str] = None


class AllianceStats(BaseModel):
    """Counts over the bloc's members: those tagged straight to it plus the
    current members of every set in it, each person once (the member list's
    definition). Shootings and kills sum `member_stats`, as `set_stats` does."""

    member_count: int = 0
    active_member_count: int = 0
    locked_members: int = 0
    dead_members: int = 0
    total_shootings: int = 0
    total_assists: int = 0
    total_kills: int = 0
    first_incident_year: Optional[int] = None
    last_incident_year: Optional[int] = None


class AllianceTerritorySummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: Optional[str] = None


class AllianceLineageCreate(BaseModel):
    """Open a descent spell between this alliance and another. `direction` says
    where the *other* alliance sits: "parent" means this one came out of it."""

    other_id: uuid.UUID
    kind: SetLineageKind
    direction: Literal["parent", "child"]
    from_date: FuzzyDateField = None


class AllianceLineageEnd(BaseModel):
    until_date: FuzzyDateField = None


class AllianceLineageItem(BaseModel):
    id: uuid.UUID
    kind: SetLineageKind
    direction: Literal["parent", "child"]
    other_id: uuid.UUID
    other_name: str
    other_slug: Optional[str] = None
    from_date: Optional[dict[str, Any]] = None
    until_date: Optional[dict[str, Any]] = None
    is_current: bool


class AllianceReadDetail(AllianceRead):
    """Everything the alliance page shows that the row itself does not hold."""

    territory_ids: list[uuid.UUID]
    set_ids: list[uuid.UUID]
    citations: list[CitationRead] = []
    gangs: list[AllianceGangSummary] = []
    territories: list[AllianceTerritorySummary] = []
    founder_display_name: Optional[str] = None
    founder_slug: Optional[str] = None
    stats: AllianceStats = AllianceStats()
    incidents_per_year: list[IncidentsPerYear] = []
    lineage: list[AllianceLineageItem] = []


class AllianceListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    name_variants: Optional[list[NameVariant]] = None
    emojis: Optional[list[str]] = None
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
    gangs: list[AllianceGangSummary] = []


class AllianceActivityEntry(BaseModel):
    """One row in the alliance's audit feed: the alliance, its sets and the
    members tagged straight to it."""

    id: uuid.UUID
    entity_type: Literal["alliance", "set", "member"]
    entity_id: uuid.UUID
    action: Literal["CREATE", "UPDATE", "DELETE"]
    actor_email: Optional[str] = None
    target_label: Optional[str] = None
    target_slug: Optional[str] = None
    diff_keys: list[str] = []
    created_at: datetime


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
