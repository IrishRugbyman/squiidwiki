import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, model_validator

from app.core.enums import SetLineageKind, SetRelationshipType, SetStatus, SourceReliability
from app.core.set_names import display_name, normalize_lead
from app.schemas.common import FuzzyDateField

Slot = Literal["name", "initials", "number"]


class NameVariant(BaseModel):
    name: Optional[str] = None
    initials: Optional[str] = None
    number: Optional[str] = None
    is_primary: bool = False
    # Which slots are shown, in order: one slot ("initials"), or several
    # (["initials", "number"] shows "CFP 2400"). If None, falls back to
    # name → initials → number. See app/core/set_names.py.
    lead: Optional[Slot | list[Slot]] = None

    @model_validator(mode="after")
    def _at_least_one_field(self):
        if not (self.name or self.initials or self.number):
            raise ValueError("name_variants entry must have at least one of name/initials/number")
        # Slots the variant does not fill are dropped, and a list of one is
        # stored as that slot.
        self.lead = normalize_lead(self.lead, self)
        return self


MAX_EMOJIS = 12
MAX_EMOJI_LENGTH = 16


def _normalize_emojis(emojis: Optional[list[str]]) -> Optional[list[str]]:
    """Trim, drop blanks, de-duplicate, and reject anything that is not a glyph.

    Order is meaningful - the first entry is the badge - so de-duplication keeps
    first occurrence rather than sorting.

    The "not a glyph" test is that an entry cannot be *entirely* ASCII. A real
    emoji never is, even the keycaps (`1\ufe0f\u20e3` is an ASCII digit plus two
    non-ASCII code points), while `BO` or `752` is, and those belong in
    `name_variants` where they are searchable as names. Anything looser and this
    column quietly becomes a second alias field.
    """
    if emojis is None:
        return None
    out: list[str] = []
    for raw in emojis:
        e = (raw or "").strip()
        if not e:
            continue
        if len(e) > MAX_EMOJI_LENGTH:
            raise ValueError(f"emoji entry too long (max {MAX_EMOJI_LENGTH} characters): {e!r}")
        if all(ord(c) < 128 for c in e):
            raise ValueError(f"not an emoji: {e!r} - plain text belongs in name_variants")
        if e not in out:
            out.append(e)
    if len(out) > MAX_EMOJIS:
        raise ValueError(f"at most {MAX_EMOJIS} emojis per set (got {len(out)})")
    return out or None


def _normalize_variants(variants: Optional[list[NameVariant]]) -> Optional[list[NameVariant]]:
    if not variants:
        return variants
    primaries = [v for v in variants if v.is_primary]
    if len(primaries) > 1:
        raise ValueError("name_variants may only have one primary entry")
    if not primaries:
        variants[0].is_primary = True
    return variants


def _derived_name(sent: Optional[str], variants: list[NameVariant]) -> str:
    """The set's name, computed from its primary variant.

    `sets.name` is never taken from the caller. A caller may still send it, and
    it must then agree with the primary variant: a mismatch means the client
    computed the display differently (the bug that let a form save rename "CFP
    2400" to "CFP"), and is refused rather than silently overridden.
    """
    derived = display_name(variants)
    if sent is not None and sent.strip() != derived:
        raise ValueError(
            f"name {sent!r} does not match the primary name variant, which displays as "
            f"{derived!r}. A set's name is derived from its primary variant: change "
            "name_variants (its slots or its lead) to rename it"
        )
    return derived


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


def _validate_rings(rings: object, where: str) -> None:
    """One polygon's rings: at least one, each closed with ≥4 positions."""
    if not isinstance(rings, list) or not rings:
        raise ValueError(f"{where} must be a non-empty list of rings")
    for i, ring in enumerate(rings):
        if not isinstance(ring, list) or len(ring) < 4:
            raise ValueError(
                f"{where} ring {i} must have at least 4 coordinates (3 vertices + closing point)"
            )
        first, last = ring[0], ring[-1]
        if not (
            isinstance(first, list)
            and isinstance(last, list)
            and len(first) >= 2
            and len(last) >= 2
        ):
            raise ValueError(f"{where} ring {i} coordinates must be [lng, lat] pairs")
        if first[0] != last[0] or first[1] != last[1]:
            raise ValueError(
                f"{where} ring {i} is not closed: first and last coordinates must be equal"
            )


