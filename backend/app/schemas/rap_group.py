import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator

from app.core.enums import (
    MemberStatus,
    RapGroupKind,
    RapGroupRole,
    RapGroupStatus,
)
from app.schemas.citation import CitationRead
from app.schemas.common import FuzzyDateField
from app.schemas.incident import IncidentListItem
from app.schemas.names import NameVariant, dedupe_ids, derived_name, normalize_variants


class RapGroupMemberIn(BaseModel):
    model_config = {"extra": "forbid"}

    member_id: uuid.UUID
    role: RapGroupRole = RapGroupRole.MEMBER
    since: FuzzyDateField = None
    until: FuzzyDateField = None


def _check_members(members: Optional[list[RapGroupMemberIn]]) -> None:
    if not members:
        return
    ids = [m.member_id for m in members]
    if len(set(ids)) != len(ids):
        raise ValueError("members lists a member more than once")


class RapGroupCreate(BaseModel):
    # A stale or misspelled field is refused, not dropped.
    model_config = {"extra": "forbid"}

    universe_id: uuid.UUID
    # Derived from the primary name variant; optional when variants are sent.
    # Sent alone, it becomes the primary variant's `name` slot.
    name: Optional[str] = None
    name_variants: Optional[list[NameVariant]] = None
    kind: RapGroupKind = RapGroupKind.GROUP
    status: RapGroupStatus = RapGroupStatus.ACTIVE
    active_from: FuzzyDateField = None
    active_to: FuzzyDateField = None
    municipality_id: Optional[uuid.UUID] = None
    bio: Optional[str] = None
    # The complete list, in display order.
    members: list[RapGroupMemberIn] = []
    friend_ids: list[uuid.UUID] = []
    enemy_ids: list[uuid.UUID] = []

    @model_validator(mode="after")
    def _normalize(self):
        variants = normalize_variants(self.name_variants)
        if not variants:
            name = (self.name or "").strip()
            if not name:
                raise ValueError("a rap group needs a name or a primary name variant")
            variants = [NameVariant(name=name, is_primary=True)]
        self.name_variants = variants
        self.name = derived_name(self.name, variants, kind="rap group")
        _check_members(self.members)
        self.friend_ids = dedupe_ids(self.friend_ids) or []
        self.enemy_ids = dedupe_ids(self.enemy_ids) or []
        return self


class RapGroupUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    # Derived from the primary name variant, never set on its own: a rename is
    # a change to name_variants. May be sent alongside them if it agrees.
    name: Optional[str] = None
    name_variants: Optional[list[NameVariant]] = None
    kind: Optional[RapGroupKind] = None
    status: Optional[RapGroupStatus] = None
    active_from: FuzzyDateField = None
    active_to: FuzzyDateField = None
    municipality_id: Optional[uuid.UUID] = None
    bio: Optional[str] = None
    # Complete lists: they replace what is on file. [] clears.
    members: Optional[list[RapGroupMemberIn]] = None
    friend_ids: Optional[list[uuid.UUID]] = None
    enemy_ids: Optional[list[uuid.UUID]] = None

    @model_validator(mode="after")
    def _normalize(self):
        # Only fields the caller sent: reassigning one marks it set and defeats
        # exclude_unset in the CRUD.
        fields_set = self.model_fields_set
        if "name_variants" in fields_set:
            if not self.name_variants:
                raise ValueError(
                    "name_variants cannot be cleared: a rap group needs a primary name"
                )
            self.name_variants = normalize_variants(self.name_variants)
            self.name = derived_name(
                self.name if "name" in fields_set else None, self.name_variants, kind="rap group"
            )
        elif "name" in fields_set:
            raise ValueError(
                "a rap group's name is derived from its primary name variant: "
                "send name_variants to rename it"
            )
        for field in ("kind", "status"):
            if field in fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        if "members" in fields_set:
            if self.members is None:
                raise ValueError("members cannot be null; send [] to clear")
            _check_members(self.members)
        for field in ("friend_ids", "enemy_ids"):
            if field in fields_set:
                setattr(self, field, dedupe_ids(getattr(self, field)) or [])
        return self


class RapGroupMunicipality(BaseModel):
    id: uuid.UUID
    name: str
    # Municipalities have no slug column; kept so the shape matches the spec.
    slug: Optional[str] = None


class RapGroupRead(BaseModel):
    """The row itself, as POST and PATCH return it."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    name: str
    slug: Optional[str] = None
    name_variants: Optional[list[NameVariant]] = None
    kind: RapGroupKind
    status: RapGroupStatus
    active_from: FuzzyDateField = None
    active_to: FuzzyDateField = None
    municipality_id: Optional[uuid.UUID] = None
    bio: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class RapGroupListItem(BaseModel):
    id: uuid.UUID
    slug: Optional[str] = None
    name: str
    name_variants: Optional[list[NameVariant]] = None
    kind: RapGroupKind
    status: RapGroupStatus
    active_from: FuzzyDateField = None
    active_to: FuzzyDateField = None
    municipality: Optional[RapGroupMunicipality] = None
    member_count: int = 0
    primary_photo_url: Optional[str] = None


class RapGroupSetRef(BaseModel):
    id: uuid.UUID
    slug: Optional[str] = None
    name: str


class RapGroupMemberOut(BaseModel):
    member_id: uuid.UUID
    slug: Optional[str] = None
    display_name: str
    role: RapGroupRole
    since: FuzzyDateField = None
    until: FuzzyDateField = None
    primary_photo_thumb_url: Optional[str] = None
    status: MemberStatus
    # The member's current sets, primary first.
    sets: list[RapGroupSetRef] = []


class RapGroupSetRepresented(RapGroupSetRef):
    count: int


class RapGroupRelationshipOut(BaseModel):
    rap_group_id: uuid.UUID
    slug: Optional[str] = None
    name: str
    type: str


class RapGroupReadDetail(RapGroupListItem):
    bio: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    members: list[RapGroupMemberOut] = []
    sets_represented: list[RapGroupSetRepresented] = []
    relationships: list[RapGroupRelationshipOut] = []
    incidents: list[IncidentListItem] = []
    citations: list[CitationRead] = []
