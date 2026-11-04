import re
import uuid
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import FuzzyDateField

# A saved OTIS profile page is a few hundred KB; this is headroom, not a target.
MAX_PASTED_HTML_CHARS = 4_000_000
# 20 pages x 25 rows = 500 rows, each page a round trip through the SOCKS proxy.
MAX_SEARCH_PAGES = 20


class MdocLookupRequest(BaseModel):
    """Identify an offender to look up.

    OTIS profiles no longer have URLs - the rebuilt site holds the selected
    offender in session state, so an MDOC number is the only stable handle.
    `url` is still accepted so that old `otis2profile.aspx?mdocNumber=NNNNNN`
    links (and the paste box in the member form) keep working: the number is
    pulled out of them and the rest discarded.
    """

    mdoc_number: Optional[str] = None
    url: Optional[str] = None

    @model_validator(mode="after")
    def _resolve_number(self) -> "MdocLookupRequest":
        raw = self.mdoc_number or self.url or ""
        m = re.search(r"\d{4,}", raw)
        if not m:
            raise ValueError(
                "Supply an MDOC offender number. OTIS profile pages no longer "
                "have their own URLs, so a link to one cannot be resolved."
            )
        self.mdoc_number = m.group(0)
        return self


class MdocSearchRequest(BaseModel):
    """Every field of the OTIS search form, plus a cap on pages walked.

    Enum values are checked by the service against its module constants
    (`SEX_VALUES`, `RACE_VALUES`, `STATUS_VALUES`) and a bad one comes back as
    400, as does a request naming none of name, MDOC number and tattoo text.
    `status` left out means the service's `DEFAULT_STATUS`.
    """

    last_name: str = ""
    first_name: str = ""
    mdoc_number: str = ""
    sex: str = "Either"
    race: str = "All"
    age: Optional[int] = Field(default=None, ge=1, le=129)
    status: Optional[str] = None
    tattoos: str = ""
    max_pages: int = Field(default=10, ge=1, le=MAX_SEARCH_PAGES)


class MdocParseRequest(BaseModel):
    """Parse HTML the caller already has, instead of fetching it.

    Kept as the escape hatch for when the server can't reach OTIS: Cloudflare
    403s this host's IP, so `/mdoc/lookup` only works with `MDOC_PROXY` pointed
    at a proxy that egresses elsewhere. A browser that can reach OTIS can hand
    the page over instead.

    `page_url` is vestigial - the photo is now inlined in the page, so there is
    no relative src left to resolve against - and is ignored.
    """

    html: str = Field(min_length=1, max_length=MAX_PASTED_HTML_CHARS)
    page_url: Optional[str] = None


class MdocSentenceRead(BaseModel):
    kind: str
    active: bool
    offense: Optional[str] = None
    mcl: list[str] = []
    court_file: Optional[str] = None
    county: Optional[str] = None
    conviction_type: Optional[str] = None
    minimum_sentence: Optional[str] = None
    maximum_sentence: Optional[str] = None
    date_of_offense: FuzzyDateField = None
    date_of_sentence: FuzzyDateField = None
    date_of_discharge: FuzzyDateField = None
    discharge_reason: Optional[str] = None


class MdocSpellRead(BaseModel):
    """An incarceration spell derived from the profile, ready to post back.

    Deliberately shaped like `MemberIncarcerationCreate` rather than like OTIS:
    the client posts these at `/members/{id}/incarcerations` verbatim. See
    `derive_spells` for why the projected dates land on only one of them.
    """

    from_date: FuzzyDateField = None
    to_date: FuzzyDateField = None
    earliest_release_date: FuzzyDateField = None
    max_discharge_date: FuzzyDateField = None
    life_sentence: bool = False
    facility: Optional[str] = None
    case_id: Optional[str] = None
    notes: Optional[str] = None


class MdocProfileResponse(BaseModel):
    legal_name: str
    dob: FuzzyDateField
    earliest_release_date: FuzzyDateField = None
    # Only populated while the offender is still serving; see MdocProfile.
    max_discharge_date: FuzzyDateField = None
    facility: Optional[str] = None
    # A `data:` URI, not a link: OTIS inlines the mugshot and no longer serves
    # it from an endpoint. Post it back to /mdoc/import-photo unchanged.
    photo_url: Optional[str] = None

    mdoc_number: Optional[str] = None
    sid_number: Optional[str] = None
    race: Optional[str] = None
    sex: Optional[str] = None
    hair: Optional[str] = None
    eyes: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    image_date: FuzzyDateField = None
    status: Optional[str] = None
    security_level: Optional[str] = None
    discharge_date: FuzzyDateField = None
    aliases: list[str] = []
    marks: list[str] = []
    sentences: list[MdocSentenceRead] = []
    # The sentences above, reshaped into incarceration spells. `sentences` is
    # what OTIS shows; this is what the wiki stores.
    spells: list[MdocSpellRead] = []


class MdocSearchRowRead(BaseModel):
    """One results-list row: a lead, not a profile. Look the number up for the rest."""

    mdoc_number: str
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    dob: FuzzyDateField = None
    sex: Optional[str] = None
    race: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    parole_board_date: FuzzyDateField = None
    max_date: FuzzyDateField = None
    date_paroled: FuzzyDateField = None


class MdocSearchResponse(BaseModel):
    rows: list[MdocSearchRowRead]
    # OTIS's own "N matches found"; not trustworthy (it has said 0 for a real hit).
    total: Optional[int] = None
    # True when max_pages ran out while OTIS still had a next page.
    truncated: bool = False


class MdocPhotoImportRequest(BaseModel):
    """`photo_url` is the `data:` URI returned by /lookup or /parse."""

    photo_url: str
    member_id: uuid.UUID
    universe_id: uuid.UUID