def _validate_polygon(value: Optional[dict]) -> Optional[dict]:
    """A territory_polygon is a closed GeoJSON Polygon, or a MultiPolygon.

    None clears the field. A MultiPolygon is for ground in separate pieces
    (1000 TG's first East Warren block and its two Mount Clemens parks): each
    piece is held to the Polygon rule, at least one ring of ≥4 coordinates (3
    unique vertices plus the closing duplicate), each closing on its first."""
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("territory_polygon must be a GeoJSON Polygon or MultiPolygon object")
    kind = value.get("type")
    coordinates = value.get("coordinates")
    if kind == "Polygon":
        _validate_rings(coordinates, "territory_polygon")
    elif kind == "MultiPolygon":
        if not isinstance(coordinates, list) or not coordinates:
            raise ValueError("territory_polygon.coordinates must be a non-empty list of polygons")
        for n, rings in enumerate(coordinates):
            _validate_rings(rings, f"territory_polygon polygon {n}")
    else:
        raise ValueError("territory_polygon.type must be 'Polygon' or 'MultiPolygon'")
    return value


class SetGangSummary(BaseModel):
    """One gang a set claims, as the list and detail payloads carry it."""

    id: uuid.UUID
    name: str
    slug: Optional[str] = None
    color: Optional[str] = None


class SetAllianceSummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: Optional[str] = None


def _dedupe_ids(ids: Optional[list[uuid.UUID]]) -> Optional[list[uuid.UUID]]:
    """Keep the first occurrence of each id, preserving order (order is rank)."""
    if ids is None:
        return None
    return list(dict.fromkeys(ids))


class SetCreate(BaseModel):
    universe_id: uuid.UUID
    # Derived from the primary name variant; optional when variants are sent.
    # Sent alone, it becomes the primary variant's `name` slot.
    name: Optional[str] = None
    name_variants: Optional[list[NameVariant]] = None
    emojis: Optional[list[str]] = None
    bio: Optional[str] = None
    status: SetStatus = SetStatus.ACTIVE
    # Legacy single alliance. Ignored when alliance_ids is sent.
    alliance_id: Optional[uuid.UUID] = None
    # Every alliance the set is in, primary first; mirrored into sets.alliance_id.
    alliance_ids: Optional[list[uuid.UUID]] = None
    # Legacy single gang. Ignored when gang_ids is sent; otherwise it becomes
    # the set's one gang.
    gang_id: Optional[uuid.UUID] = None
    # Every gang the set claims, in rank order: the first is the primary and is
    # mirrored into sets.gang_id.
    gang_ids: Optional[list[uuid.UUID]] = None
    municipality_id: Optional[uuid.UUID] = None
    founder_id: Optional[uuid.UUID] = None
    # Sub-district claims; each id MUST be a child of municipality_id.
    territory_ids: list[uuid.UUID] = []
    friend_ids: list[uuid.UUID] = []
    enemy_ids: list[uuid.UUID] = []
    # Citations for the set itself (set_source).
    source_ids: list[uuid.UUID] = []

    @model_validator(mode="after")
    def _normalize(self):
        variants = _normalize_variants(self.name_variants)
        if not variants:
            name = (self.name or "").strip()
            if not name:
                raise ValueError("a set needs a name or a primary name variant")
            variants = [NameVariant(name=name, is_primary=True)]
        self.name_variants = variants
        self.name = _derived_name(self.name, variants)
        self.source_ids = _dedupe_ids(self.source_ids) or []
        self.emojis = _normalize_emojis(self.emojis)
        self.gang_ids = _dedupe_ids(self.gang_ids)
        self.alliance_ids = _dedupe_ids(self.alliance_ids)
        return self


