"""Parser for MDOC OTIS offender-profile pages.

Extracts only what we use elsewhere in the app:
- legal full name
- date of birth
- earliest release date
- maximum discharge date
- assigned facility

The OTIS page renders label/value pairs as glued text — e.g. ``Name:MALIEK
THOMAS WILLIAMS`` and ``...FacilityMaximum Discharge Date:10/14/2110``. The
parser flattens the page text, finds every known label by name, and slices
each value out of the substring up to the next known label.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.enums import DatePrecision
from app.core.fuzzy_date import FuzzyDate

ALLOWED_HOSTS = {"mdocweb.state.mi.us", "offendersearch.michigan.gov"}
HTTP_TIMEOUT = httpx.Timeout(15.0, connect=5.0)

# All labels we recognize on the page. Order doesn't matter for parsing, but
# every label that can immediately follow a value of interest MUST be present
# so the slice terminates correctly. Listed longest-first within the regex
# alternation to prevent prefix matches (e.g. "Date of Birth" before "Date").
KNOWN_LABELS = [
    "MDOC Number",
    "SID Number",
    "Name",
    "Racial Identification",
    "Gender",
    "Hair",
    "Eyes",
    "Height",
    "Weight",
    "Date of Birth",
    "Image Date",
    "Current Status",
    "Earliest Release Date",
    "Assigned Location",
    "Maximum Discharge Date",
    "Security Level",
]


class MdocParseError(Exception):
    """Raised when the MDOC page can't be parsed for one of our required fields."""


class MdocFetchError(Exception):
    """Raised when the upstream MDOC page can't be fetched."""


class MdocProfile:
    def __init__(
        self,
        legal_name: str,
        dob: FuzzyDate,
        earliest_release_date: FuzzyDate | None,
        max_discharge_date: FuzzyDate | None,
        facility: str | None,
        photo_url: str | None,
    ):
        self.legal_name = legal_name
        self.dob = dob
        self.earliest_release_date = earliest_release_date
        self.max_discharge_date = max_discharge_date
        self.facility = facility
        self.photo_url = photo_url


