"""The one shape a source takes inside any record, and a citation of it.

Before 2026-10-04 every record type had its own copy of a source brief
(IncidentSourceBrief, SetSourceBrief, CourtCaseSourceBrief,
MunicipalitySourceBrief), none of them carrying the date, the domain or the
archive link, and members and businesses returned bare ids. Every record now
returns `citations: list[CitationRead]` built from these.
"""

import uuid
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, computed_field

from app.core.enums import SourceReliability
from app.core.sources import domain_of
from app.schemas.common import FuzzyDateField

EntityType = Literal[
    "member", "incident", "set", "alliance", "court_case", "municipality", "business"
]


class SourceSummary(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    url: str
    kind: str
    publication: Optional[str] = None
    published_at: FuzzyDateField = None
    accessed_at: Optional[date] = None
    reliability: SourceReliability
    archive_url: Optional[str] = None
    lookup_system: Optional[str] = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def domain(self) -> Optional[str]:
        return domain_of(self.url)


class CitationRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    source_id: uuid.UUID
    position: int
    locator: Optional[str] = None
    quote: Optional[str] = None
    note: Optional[str] = None
    accessed_at: Optional[date] = None
    created_at: datetime
    source: SourceSummary


class CitationDetail(BaseModel):
    """The per-citation fields a researcher writes."""

    locator: Optional[str] = Field(default=None, max_length=500)
    quote: Optional[str] = Field(default=None, max_length=5000)
    note: Optional[str] = Field(default=None, max_length=5000)
    accessed_at: Optional[date] = None


class CitationCreate(CitationDetail):
    source_id: uuid.UUID
    entity_type: EntityType
    entity_id: uuid.UUID
    # Omitted: appended after the record's last citation.
    position: Optional[int] = Field(default=None, ge=0)


class CitationUpdate(BaseModel):
    locator: Optional[str] = Field(default=None, max_length=500)
    quote: Optional[str] = Field(default=None, max_length=5000)
    note: Optional[str] = Field(default=None, max_length=5000)
    accessed_at: Optional[date] = None
    # Re-point a citation at another source (same universe), e.g. a duplicate.
    source_id: Optional[uuid.UUID] = None


class CitationBatch(BaseModel):
    items: list[CitationCreate] = Field(min_length=1, max_length=500)
    # What to do with an item whose (source, record) pair is already cited:
    # skip it, or overwrite the detail fields it carries.
    on_conflict: Literal["skip", "update"] = "skip"


class CitationBatchResult(BaseModel):
    created: list[uuid.UUID]
    updated: list[uuid.UUID]
    skipped: list[uuid.UUID]


class CitationOrder(BaseModel):
    entity_type: EntityType
    entity_id: uuid.UUID
    # Every citation of the record, in the new order.
    ids: list[uuid.UUID]


class EntityRef(BaseModel):
    """Any record, as the source page lists it."""

    type: EntityType
    id: uuid.UUID
    slug: Optional[str] = None
    label: str
    detail: Optional[str] = None
    date: FuzzyDateField = None
    universe_slug: Optional[str] = None


class SourceCitationRow(BaseModel):
    """A citation of one source, seen from the source: which record, and how."""

    id: uuid.UUID
    source_id: uuid.UUID
    position: int
    locator: Optional[str] = None
    quote: Optional[str] = None
    note: Optional[str] = None
    accessed_at: Optional[date] = None
    created_at: datetime
    entity: EntityRef


class SourceCustodyRow(BaseModel):
    id: uuid.UUID
    system: str
    number: str
    retrieved_at: Optional[date] = None
    member_id: uuid.UUID
    member_slug: Optional[str] = None
    member_label: str
