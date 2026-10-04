import uuid
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, computed_field

from app.core.enums import SourceReliability
from app.core.sources import SourceKind, domain_of
from app.schemas.common import FuzzyDateField


class SourceCreate(BaseModel):
    universe_id: uuid.UUID
    url: str
    title: str
    publication: Optional[str] = None
    published_at: FuzzyDateField = None
    accessed_at: Optional[date] = None
    reliability: SourceReliability = SourceReliability.UNVERIFIED
    # Omitted: derived from the URL (app.core.sources.classify_kind).
    kind: Optional[SourceKind] = None
    notes: Optional[str] = None
    archive_url: Optional[str] = None
    # The API refuses a URL already on file in the universe (409 duplicate_url)
    # and a custody lookup URL (409 lookup_source: cite the system's source
    # with a locator instead). True overrides the first, never the second.
    allow_duplicate: bool = False


class SourceUpdate(BaseModel):
    url: Optional[str] = None
    title: Optional[str] = None
    publication: Optional[str] = None
    published_at: FuzzyDateField = None
    accessed_at: Optional[date] = None
    reliability: Optional[SourceReliability] = None
    kind: Optional[SourceKind] = None
    notes: Optional[str] = None
    archive_url: Optional[str] = None


class SourceBulkUpdate(BaseModel):
    ids: list[uuid.UUID] = Field(min_length=1, max_length=1000)
    reliability: Optional[SourceReliability] = None
    kind: Optional[SourceKind] = None


class SourceMerge(BaseModel):
    into_id: uuid.UUID


class SourceMergeResult(BaseModel):
    moved: int
    combined: int
    into_id: uuid.UUID


class SourceCounts(BaseModel):
    member: int = 0
    incident: int = 0
    set: int = 0
    alliance: int = 0
    court_case: int = 0
    municipality: int = 0
    business: int = 0
    # Cited through a single column rather than a citation.
    custody_id: int = 0
    alias: int = 0
    media: int = 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total(self) -> int:
        return (
            self.member
            + self.incident
            + self.set
            + self.alliance
            + self.court_case
            + self.municipality
            + self.business
            + self.custody_id
            + self.alias
            + self.media
        )


class SourceRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    url: str
    title: str
    publication: Optional[str]
    published_at: FuzzyDateField
    accessed_at: Optional[date]
    reliability: SourceReliability
    kind: str
    lookup_system: Optional[str] = None
    notes: Optional[str]
    archive_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def domain(self) -> Optional[str]:
        return domain_of(self.url)


class SourceReadDetail(SourceRead):
    counts: SourceCounts


class SourceListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    url: str
    reliability: SourceReliability
    kind: str = "OTHER"
    lookup_system: Optional[str] = None
    publication: Optional[str] = None
    published_at: FuzzyDateField = None
    archive_url: Optional[str] = None
    created_at: Optional[datetime] = None
    # Filled on list rows (crud.source.attach_counts); zero elsewhere.
    counts: SourceCounts = SourceCounts()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def domain(self) -> Optional[str]:
        return domain_of(self.url)


class SourceFacets(BaseModel):
    kind: dict[str, int]
    reliability: dict[str, int]


class SourceListPage(BaseModel):
    items: list[SourceListItem]
    total: int
    facets: SourceFacets


SourceSort = Literal["added", "title", "published", "cited", "reliability"]


class SourceLookupHit(BaseModel):
    source: "SourceListItem"
    suggested_locator: Optional[str] = None


class SourceLookup(BaseModel):
    """What the wiki already holds for a pasted URL."""

    exact: Optional[SourceListItem] = None
    lookup: Optional[SourceLookupHit] = None
    same_host: list[SourceListItem] = []
