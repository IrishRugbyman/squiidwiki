import uuid
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import FuzzyDateField

# A saved OTIS profile page is a few hundred KB; this is headroom, not a target.
MAX_PASTED_HTML_CHARS = 4_000_000


class MdocLookupRequest(BaseModel):
    url: str


class MdocParseRequest(BaseModel):
    """Parse HTML the caller already has, instead of fetching it.

    The server cannot reach OTIS: mdocweb.state.mi.us returns a Cloudflare 403
    to this host's IP, so `/mdoc/lookup` fails before it ever parses anything.
    This lets a browser that *can* reach OTIS supply the page instead.

    `page_url` is optional and only used to resolve a relative photo `src` to an
    absolute URL; the parser rejects any that resolves off the MDOC allowlist.
    """

    html: str = Field(min_length=1, max_length=MAX_PASTED_HTML_CHARS)
    page_url: Optional[str] = None


class MdocProfileResponse(BaseModel):
    legal_name: str
    dob: FuzzyDateField
    earliest_release_date: FuzzyDateField = None
    max_discharge_date: FuzzyDateField = None
    facility: Optional[str] = None
    photo_url: Optional[str] = None


class MdocPhotoImportRequest(BaseModel):
    photo_url: str
    member_id: uuid.UUID
    universe_id: uuid.UUID