class SetUpdate(BaseModel):
    # Derived from the primary name variant, never set on its own: a rename is
    # a change to name_variants. May be sent alongside them if it agrees.
    name: Optional[str] = None
    name_variants: Optional[list[NameVariant]] = None
    emojis: Optional[list[str]] = None
    bio: Optional[str] = None
    status: Optional[SetStatus] = None
    # Legacy single alliance: it becomes the primary and the set's other
    # alliances are kept; null clears them all. Ignored when alliance_ids is sent.
    alliance_id: Optional[uuid.UUID] = None
    # The complete, ordered list of alliances; the first is the primary. [] clears.
    alliance_ids: Optional[list[uuid.UUID]] = None
    # Legacy single gang, for callers that predate gang_ids: a gang here becomes
    # the primary and the set's other gangs are kept; null clears them all.
    # Ignored when gang_ids is sent.
    gang_id: Optional[uuid.UUID] = None
    # The complete, ordered list of gangs; the first is the primary. [] clears.
    gang_ids: Optional[list[uuid.UUID]] = None
    municipality_id: Optional[uuid.UUID] = None
    founder_id: Optional[uuid.UUID] = None
    territory_ids: Optional[list[uuid.UUID]] = None
    friend_ids: Optional[list[uuid.UUID]] = None
    enemy_ids: Optional[list[uuid.UUID]] = None
    territory_polygon: Optional[dict] = None
    territory_point: Optional[dict] = None
    # The complete citation list for the set itself; [] clears. Omit to keep.
    source_ids: Optional[list[uuid.UUID]] = None

    @model_validator(mode="after")
    def _normalize(self):
        # Only touch fields the caller actually sent. Unconditional reassignment
        # marks the field as "set", defeating exclude_unset=True in the CRUD —
        # which previously wiped territory_polygon on every form-edit PATCH.
        fields_set = self.model_fields_set
        if "name_variants" in fields_set:
            if not self.name_variants:
                raise ValueError("name_variants cannot be cleared: a set needs a primary name")
            self.name_variants = _normalize_variants(self.name_variants)
            self.name = _derived_name(
                self.name if "name" in fields_set else None, self.name_variants
            )
        elif "name" in fields_set:
            raise ValueError(
                "a set's name is derived from its primary name variant: "
                "send name_variants to rename it"
            )
        if "emojis" in fields_set:
            self.emojis = _normalize_emojis(self.emojis)
        if "gang_ids" in fields_set:
            self.gang_ids = _dedupe_ids(self.gang_ids)
        if "alliance_ids" in fields_set:
            self.alliance_ids = _dedupe_ids(self.alliance_ids)
        if "source_ids" in fields_set:
            self.source_ids = _dedupe_ids(self.source_ids)
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
    emojis: Optional[list[str]] = None
    bio: Optional[str]
    status: SetStatus
    alliance_id: Optional[uuid.UUID]
    # Filled from alliance_set by the CRUD layer, primary first; [] for none.
    alliance_ids: list[uuid.UUID] = []
    gang_id: Optional[uuid.UUID] = None
    # Filled from set_gang by the CRUD layer (a transient attribute on the ORM
    # row); [] when the set claims no gang.
    gang_ids: list[uuid.UUID] = []
    municipality_id: Optional[uuid.UUID]
    founder_id: Optional[uuid.UUID]
    is_reserved: bool = False
    created_at: datetime
    updated_at: datetime
    primary_photo_url: Optional[str] = None
    primary_photo_thumb_url: Optional[str] = None
    territory_polygon: Optional[dict] = None
    territory_point: Optional[dict] = None


