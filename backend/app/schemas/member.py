import re
import uuid
from datetime import date, datetime
from typing import Annotated, Any, Optional

from pydantic import AfterValidator, BaseModel, computed_field, model_validator

from app.core.enums import CustodySystem, MemberStatus, RapGroupRole, SetRank
from app.schemas.citation import CitationRead
from app.schemas.common import FuzzyDateField, refuse_null

_BOP_REGISTER_NUMBER = re.compile(r"^(\d{5})-?(\d{3})$")


def normalise_bop_register_number(value: str | None) -> str | None:
    """A BOP register number in the locator's own `NNNNN-NNN` spelling, or None.

    Accepts the hyphen or not and stray whitespace, and turns an empty string
    into None so the member form can clear the field. Anything else is refused:
    an MDOC number or a docket pasted here would otherwise pass for a key.

    Raises:
        ValueError: If the value is not five digits and three digits.
    """
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    match = _BOP_REGISTER_NUMBER.match(value)
    if match is None:
        raise ValueError("a BOP register number is five digits, a hyphen and three digits")
    return f"{match.group(1)}-{match.group(2)}"


BopRegisterNumber = Annotated[Optional[str], AfterValidator(normalise_bop_register_number)]


class MemberSetAffiliationIn(BaseModel):
    """One *current* affiliation. Closing a spell is a separate dated action,
    so there is deliberately no until_date here."""

    set_id: uuid.UUID
    rank: Optional[SetRank] = None
    is_primary: bool = False
    from_date: FuzzyDateField = None


class MemberSetAffiliationOut(BaseModel):
    id: Optional[uuid.UUID] = None
    set_id: uuid.UUID
    set_name: Optional[str] = None
    set_slug: Optional[str] = None
    rank: Optional[SetRank] = None
    is_primary: bool = False
    from_date: Optional[dict[str, Any]] = None
    until_date: Optional[dict[str, Any]] = None

    @computed_field
    @property
    def is_current(self) -> bool:
        return self.until_date is None


class AffiliationEnd(BaseModel):
    """Close an affiliation spell as of a date."""

    until_date: FuzzyDateField = None


class MemberCreate(BaseModel):
    universe_id: uuid.UUID
    nickname: Optional[str] = None
    legal_name: Optional[str] = None
    # The MDOC offender number, when known: OTIS's only stable handle
    # since the rebuilt site gives profiles no URL.
    mdoc_number: Optional[str] = None
    bop_register_number: BopRegisterNumber = None
    nickname_unknown: bool = False
    is_rapper: bool = False
    is_snitch: bool = False
    aliases: Optional[list[str]] = None
    biography: str = ""
    affiliations: list[MemberSetAffiliationIn] = []
    alliance_id: Optional[uuid.UUID] = None
    gang_id: Optional[uuid.UUID] = None
    status: MemberStatus = MemberStatus.UNKNOWN
    dob: FuzzyDateField = None
    date_of_death: FuzzyDateField = None
    family: Optional[dict[str, Any]] = None
    social_media: Optional[dict[str, Any]] = None
    death_incident_id: Optional[uuid.UUID] = None

    @model_validator(mode="after")
    def _fix_primary(self) -> "MemberCreate":
        _ensure_single_primary(self.affiliations)
        return self


class MemberUpdate(BaseModel):
    _required = refuse_null("nickname_unknown", "is_rapper", "is_snitch", "biography", "status")
    nickname: Optional[str] = None
    legal_name: Optional[str] = None
    mdoc_number: Optional[str] = None
    bop_register_number: BopRegisterNumber = None
    nickname_unknown: Optional[bool] = None
    is_rapper: Optional[bool] = None
    is_snitch: Optional[bool] = None
    aliases: Optional[list[str]] = None
    biography: Optional[str] = None
    affiliations: Optional[list[MemberSetAffiliationIn]] = None
    alliance_id: Optional[uuid.UUID] = None
    gang_id: Optional[uuid.UUID] = None
    status: Optional[MemberStatus] = None
    dob: FuzzyDateField = None
    date_of_death: FuzzyDateField = None
    family: Optional[dict[str, Any]] = None
    social_media: Optional[dict[str, Any]] = None
    death_incident_id: Optional[uuid.UUID] = None

    @model_validator(mode="after")
    def _fix_primary(self) -> "MemberUpdate":
        if self.affiliations is not None:
            _ensure_single_primary(self.affiliations)
        return self


