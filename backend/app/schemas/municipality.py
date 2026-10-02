import uuid
from typing import Any, Optional

from pydantic import BaseModel, field_validator

from app.core.enums import MunicipalityKind, SourceReliability


def _clean_aliases(v: Optional[list[str]]) -> Optional[list[str]]:
    """Trim, drop blanks and case-insensitive repeats, keep the given order."""
    if v is None:
        return None
    seen: set[str] = set()
    out: list[str] = []
    for a in v:
        a = a.strip()
        if a and a.casefold() not in seen:
            seen.add(a.casefold())
            out.append(a)
    return out


class MunicipalityCreate(BaseModel):
    universe_id: uuid.UUID
    name: str
    parent_id: Optional[uuid.UUID] = None
    # Omitted: CITY at the top level, DISTRICT under a parent.
    kind: Optional[MunicipalityKind] = None
    geometry: Optional[Any] = None
    aliases: Optional[list[str]] = None
    region: Optional[str] = None
    description: Optional[str] = None
    source_ids: list[uuid.UUID] = []

    @field_validator("aliases")
    @classmethod
    def _aliases(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        return _clean_aliases(v)


class MunicipalityUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    kind: Optional[MunicipalityKind] = None
    geometry: Optional[Any] = None
    aliases: Optional[list[str]] = None
    region: Optional[str] = None
    description: Optional[str] = None
    # The complete list when present; omitted leaves the links alone.
    source_ids: Optional[list[uuid.UUID]] = None

    @field_validator("aliases")
    @classmethod
    def _aliases(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        return _clean_aliases(v)


class MunicipalitySourceBrief(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    url: str
    publication: Optional[str] = None
    reliability: SourceReliability


class _AliasesOut(BaseModel):
    """A stored null reads as no aliases."""

    @field_validator("aliases", mode="before", check_fields=False)
    @classmethod
    def _none_is_empty(cls, v: Any) -> Any:
        return [] if v is None else v


class MunicipalityOverlapBrief(BaseModel):
    """The other layer's row: the districts a neighborhood lies in, or the
    neighborhoods inside a district, with how much of each lies in the other."""

    id: uuid.UUID
    name: str
    kind: MunicipalityKind
    share_of_neighborhood: float
    share_of_district: float


class MunicipalityRead(_AliasesOut):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    name: str
    parent_id: Optional[uuid.UUID]
    kind: MunicipalityKind
    geometry: Optional[Any] = None
    aliases: list[str] = []
    region: Optional[str] = None
    description: Optional[str] = None
    population: Optional[int] = None
    population_year: Optional[int] = None
    population_source: Optional[str] = None
    sources: list[MunicipalitySourceBrief] = []
    overlaps: list[MunicipalityOverlapBrief] = []
    has_geometry: bool = False
    incident_count: int = 0
    child_count: int = 0


class MunicipalityListItem(_AliasesOut):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    parent_id: Optional[uuid.UUID]
    universe_id: uuid.UUID
    kind: MunicipalityKind = MunicipalityKind.CITY
    aliases: list[str] = []
    region: Optional[str] = None
    population: Optional[int] = None
    population_year: Optional[int] = None
    incident_count: int = 0
    # Own incidents plus its sub-districts'; equal to incident_count for a district.
    total_incident_count: int = 0
    child_count: int = 0
    # Real sets anchored to it (a city) or claiming it as territory (a district).
    set_count: int = 0
    has_geometry: bool = False