class SetSourceBrief(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    url: str
    publication: Optional[str] = None
    reliability: SourceReliability


class SetReadDetail(SetRead):
    territory_ids: list[uuid.UUID]
    friend_ids: list[uuid.UUID]
    enemy_ids: list[uuid.UUID]
    lineage: list["SetLineageItem"] = []
    source_ids: list[uuid.UUID] = []


class SetPolygonItem(BaseModel):
    """Lightweight territory row for the territory map (polygon and/or point)."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: Optional[str]
    status: SetStatus
    municipality_id: Optional[uuid.UUID]
    alliance_id: Optional[uuid.UUID]
    alliance_ids: list[uuid.UUID] = []
    gang_id: Optional[uuid.UUID] = None
    gang_color: Optional[str] = None
    gang_color_secondary: Optional[str] = None
    # Main colour of every gang the set claims, primary first.
    gang_colors: list[str] = []
    territory_polygon: Optional[dict] = None
    territory_point: Optional[dict] = None


class SetListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: Optional[str]
    name_variants: Optional[list[NameVariant]]
    emojis: Optional[list[str]] = None
    status: SetStatus
    universe_id: uuid.UUID
    alliance_id: Optional[uuid.UUID]
    alliance_name: Optional[str] = None
    # Every alliance, primary first. alliance_id/alliance_name are the primary's.
    alliances: list[SetAllianceSummary] = []
    gang_id: Optional[uuid.UUID] = None
    gang_name: Optional[str] = None
    gang_color: Optional[str] = None
    # Every gang, primary first. gang_id/gang_name/gang_color are the primary's.
    gangs: list[SetGangSummary] = []
    municipality_id: Optional[uuid.UUID]
    municipality_name: Optional[str] = None
    member_count: int = 0
    is_reserved: bool = False
    primary_photo_url: Optional[str] = None
    primary_photo_thumb_url: Optional[str] = None
    # Declared so they survive serialisation: the router always passed
    # territory_ids, but without the field Pydantic dropped it, and the set form's
    # "also claimed by" hints read an empty list for every set.
    territory_ids: list[uuid.UUID] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SetRelationshipCreate(BaseModel):
    target_id: uuid.UUID
    type: SetRelationshipType
    # When the link began. Often known only to the year, which FuzzyDate covers.
    # Null is not the same claim as a dated start: it reads as "for as long as
    # anyone recorded", so set it whenever the date is known.
    from_date: FuzzyDateField = None


class SetRelationshipEnd(BaseModel):
    """Close a relationship spell as of a date."""

    until_date: FuzzyDateField = None


class SetRelationshipHistoryItem(BaseModel):
    """One spell of a link with another set, current or ended."""

    id: uuid.UUID
    other_id: uuid.UUID
    other_name: str
    other_slug: Optional[str] = None
    type: SetRelationshipType
    from_date: Optional[dict[str, Any]] = None
    until_date: Optional[dict[str, Any]] = None
    is_current: bool


class SetLineageCreate(BaseModel):
    """Open a descent spell between this set and another.

    `direction` says which side of the edge the *other* set is on, so the same
    form works from either set's page: "parent" means the other set is the one
    this set came out of.
    """

    other_id: uuid.UUID
    kind: SetLineageKind
    direction: Literal["parent", "child"]
    from_date: FuzzyDateField = None


class SetLineageEnd(BaseModel):
    until_date: FuzzyDateField = None


class SetLineageItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    kind: SetLineageKind
    # Where the *other* set sits relative to the set being viewed.
    direction: Literal["parent", "child"]
    other_id: uuid.UUID
    other_name: str
    other_slug: Optional[str] = None
    from_date: Optional[dict[str, Any]] = None
    until_date: Optional[dict[str, Any]] = None
    is_current: bool


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
    # Every alliance, primary first; alliance_name/alliance_slug are the primary's.
    alliances: list[SetAllianceSummary] = []
    municipality_name: Optional[str] = None
    municipality_slug: Optional[str] = None
    founder_display_name: Optional[str] = None
    founder_slug: Optional[str] = None
    gang_name: Optional[str] = None
    gang_color: Optional[str] = None
    gangs: list[SetGangSummary] = []
    territories: list[SetTerritorySummary] = []
    allies: list[SetRelatedSummary] = []
    enemies: list[SetRelatedSummary] = []
    stats: SetStats
    incidents_per_year: list[IncidentsPerYear] = []
    sources: list[SetSourceBrief] = []
    lede: str