def _ensure_single_primary(affiliations: list[MemberSetAffiliationIn]) -> None:
    """Auto-promote first affiliation to primary if none is marked."""
    if not affiliations:
        return
    primaries = [a for a in affiliations if a.is_primary]
    if not primaries:
        affiliations[0].is_primary = True


class MemberRapGroupRef(BaseModel):
    """A rap group or label as a member's page lists it."""

    id: uuid.UUID
    slug: Optional[str] = None
    name: str
    role: RapGroupRole


class MemberRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    nickname: Optional[str]
    legal_name: Optional[str]
    # Defaulted, unlike its neighbours: MemberRead is assembled from dicts in
    # several places, and a required field breaks every one that predates it.
    mdoc_number: Optional[str] = None
    bop_register_number: BopRegisterNumber = None
    nickname_unknown: bool
    is_rapper: bool = False
    is_snitch: bool = False
    aliases: Optional[list[str]]
    biography: str
    affiliations: list[MemberSetAffiliationOut] = []
    # Rap groups and labels, by position. Not sets: never an affiliation.
    rap_groups: list[MemberRapGroupRef] = []
    primary_set_id: Optional[uuid.UUID] = None
    primary_set_name: Optional[str] = None
    primary_set_slug: Optional[str] = None
    # The member's own slug, not the set's. Its absence here meant every consumer
    # reading a member through the detail endpoint had to fall back to the UUID for
    # links, while the list endpoint returned it all along.
    slug: Optional[str] = None
    primary_set_rank: Optional[SetRank] = None
    alliance_id: Optional[uuid.UUID]
    gang_id: Optional[uuid.UUID] = None
    status: MemberStatus
    dob: FuzzyDateField
    date_of_death: FuzzyDateField
    family: Optional[dict[str, Any]]
    social_media: Optional[dict[str, Any]]
    death_incident_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime
    display_name: str
    primary_photo_url: Optional[str] = None
    primary_photo_thumb_url: Optional[str] = None


class MemberKilledInSummary(BaseModel):
    incident_id: uuid.UUID
    type: str
    date: FuzzyDateField = None
    municipality_id: Optional[uuid.UUID] = None
    municipality_name: Optional[str] = None
    # The incident's universe, which may not be the member's: he can be killed
    # away from home. The card links to the incident under this slug.
    universe_slug: Optional[str] = None


class MemberReadDetail(MemberRead):
    citations: list[CitationRead] = []
    alliance_name: Optional[str] = None
    alliance_slug: Optional[str] = None
    aliases_detail: list["MemberAliasRead"] = []
    incarcerations: list["MemberIncarcerationRead"] = []
    custody_ids: list["MemberCustodyIdRead"] = []
    stats: Optional["MemberStats"] = None
    killed_in: Optional[MemberKilledInSummary] = None


class MemberListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    display_name: str
    status: MemberStatus
    affiliations: list[MemberSetAffiliationOut] = []
    rap_groups: list[MemberRapGroupRef] = []
    primary_set_id: Optional[uuid.UUID] = None
    primary_set_name: Optional[str] = None
    primary_set_slug: Optional[str] = None
    primary_set_rank: Optional[SetRank] = None
    alliance_id: Optional[uuid.UUID] = None
    gang_id: Optional[uuid.UUID] = None
    universe_id: uuid.UUID
    slug: Optional[str] = None
    primary_photo_url: Optional[str] = None
    primary_photo_thumb_url: Optional[str] = None
    aliases: Optional[list[str]] = None
    # Both dates: the calendar renders a death, a recurring memorial and a
    # recurring birthday off this one list, and refetching each member to find
    # a date of birth would be one request per row.
    dob: FuzzyDateField = None
    date_of_death: FuzzyDateField = None
    is_rapper: bool = False
    is_snitch: bool = False


class MemberSimilar(BaseModel):
    """A possible duplicate: a member whose name is close to the one asked about."""

    member: MemberListItem
    # word_similarity, 0..1; 1.0 is an exact name, nickname or alias match.
    score: float


class MemberMergeRequest(BaseModel):
    """Merge ``drop_id`` into the member in the path, then delete ``drop_id``."""

    drop_id: uuid.UUID
    # Columns where the dropped record's value should win (see
    # app/crud/member_merge.PREFERABLE_FIELDS). Otherwise the kept value stands
    # unless it is empty.
    prefer: list[str] = []
    # Do the whole merge and roll it back: the preview is the real thing.
    dry_run: bool = False


