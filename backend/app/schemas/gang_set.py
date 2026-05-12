import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, model_validator

from app.core.enums import SetRelationshipType, SetStatus


class NameVariant(BaseModel):
    name: Optional[str] = None
    initials: Optional[str] = None
    number: Optional[str] = None
    is_primary: bool = False
    # Which slot leads the display for this variant. If None, falls back to
    # name → initials → number.
    lead: Optional[Literal["name", "initials", "number"]] = None

    @model_validator(mode="after")
    def _at_least_one_field(self):
        if not (self.name or self.initials or self.number):
            raise ValueError("name_variants entry must have at least one of name/initials/number")
        if self.lead is not None and not getattr(self, self.lead):
            # Fall back silently if lead points to an empty slot.
            self.lead = None
        return self


def _normalize_variants(variants: Optional[list[NameVariant]]) -> Optional[list[NameVariant]]:
    if not variants:
        return variants
    primaries = [v for v in variants if v.is_primary]
    if len(primaries) > 1:
        raise ValueError("name_variants may only have one primary entry")
    if not primaries:
        variants[0].is_primary = True
    return variants


def _validate_point(value: Optional[dict]) -> Optional[dict]:
    """A territory_point must be a GeoJSON Point with valid [lng, lat] coordinates."""
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("territory_point must be a GeoJSON Point object")
    if value.get("type") != "Point":
        raise ValueError("territory_point.type must be 'Point'")
    coords = value.get("coordinates")
    if not isinstance(coords, list) or len(coords) < 2:
        raise ValueError("territory_point.coordinates must be [lng, lat]")
    lng, lat = coords[0], coords[1]
    if not isinstance(lng, (int, float)) or not isinstance(lat, (int, float)):
        raise ValueError("territory_point coordinates must be numbers")
    if not (-180 <= lng <= 180):
        raise ValueError("territory_point longitude must be between -180 and 180")
    if not (-90 <= lat <= 90):
        raise ValueError("territory_point latitude must be between -90 and 90")
    return value


def _validate_polygon(value: Optional[dict]) -> Optional[dict]:
    """A territory_polygon must be a closed GeoJSON Polygon.

    None clears the field. Otherwise: type=='Polygon', at least one ring with
    ≥4 coordinates (3 unique vertices plus the closing duplicate), and each
    ring's first coordinate must equal its last."""
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("territory_polygon must be a GeoJSON Polygon object")
    if value.get("type") != "Polygon":
        raise ValueError("territory_polygon.type must be 'Polygon'")
    rings = value.get("coordinates")
    if not isinstance(rings, list) or not rings:
        raise ValueError("territory_polygon.coordinates must be a non-empty list of rings")
    for i, ring in enumerate(rings):
        if not isinstance(ring, list) or len(ring) < 4:
            raise ValueError(f"ring {i} must have at least 4 coordinates (3 vertices + closing point)")
        first, last = ring[0], ring[-1]
        if not (isinstance(first, list) and isinstance(last, list) and len(first) >= 2 and len(last) >= 2):
            raise ValueError(f"ring {i} coordinates must be [lng, lat] pairs")
        if first[0] != last[0] or first[1] != last[1]:
            raise ValueError(f"ring {i} is not closed: first and last coordinates must be equal")
    return value


class SetCreate(BaseModel):
    universe_id: uuid.UUID
    name: str
    name_variants: Optional[list[NameVariant]] = None
    bio: Optional[str] = None
    status: SetStatus = SetStatus.ACTIVE
    alliance_id: Optional[uuid.UUID] = None
    gang_id: Optional[uuid.UUID] = None
    municipality_id: Optional[uuid.UUID] = None
    founder_id: Optional[uuid.UUID] = None
    # Sub-district claims; each id MUST be a child of municipality_id.
    territory_ids: list[uuid.UUID] = []
    friend_ids: list[uuid.UUID] = []
    enemy_ids: list[uuid.UUID] = []

    @model_validator(mode="after")
    def _normalize(self):
        self.name_variants = _normalize_variants(self.name_variants)
        return self


