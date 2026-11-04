import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.enums import (
    CaseDisposition,
    CourtCaseKind,
    CourtJurisdiction,
    MemberStatus,
)
from app.schemas.citation import CitationRead
from app.schemas.common import FuzzyDateField
from app.schemas.incident import IncidentListItem


def _clean(value: Optional[str]) -> Optional[str]:
    """Trimmed, with internal runs of whitespace collapsed; blank reads as None.

    Phase 1 normalises no further than this. Parsing a docket into its court
    and number is the normaliser's job (app.core.dockets, with the backfill),
    and until it exists the court and docket are stored as typed.
    """
    if value is None:
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


def _clean_list(values: list[str]) -> list[str]:
    out: list[str] = []
    for v in values:
        c = _clean(v)
        if c and c not in out:
            out.append(c)
    return out


class Charge(BaseModel):
    """One count as the court lists it."""

    count: Optional[int] = None
    statute: Optional[str] = None
    offense: Optional[str] = None
    disposition: Optional[CaseDisposition] = None
    # When the act was committed, as OTIS gives it per count. Two files against
    # one man (two killings pleaded in one deal) differ by little else.
    offense_date: FuzzyDateField = None


class _CaseFields(BaseModel):
    @field_validator("court", "docket", "judge", mode="before", check_fields=False)
    @classmethod
    def _strip(cls, v):
        return _clean(v) if isinstance(v, str) else v

    @field_validator("docket_aliases", mode="before", check_fields=False)
    @classmethod
    def _strip_aliases(cls, v):
        return _clean_list(v) if isinstance(v, list) else v


class CourtCaseCreate(_CaseFields):
    universe_id: uuid.UUID
    name: str = Field(min_length=1)
    jurisdiction: CourtJurisdiction
    kind: CourtCaseKind = CourtCaseKind.CRIMINAL
    court: str = Field(min_length=1)
    docket: Optional[str] = None
    docket_aliases: list[str] = []
    parent_case_id: Optional[uuid.UUID] = None
    filed_at: FuzzyDateField = None
    closed_at: FuzzyDateField = None
    judge: Optional[str] = None
    summary: Optional[str] = None
    courtlistener_ids: list[int] = []
    # The complete lists. Incidents may be in any universe; sets must be in
    # the case's own (422 otherwise). Sources are cited through /citations.
    incident_ids: list[uuid.UUID] = []
    set_ids: list[uuid.UUID] = []


class CourtCaseUpdate(_CaseFields):
    """A PATCH: only the fields sent change. A list sent replaces the list on
    file, `[]` clears it, and an omitted list is kept."""

    name: Optional[str] = Field(default=None, min_length=1)
    jurisdiction: Optional[CourtJurisdiction] = None
    kind: Optional[CourtCaseKind] = None
    court: Optional[str] = Field(default=None, min_length=1)
    docket: Optional[str] = None
    docket_aliases: Optional[list[str]] = None
    parent_case_id: Optional[uuid.UUID] = None
    filed_at: FuzzyDateField = None
    closed_at: FuzzyDateField = None
    judge: Optional[str] = None
    summary: Optional[str] = None
    courtlistener_ids: Optional[list[int]] = None
    incident_ids: Optional[list[uuid.UUID]] = None
    set_ids: Optional[list[uuid.UUID]] = None


class CourtCaseRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    universe_slug: Optional[str] = None
    name: str
    slug: Optional[str]
    jurisdiction: CourtJurisdiction
    kind: CourtCaseKind
    court: str
    docket: Optional[str]
    docket_aliases: list[str]
    parent_case_id: Optional[uuid.UUID]
    filed_at: FuzzyDateField
    closed_at: FuzzyDateField
    judge: Optional[str]
    summary: Optional[str]
    courtlistener_ids: list[int]
    created_at: datetime
    updated_at: datetime


class CourtCaseListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    # A member's or set's list can hold cases from another universe, so a link
    # cannot assume the current one.
    universe_slug: Optional[str] = None
    name: str
    slug: Optional[str]
    jurisdiction: CourtJurisdiction
    kind: CourtCaseKind
    court: str
    docket: Optional[str]
    filed_at: FuzzyDateField
    closed_at: FuzzyDateField
    defendant_count: int = 0
    incident_count: int = 0
    # Filled on a member's own list: what the case did with them.
    viewer_disposition: Optional[CaseDisposition] = None
    viewer_sentence_months: Optional[int] = None
    viewer_life_sentence: bool = False
    # The member's lead count in the case (a homicide first), so two cases with
    # the same caption and court can be told apart in his list.
    viewer_lead_charge: Optional[str] = None
    viewer_offense_date: FuzzyDateField = None