class MemberMergeRef(BaseModel):
    id: uuid.UUID
    display_name: str
    slug: Optional[str] = None


class MemberMergeField(BaseModel):
    field: str
    kept: Any = None
    discarded: Any = None


class MemberMergeConflict(BaseModel):
    kind: str
    id: Optional[uuid.UUID] = None
    message: str
    discarded: Any = None


class MemberMergeReport(BaseModel):
    keep: MemberMergeRef
    drop: MemberMergeRef
    fields: list[MemberMergeField]
    moved: dict[str, int]
    conflicts: list[MemberMergeConflict]
    dry_run: bool


class MemberIncarcerationCreate(BaseModel):
    from_date: FuzzyDateField = None
    # When the spell ended. Set means historical; see the model for why that is
    # not the same field as max_discharge_date.
    to_date: FuzzyDateField = None
    earliest_release_date: FuzzyDateField = None
    max_discharge_date: FuzzyDateField = None
    life_sentence: bool = False
    facility: Optional[str] = None
    case_id: Optional[str] = None
    # The court case this spell was served for; case_id stays as the custody
    # record wrote it.
    court_case_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class MemberIncarcerationUpdate(BaseModel):
    from_date: FuzzyDateField = None
    to_date: FuzzyDateField = None
    earliest_release_date: FuzzyDateField = None
    max_discharge_date: FuzzyDateField = None
    life_sentence: Optional[bool] = None
    facility: Optional[str] = None
    case_id: Optional[str] = None
    court_case_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class MemberIncarcerationRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    member_id: uuid.UUID
    from_date: FuzzyDateField
    to_date: FuzzyDateField
    earliest_release_date: FuzzyDateField
    max_discharge_date: FuzzyDateField
    life_sentence: bool
    facility: Optional[str]
    case_id: Optional[str]
    court_case_id: Optional[uuid.UUID] = None
    notes: Optional[str]
    created_at: datetime


def normalise_custody_number(system: "CustodySystem", number: str) -> str:
    """A custody number in the spelling its system uses, or ValueError.

    BOP goes through the register-number normaliser. Everything else is kept as
    written minus whitespace: GDC IDs and OTNs carry meaningful leading zeros
    (`0001238843` is a real GDC ID), so nothing here may cast to int.

    Raises:
        ValueError: If the number is empty, or not a BOP register number for BOP.
    """
    if system == CustodySystem.BOP:
        normalised = normalise_bop_register_number(number)
        if normalised is None:
            raise ValueError("a custody number cannot be empty")
        return normalised
    compact = re.sub(r"\s+", "", number or "")
    if not compact:
        raise ValueError("a custody number cannot be empty")
    return compact


class MemberCustodyIdCreate(BaseModel):
    system: CustodySystem
    number: str
    source_id: Optional[uuid.UUID] = None
    photo_media_id: Optional[uuid.UUID] = None
    retrieved_at: Optional[date] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def _normalise(self) -> "MemberCustodyIdCreate":
        self.number = normalise_custody_number(self.system, self.number)
        return self


class MemberCustodyIdUpdate(BaseModel):
    """Everything but the key: to change a number, delete the row and add the right one."""

    source_id: Optional[uuid.UUID] = None
    photo_media_id: Optional[uuid.UUID] = None
    retrieved_at: Optional[date] = None
    notes: Optional[str] = None


class MemberCustodyIdRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    member_id: uuid.UUID
    system: CustodySystem
    number: str
    source_id: Optional[uuid.UUID]
    photo_media_id: Optional[uuid.UUID]
    retrieved_at: Optional[date]
    notes: Optional[str]
    created_at: datetime


class MemberReleaseEvent(BaseModel):
    spell_id: uuid.UUID
    member_id: uuid.UUID
    member_display_name: str
    member_slug: Optional[str]
    facility: Optional[str]
    earliest_release_date: FuzzyDateField = None
    max_discharge_date: FuzzyDateField = None
    life_sentence: bool


class MemberAliasCreate(BaseModel):
    alias: str
    from_date: FuzzyDateField = None
    until_date: FuzzyDateField = None
    source_id: Optional[uuid.UUID] = None


class MemberAliasRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    member_id: uuid.UUID
    alias: str
    from_date: FuzzyDateField
    until_date: FuzzyDateField
    source_id: Optional[uuid.UUID]
    created_at: datetime


class MemberStats(BaseModel):
    member_id: uuid.UUID
    shootings: int
    assists: int
    kills: int
    times_shot_survived: int


MemberReadDetail.model_rebuild()