class SetUpdate(BaseModel):
    name: Optional[str] = None
    name_variants: Optional[list[NameVariant]] = None
    bio: Optional[str] = None
    status: Optional[SetStatus] = None
    alliance_id: Optional[uuid.UUID] = None
    gang_id: Optional[uuid.UUID] = None
    municipality_id: Optional[uuid.UUID] = None
    founder_id: Optional[uuid.UUID] = None
    territory_ids: Optional[list[uuid.UUID]] = None
    friend_ids: Optional[list[uuid.UUID]] = None
    enemy_ids: Optional[list[uuid.UUID]] = None
    territory_polygon: Optional[dict] = None
    territory_point: Optional[dict] = None

    @model_validator(mode="after")
    def _normalize(self):
        # Only touch fields the caller actually sent. Unconditional reassignment
        # marks the field as "set", defeating exclude_unset=True in the CRUD —
        # which previously wiped territory_polygon on every form-edit PATCH.
        fields_set = self.model_fields_set
        if "name_variants" in fields_set:
            self.name_variants = _normalize_variants(self.name_variants)
        if "territory_polygon" in fields_set:
            self.territory_polygon = _validate_polygon(self.territory_polygon)
        if "territory_point" in fields_set:
            self.territory_point = _validate_point(self.territory_point)
        return self


class SetRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    name: str
    slug: Optional[str]
    name_variants: Optional[list[NameVariant]]
    bio: Optional[str]
    status: SetStatus
    alliance_id: Optional[uuid.UUID]
    gang_id: Optional[uuid.UUID] = None
    municipality_id: Optional[uuid.UUID]
    founder_id: Optional[uuid.UUID]
    is_reserved: bool = False
    created_at: datetime
    updated_at: datetime
    primary_photo_url: Optional[str] = None
    primary_photo_thumb_url: Optional[str] = None
    territory_polygon: Optional[dict] = None
    territory_point: Optional[dict] = None


class SetReadDetail(SetRead):
    territory_ids: list[uuid.UUID]
    friend_ids: list[uuid.UUID]
    enemy_ids: list[uuid.UUID]


class SetPolygonItem(BaseModel):
    """Lightweight territory row for the territory map (polygon and/or point)."""
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: Optional[str]
    status: SetStatus
    municipality_id: Optional[uuid.UUID]
    alliance_id: Optional[uuid.UUID]
    gang_id: Optional[uuid.UUID] = None
    gang_color: Optional[str] = None
    territory_polygon: Optional[dict] = None
    territory_point: Optional[dict] = None


class SetListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: Optional[str]
    name_variants: Optional[list[NameVariant]]
    status: SetStatus
    universe_id: uuid.UUID
    alliance_id: Optional[uuid.UUID]
    alliance_name: Optional[str] = None
    gang_id: Optional[uuid.UUID] = None
    gang_name: Optional[str] = None
    gang_color: Optional[str] = None
    municipality_id: Optional[uuid.UUID]
    municipality_name: Optional[str] = None
    member_count: int = 0
    is_reserved: bool = False
    primary_photo_url: Optional[str] = None
    primary_photo_thumb_url: Optional[str] = None


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
    active_member_count: int = 0
    last_incident_year: Optional[int] = None
    first_incident_year: Optional[int] = None


class SetRelatedSummary(BaseModel):
    """Lightweight ally / enemy reference for the detail payload."""
    id: uuid.UUID
    name: str
    slug: Optional[str]
    status: SetStatus
    member_count: int = 0


class SetTerritorySummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: Optional[str]


class IncidentsPerYear(BaseModel):
    year: int
    count: int


class SetActivityEntry(BaseModel):
    """One row in the per-set audit feed."""
    id: uuid.UUID
    entity_type: Literal["set", "member"]
    entity_id: uuid.UUID
    action: Literal["CREATE", "UPDATE", "DELETE"]
    actor_email: Optional[str] = None
    target_label: Optional[str] = None  # set name OR member display name
    target_slug: Optional[str] = None
    diff_keys: list[str] = []  # condensed view of diff_json — just the changed field names
    created_at: datetime


class SetReadDetailFull(SetReadDetail):
    """Denormalized payload for the set detail page — single round-trip."""
    alliance_name: Optional[str] = None
    alliance_slug: Optional[str] = None
    municipality_name: Optional[str] = None
    municipality_slug: Optional[str] = None
    founder_display_name: Optional[str] = None
    founder_slug: Optional[str] = None
    gang_name: Optional[str] = None
    gang_color: Optional[str] = None
    territories: list[SetTerritorySummary] = []
    allies: list[SetRelatedSummary] = []
    enemies: list[SetRelatedSummary] = []
    stats: SetStats
    incidents_per_year: list[IncidentsPerYear] = []
    lede: str