class CourtCaseBrief(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: Optional[str]
    court: str
    docket: Optional[str]
    kind: CourtCaseKind
    universe_slug: Optional[str] = None


class DefendantCreate(BaseModel):
    member_id: Optional[uuid.UUID] = None
    # For someone the wiki has no member for ("D-7"). Required when member_id is.
    label: Optional[str] = None
    defendant_number: Optional[str] = None
    disposition: CaseDisposition = CaseDisposition.PENDING
    charges: list[Charge] = []
    sentence_months: Optional[int] = Field(default=None, ge=0)
    life_sentence: bool = False
    supervised_release_months: Optional[int] = Field(default=None, ge=0)
    sentenced_at: FuzzyDateField = None
    cooperated: bool = False
    notes: Optional[str] = None

    @field_validator("label", "defendant_number", mode="before")
    @classmethod
    def _strip(cls, v):
        return _clean(v) if isinstance(v, str) else v

    @model_validator(mode="after")
    def _someone(self) -> "DefendantCreate":
        if self.member_id is None and not self.label:
            raise ValueError("a defendant needs a member_id or a label")
        return self


class DefendantUpdate(BaseModel):
    """A PATCH: only the fields sent change, and a field sent as null clears."""

    member_id: Optional[uuid.UUID] = None
    label: Optional[str] = None
    defendant_number: Optional[str] = None
    disposition: Optional[CaseDisposition] = None
    charges: Optional[list[Charge]] = None
    sentence_months: Optional[int] = Field(default=None, ge=0)
    life_sentence: Optional[bool] = None
    supervised_release_months: Optional[int] = Field(default=None, ge=0)
    sentenced_at: FuzzyDateField = None
    cooperated: Optional[bool] = None
    notes: Optional[str] = None

    @field_validator("label", "defendant_number", mode="before")
    @classmethod
    def _strip(cls, v):
        return _clean(v) if isinstance(v, str) else v


class DefendantRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    court_case_id: uuid.UUID
    member_id: Optional[uuid.UUID]
    label: Optional[str]
    defendant_number: Optional[str]
    disposition: CaseDisposition
    charges: list[Charge]
    sentence_months: Optional[int]
    life_sentence: bool
    supervised_release_months: Optional[int]
    sentenced_at: FuzzyDateField
    cooperated: bool
    notes: Optional[str]
    # Filled by the detail endpoint. The member's universe need not be the case's.
    member_name: Optional[str] = None
    member_slug: Optional[str] = None
    member_universe_slug: Optional[str] = None
    member_status: Optional[MemberStatus] = None


class SentencingEvent(BaseModel):
    """A dated sentencing, for the timeline and the calendar."""

    court_case_id: uuid.UUID
    case_name: str
    case_slug: Optional[str]
    universe_slug: Optional[str] = None
    defendant: str
    member_id: Optional[uuid.UUID] = None
    sentenced_at: FuzzyDateField
    disposition: CaseDisposition
    sentence_months: Optional[int]
    life_sentence: bool


class CourtCaseSetBrief(BaseModel):
    id: uuid.UUID
    name: str
    slug: Optional[str]


class CourtCaseSpellBrief(BaseModel):
    """A prison spell served for this case."""

    id: uuid.UUID
    member_id: uuid.UUID
    member_name: Optional[str] = None
    member_slug: Optional[str] = None
    member_universe_slug: Optional[str] = None
    from_date: FuzzyDateField
    to_date: FuzzyDateField
    facility: Optional[str]
    life_sentence: bool


class CourtCaseReadDetail(CourtCaseRead):
    defendants: list[DefendantRead]
    incidents: list[IncidentListItem]
    sets: list[CourtCaseSetBrief]
    citations: list[CitationRead] = []
    spells: list[CourtCaseSpellBrief]
    parent: Optional[CourtCaseBrief] = None
    # Appeals of this case, indictments a complaint became, and so on.
    children: list[CourtCaseBrief] = []
