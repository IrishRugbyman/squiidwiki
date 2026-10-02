import re
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.core.enums import GangNation
from app.core.fuzzy_date import FuzzyDate
from app.schemas.common import FuzzyDateField

_HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


def _validate_color(v: Optional[str]) -> Optional[str]:
    if v is None or v == "":
        return None
    if not _HEX_COLOR_RE.match(v):
        raise ValueError("color must be a hex string like #RRGGBB or #RRGGBBAA")
    return v.lower()


def _clean_symbols(v: Optional[list[str]]) -> Optional[list[str]]:
    if v is None:
        return None
    out = list(dict.fromkeys(x.strip() for x in v if x and x.strip()))
    return out or None


class _GangFields(BaseModel):
    """What a caller may write on a card, shared by create and update."""

    aliases: Optional[list[str]] = None
    description: Optional[str] = None
    color: Optional[str] = None
    color_secondary: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    nation: Optional[GangNation] = None
    origin: Optional[str] = None
    founded_at: FuzzyDateField = None
    symbols: Optional[list[str]] = None

    @field_validator("color", "color_secondary")
    @classmethod
    def _color(cls, v):
        return _validate_color(v)

    @field_validator("symbols")
    @classmethod
    def _symbols(cls, v):
        return _clean_symbols(v)


class GangCreate(_GangFields):
    universe_id: uuid.UUID
    name: str
    # The national history, on the shared card (see GangCard); `description`
    # is this universe's own note.
    card_description: Optional[str] = None


class GangUpdate(_GangFields):
    name: Optional[str] = None
    card_description: Optional[str] = None


class GangRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    name: str
    slug: Optional[str] = None
    aliases: Optional[list[str]] = None
    description: Optional[str] = None
    color: Optional[str] = None
    color_secondary: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    nation: Optional[GangNation] = None
    origin: Optional[str] = None
    founded_at: Optional[FuzzyDate] = None
    symbols: Optional[list[str]] = None
    # The shared card: its slug, national history and aliases. Null for a gang
    # no card is linked to (a local organisation such as Corsica's clans).
    card_id: Optional[uuid.UUID] = None
    card_slug: Optional[str] = None
    card_description: Optional[str] = None
    card_aliases: Optional[list[str]] = None
    created_at: datetime
    updated_at: datetime


class GangListItem(GangRead):
    """A card with the counts the Gangs page sorts and shows by."""

    # Sets claiming this card, as primary or secondary gang.
    set_count: int = 0
    alliance_count: int = 0
    # Current members of those sets plus members tagged to the card directly,
    # each person counted once.
    member_count: int = 0


class GangSummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: Optional[str] = None
    color: Optional[str] = None
    color_secondary: Optional[str] = None


class GangSetItem(BaseModel):
    """One set claiming the card, for the gang page."""

    id: uuid.UUID
    name: str
    slug: Optional[str] = None
    status: str
    is_primary: bool
    member_count: int = 0
    municipality_name: Optional[str] = None
    alliance_name: Optional[str] = None
    alliance_slug: Optional[str] = None
    primary_photo_thumb_url: Optional[str] = None


class GangAllianceItem(BaseModel):
    id: uuid.UUID
    name: str
    slug: Optional[str] = None
    status: str


class GangDetail(GangListItem):
    """The gang page in one round trip."""

    parent: Optional[GangSummary] = None
    # Every card above this one, nearest first (Rollin 80s Skyline Pirus ->
    # Pirus -> Bloods).
    ancestors: list[GangSummary] = []
    branches: list[GangListItem] = []
    sets: list[GangSetItem] = []
    alliances: list[GangAllianceItem] = []