def is_allowed_mdoc_url(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    return host in ALLOWED_HOSTS


def _parse_mdoc_date(s: str) -> FuzzyDate:
    """MDOC dates are MM/DD/YYYY. Returns YMD precision."""
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if not m:
        raise ValueError(f"unrecognized MDOC date: {s!r}")
    month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return FuzzyDate(year=year, month=month, day=day, precision=DatePrecision.YMD, approx=False)


def _extract_label_values(text: str) -> dict[str, str]:
    """Walk the flat page text and slice out each known label's value.

    Each value starts right after ``Label:`` and ends where the next known
    label begins (or end of text). Whitespace is collapsed and surrounding
    junk trimmed.
    """
    # Sort longest-first so "Date of Birth" wins against "Date".
    sorted_labels = sorted(KNOWN_LABELS, key=len, reverse=True)
    pattern = re.compile(
        r"(?P<label>" + "|".join(re.escape(label) for label in sorted_labels) + r")\s*:",
        re.IGNORECASE,
    )

    matches = list(pattern.finditer(text))
    out: dict[str, str] = {}
    for i, m in enumerate(matches):
        label = m.group("label")
        # Canonicalize back to the casing in KNOWN_LABELS
        canonical = next((k for k in KNOWN_LABELS if k.lower() == label.lower()), label)
        value_start = m.end()
        value_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        value = text[value_start:value_end].strip()
        # Collapse whitespace runs
        value = re.sub(r"\s+", " ", value)
        if canonical not in out and value:
            out[canonical] = value
    return out


def parse_mdoc_html(html: str, page_url: str | None = None) -> MdocProfile:
    soup = BeautifulSoup(html, "html.parser")
    # Remove scripts/styles so their content doesn't leak into the visible text.
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    photo_url = _extract_photo_url(soup, page_url)
    text = soup.get_text(" ", strip=True)
    fields = _extract_label_values(text)

    name_raw = fields.get("Name")
    if not name_raw:
        raise MdocParseError("Couldn't read 'Name' from MDOC page")
    legal_name = _normalize_name(name_raw)

    dob_raw = fields.get("Date of Birth")
    if not dob_raw:
        raise MdocParseError("Couldn't read 'Date of Birth' from MDOC page")
    try:
        dob = _parse_mdoc_date(dob_raw)
    except ValueError as e:
        raise MdocParseError(f"Couldn't parse Date of Birth: {e}") from e

    earliest_fd = _try_parse_date(fields.get("Earliest Release Date"))
    max_fd = _try_parse_date(fields.get("Maximum Discharge Date"))
    facility = fields.get("Assigned Location") or None

    return MdocProfile(
        legal_name=legal_name,
        dob=dob,
        earliest_release_date=earliest_fd,
        max_discharge_date=max_fd,
        facility=facility,
        photo_url=photo_url,
    )


def _extract_photo_url(soup: BeautifulSoup, page_url: str | None) -> str | None:
    """Find the offender photo. OTIS marks it with alt='Photo of Offender'
    (or similar), or the src lives under /OTIS2/.../photos/.
    Returns an absolute URL on an allowed MDOC host, or None.
    """
    candidates: list[str] = []
    for img in soup.find_all("img"):
        alt = (img.get("alt") or "").lower()
        src = img.get("src") or ""
        if not src:
            continue
        if "photo of offender" in alt or "offender" in alt:
            candidates.append(src)
        elif re.search(r"(?:^|/)(?:photos?|images?)/", src, re.I) and re.search(r"\.(jpe?g|png)(\?|$)", src, re.I):
            candidates.append(src)
    if not candidates:
        return None
    src = candidates[0]
    abs_url = urljoin(page_url or "", src) if page_url else src
    # Reject anything that resolved to an off-allowlist host (e.g. tracking pixel).
    parsed = urlparse(abs_url)
    if parsed.hostname and parsed.hostname.lower() not in ALLOWED_HOSTS:
        return None
    return abs_url


def _try_parse_date(raw: str | None) -> FuzzyDate | None:
    if not raw:
        return None
    if raw.lower() in ("n/a", "none", "", "life", "indefinite"):
        return None
    try:
        return _parse_mdoc_date(raw)
    except ValueError:
        return None


def _normalize_name(s: str) -> str:
    """MDOC may render names as 'LAST, FIRST MIDDLE' or 'FIRST MIDDLE LAST'.
    Title-case the result either way.
    """
    s = s.strip()
    if "," in s:
        last, _, rest = s.partition(",")
        rest = rest.strip()
        last = last.strip()
        if rest:
            return f"{rest.title()} {last.title()}"
        return last.title()
    return s.title()


async def fetch_mdoc_profile(url: str) -> MdocProfile:
    if not is_allowed_mdoc_url(url):
        raise ValueError("URL is not on an MDOC offender-search domain")
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise MdocFetchError(str(e)) from e
    return parse_mdoc_html(resp.text, page_url=str(resp.url))


async def fetch_mdoc_image(photo_url: str) -> tuple[bytes, str]:
    """Download an offender photo. Returns (bytes, content_type).
    Rejects URLs not on an allowed MDOC host.
    """
    if not is_allowed_mdoc_url(photo_url):
        raise ValueError("Photo URL is not on an MDOC offender-search domain")
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
        try:
            resp = await client.get(photo_url)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise MdocFetchError(str(e)) from e
    ct = (resp.headers.get("content-type") or "").split(";")[0].strip().lower() or "image/jpeg"
    # MDOC sometimes serves the non-standard "image/jpg" — normalize to "image/jpeg".
    if ct == "image/jpg":
        ct = "image/jpeg"
    return resp.content, ct
