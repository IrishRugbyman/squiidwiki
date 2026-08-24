import re
import uuid
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import FuzzyDateField

# A saved OTIS profile page is a few hundred KB; this is headroom, not a target.
MAX_PASTED_HTML_CHARS = 4_000_000


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


class MdocPhotoImportRequest(BaseModel):
    """`photo_url` is the `data:` URI returned by /lookup or /parse."""

    photo_url: str
    member_id: uuid.UUID
    universe_id: uuid.UUID
