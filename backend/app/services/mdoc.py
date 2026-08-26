"""Fetch and parse MDOC OTIS offender profiles.

OTIS was rebuilt some time before 2026-08. Three things changed, and all three
break any code written against the old site:

1. **Nothing is addressable.** The old ``otis2profile.aspx?mdocNumber=NNNNNN``
   URLs 404. A profile is now held in *session state*: ``/OTIS2/Profile``
   renders whoever the session last loaded, and serves the search form to
   anyone else. There is no permalink to a profile and no way to link one.
2. **Reaching a profile takes three requests**, in order, on one cookie jar.
   See ``fetch_mdoc_profile``. Posting ``action:LoadProfile`` without a search
   already in session bounces back to the form - verified, there is no shortcut.
3. **The photo is inlined** as a ``data:`` URI in the profile HTML. The old
   ``ProfileImage.aspx`` endpoint is gone, so a mugshot can no longer be
   fetched on its own, and the declared MIME type is wrong (it says
   ``image/gif`` for what is plainly a JPEG). We sniff the magic bytes.

The upside of the rebuild: the markup is now clean tables with stable
``label for="Results_ProfileData_*"`` ids, so the old "flatten the page to text
and slice between known labels" hack is gone, and the page exposes far more
than it used to - aliases, marks/scars/tattoos, SID, and full per-sentence
detail including court file number, county and conviction type.

**Reaching OTIS at all.** mdocweb.state.mi.us sits behind Cloudflare, which
403s this server's Helsinki IP on every path. Set ``MDOC_PROXY`` (or pass
``proxy=``) to route through a SOCKS5 proxy that egresses somewhere unblocked -
``infra/otis-tunnel.sh`` opens one over a reverse SSH forward. Without it every
fetch here raises ``MdocFetchError``; parsing supplied HTML still works.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import datetime
import re
from dataclasses import dataclass, field, replace
from urllib.parse import unquote_to_bytes, urlparse

import httpx
from bs4 import BeautifulSoup, Tag

from app.core.config import settings
from app.core.enums import DatePrecision
from app.core.fuzzy_date import FuzzyDate

BASE_URL = "https://mdocweb.state.mi.us/OTIS2"
ALLOWED_HOSTS = {"mdocweb.state.mi.us"}
HTTP_TIMEOUT = httpx.Timeout(40.0, connect=15.0)

# OTIS returns the search form rather than an error for a session it doesn't
# like, so every step is checked against the page title instead of the status.
SEARCH_TITLE = "OTIS Offender Search"
RESULTS_TITLE = "Results Page"
PROFILE_TITLE = "Offender Profile"

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# Every field the search form posts. OffenderStatus is the one that matters:
# the form defaults to "Active Offenders", which silently omits anyone
# discharged - which is most of the people we look up.
BLANK_SEARCH: dict[str, str] = {
    "LastName": "",
    "FirstName": "",
    "MDOCNumber": "",
    "Sex": "Either",
    "Race": "All",
    "Age": "",
    "OffenderStatus": "All",
    "MarksScarsTattoos": "",
}

# Biographical fields, keyed by the suffix of their <label for> id.
_BIO_FIELDS = {
    "mdoc_number": "MDOCNum",
    "sid_number": "SIDNum",
    "race": "Race",
    "sex": "Gender",  # the id still says Gender; the page renders "Sex:"
    "hair": "HairColor",
    "eyes": "EyeColor",
    "height": "Height",
    "weight": "Weight",
}

# (magic bytes, real content type). The declared type on the data URI is not
# trustworthy, so it is never consulted.
_IMAGE_MAGIC: tuple[tuple[bytes, str], ...] = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
)


class MdocParseError(Exception):
    """The page was fetched but isn't an OTIS profile we can read."""


class MdocFetchError(Exception):
    """OTIS couldn't be reached, or didn't return the page we asked for."""


@dataclass(frozen=True)
class MdocPhoto:
    """A mugshot decoded out of the profile page's inline data URI."""

    data: bytes
    content_type: str

    def as_data_uri(self) -> str:
        b64 = base64.b64encode(self.data).decode("ascii")
        return f"data:{self.content_type};base64,{b64}"


@dataclass(frozen=True)
class MdocSentence:
    """One row of the Prison Sentences or Probation Sentences section."""

    kind: str  # "prison" | "probation"
    active: bool
    offense: str | None = None
    mcl: list[str] = field(default_factory=list)
    court_file: str | None = None
    county: str | None = None
    conviction_type: str | None = None
    minimum_sentence: str | None = None
    maximum_sentence: str | None = None
    date_of_offense: FuzzyDate | None = None
    date_of_sentence: FuzzyDate | None = None
    date_of_discharge: FuzzyDate | None = None
    discharge_reason: str | None = None


@dataclass(frozen=True)
class MdocSearchResult:
    """One row of the OTIS results list.

    Deliberately not an MdocProfile: the results table carries only what OTIS
    chooses to show in a list, and a name search is a *lead*, not an
    identification. Load the profile by `mdoc_number` to get the rest.
    """

    mdoc_number: str
    last_name: str | None = None
    first_name: str | None = None
    dob: FuzzyDate | None = None
    sex: str | None = None
    race: str | None = None
    status: str | None = None


@dataclass(frozen=True)
class MdocProfile:
    legal_name: str
    dob: FuzzyDate
    mdoc_number: str | None = None
    sid_number: str | None = None
    race: str | None = None
    sex: str | None = None
    hair: str | None = None
    eyes: str | None = None
    height: str | None = None
    weight: str | None = None
    image_date: FuzzyDate | None = None
    status: str | None = None
    facility: str | None = None
    security_level: str | None = None
    earliest_release_date: FuzzyDate | None = None
    # OTIS labels this "Discharge Date" whatever the offender's status, but it
    # means two different things: for someone still serving it is the *maximum*
    # discharge date (the latest they could be released), and for someone
    # already out it is the date they actually discharged. Read it together
    # with `status`; never present it as one or the other without checking.
    discharge_date: FuzzyDate | None = None
    aliases: list[str] = field(default_factory=list)
    marks: list[str] = field(default_factory=list)
    sentences: list[MdocSentence] = field(default_factory=list)
    photo: MdocPhoto | None = None

    @property
    def max_discharge_date(self) -> FuzzyDate | None:
        """`discharge_date`, but only when it is still a projection.

        Once someone is discharged the same field is a historical fact, not a
        maximum, and returning it as a max would misdate them by years.
        """
        if self.status and self.status.strip().lower() == "discharged":
            return None
        return self.discharge_date


@dataclass(frozen=True)
class MdocSpell:
    """One incarceration spell, assembled from what OTIS says about a sentence.

    Field names are `MemberIncarcerationCreate`'s rather than OTIS's, so this
    can be posted at `/members/{id}/incarcerations` unchanged. Deriving it here
    keeps the knowledge of what each OTIS field means in one place - the client
    that shows the profile should not have to know that "Discharge Date" means
    two different things depending on the status above it.
    """

    from_date: FuzzyDate | None = None
    to_date: FuzzyDate | None = None
    earliest_release_date: FuzzyDate | None = None
    max_discharge_date: FuzzyDate | None = None
    life_sentence: bool = False
    facility: str | None = None
    case_id: str | None = None
    notes: str | None = None


_LIFE_TERM = re.compile(r"\blife\b", re.IGNORECASE)


def _looks_like_life(sentence: MdocSentence) -> bool:
    """True when OTIS gives the maximum as a life term.

    Only the maximum is read. An indeterminate term can carry a minimum in
    years and still top out at life, and it is the maximum that decides whether
    a release date exists at all.
    """
    return bool(sentence.maximum_sentence and _LIFE_TERM.search(sentence.maximum_sentence))


def _spell_notes(sentence: MdocSentence) -> str | None:
    """The sentence detail that has no column of its own, as plain lines.

    This text renders on the member page, so it names no source and hedges
    nothing: it states what the sentence was and stops.
    """
    lines: list[str] = []
    if sentence.offense:
        lines.append(f"Offense: {sentence.offense}")
    if sentence.mcl:
        lines.append("MCL " + " / ".join(sentence.mcl))
    if sentence.county:
        lines.append(f"County: {sentence.county}")
    if sentence.conviction_type:
        lines.append(f"Conviction type: {sentence.conviction_type}")
    if sentence.minimum_sentence or sentence.maximum_sentence:
        lo = sentence.minimum_sentence or "unspecified"
        hi = sentence.maximum_sentence or "unspecified"
        lines.append(f"Sentence: {lo} to {hi}")
    if sentence.date_of_offense:
        lines.append(f"Date of offense: {sentence.date_of_offense.display()}")
    if sentence.discharge_reason:
        lines.append(f"Discharge reason: {sentence.discharge_reason}")
    return "\n".join(lines) or None


def _started(spell: MdocSpell) -> datetime.date:
    """Sort key for "which open spell is the most recent"."""
    if spell.from_date is None:
        return datetime.date.min
    return spell.from_date.to_sortable_date() or datetime.date.min


_TERM_UNIT = re.compile(r"(\d+)\s*(year|month|day)s?", re.IGNORECASE)
_UNIT_DAYS = {"year": 365, "month": 30, "day": 1}


def _max_term_days(sentence: MdocSentence) -> float:
    """How long the sentence can run, in rough days, for ranking only.

    Approximate on purpose. This decides only which of several concurrent
    sentences is the controlling one, so 365-day years are precise enough and
    calendar arithmetic would be false precision.
    """
    raw = sentence.maximum_sentence or ""
    if _LIFE_TERM.search(raw):
        return float("inf")
    return float(sum(int(n) * _UNIT_DAYS[u.lower()] for n, u in _TERM_UNIT.findall(raw)))


def derive_spells(profile: MdocProfile) -> list[MdocSpell]:
    """Turn an OTIS profile into incarceration spells, one per prison sentence.

    Probation sentences are dropped, and that is a product rule rather than a
    simplification. Probation is not custody, and a spell row for one would read
    on the member page as time served - a false claim about a named living
    person. A profile with three probation terms and no prison time therefore
    yields zero spells, correctly. Do not loosen this filter to make an import
    look more productive; see docs/SCHEMA.md, "Incarceration Spells".

    The wrinkle is that OTIS splits the facts across two places. Each sentence
    row carries its own start and, once served, its own end. The projected
    release dates and the assigned facility live in the Status block instead,
    and belong to the offender rather than to any one sentence - concurrent
    sentences share them. They are therefore attached to exactly one spell - the
    controlling one, meaning the still-running sentence with the longest maximum
    term - so that someone serving three concurrent sentences yields one
    projected release rather than three duplicates on the calendar, and it sits
    on the count that actually determines the date.

    A discharged offender has an empty Status block, which is the whole reason
    this exists: their history is *only* in the sentence rows, and reading the
    Status block alone (as the member form used to) imported nothing at all.
    """
    prison = [s for s in profile.sentences if s.kind == "prison"]
    if not prison:
        # Nothing usable in the sentence sections - either the offender has none
        # or OTIS changed that markup. Fall back to the Status block so a
        # currently-serving prisoner still imports something.
        if profile.earliest_release_date or profile.max_discharge_date or profile.facility:
            return [
                MdocSpell(
                    earliest_release_date=profile.earliest_release_date,
                    max_discharge_date=profile.max_discharge_date,
                    facility=profile.facility,
                )
            ]
        return []

    spells = [
        MdocSpell(
            from_date=s.date_of_sentence,
            to_date=s.date_of_discharge,
            life_sentence=_looks_like_life(s),
            case_id=s.court_file,
            notes=_spell_notes(s),
        )
        for s in prison
    ]

    # Prefer a sentence OTIS itself calls active; fall back to merely undischarged,
    # since a row can lack a discharge date without sitting under an "Active" heading.
    running = [i for i, s in enumerate(prison) if spells[i].to_date is None and s.active]
    if not running:
        running = [i for i, sp in enumerate(spells) if sp.to_date is None]
    if running:
        # Longest maximum term first, because that is the sentence controlling
        # the release: concurrent sentences are handed down the same day, so a
        # start-date tiebreak alone lands the projection arbitrarily - it put a
        # 2051 max discharge on a two-year felony-firearm count next to the
        # 20-to-35 assault that actually decides the date.
        i = max(running, key=lambda i: (_max_term_days(prison[i]), _started(spells[i]), i))
        spells[i] = replace(
            spells[i],
            earliest_release_date=profile.earliest_release_date,
            max_discharge_date=profile.max_discharge_date,
            facility=profile.facility,
        )
    return spells


def is_allowed_mdoc_url(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    return host in ALLOWED_HOSTS


# --------------------------------------------------------------------------
# parsing
# --------------------------------------------------------------------------


def _clean(s: str | None) -> str | None:
    """Collapse whitespace; empty and non-breaking-space-only become None."""
    if s is None:
        return None
    out = re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip()
    return out or None


def _parse_mdoc_date(s: str) -> FuzzyDate:
    """MDOC dates are M/D/YYYY. Trailing junk (e.g. the "(52)" age beside a
    date of birth) is ignored.
    """
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if not m:
        raise ValueError(f"unrecognized MDOC date: {s!r}")
    month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return FuzzyDate(year=year, month=month, day=day, precision=DatePrecision.YMD, approx=False)


def _try_parse_date(raw: str | None) -> FuzzyDate | None:
    raw = _clean(raw)
    if not raw or raw.lower() in {"n/a", "none", "life", "indefinite"}:
        return None
    try:
        return _parse_mdoc_date(raw)
    except ValueError:
        return None


def _value_beside(cell: Tag | None) -> str | None:
    """OTIS renders every field as two cells: the label, then the value."""
    if cell is None:
        return None
    sibling = cell.find_next_sibling("td")
    return _clean(sibling.get_text(" ", strip=True)) if sibling else None


def _bio_field(soup: BeautifulSoup, suffix: str) -> str | None:
    label = soup.find("label", attrs={"for": f"Results_ProfileData_{suffix}"})
    return _value_beside(label.find_parent("td")) if label else None


def _section_rows(soup: BeautifulSoup, section_id: str) -> list[Tag]:
    """Every <tr> between one <h4 id=...> section heading and the next.

    The page is one flat table, so sections aren't nested containers - they're
    delimited by their headings, and we walk siblings until the next one.
    """
    heading = soup.find("h4", id=section_id)
    if heading is None:
        return []
    start = heading.find_parent("tr")
    if start is None:
        return []
    rows: list[Tag] = []
    for sibling in start.find_next_siblings("tr"):
        if sibling.find("h4"):
            break
        rows.append(sibling)
    return rows


def _section_list(soup: BeautifulSoup, section_id: str) -> list[str]:
    """A section that is just a list of single-cell rows (Aliases, Marks)."""
    out: list[str] = []
    for row in _section_rows(soup, section_id):
        text = _clean(row.get_text(" ", strip=True))
        if text and text.lower() not in {"none", "no data"}:
            out.append(text)
    return out


def _labelled_pairs(scope: Tag) -> dict[str, str]:
    """Collect every "Label:" / value cell pair inside `scope`."""
    pairs: dict[str, str] = {}
    for row in scope.find_all("tr"):
        cells = row.find_all("td", recursive=False) or row.find_all("td")
        if len(cells) < 2:
            continue
        key = _clean(cells[0].get_text(" ", strip=True))
        if not key or not key.endswith(":"):
            continue
        value = _clean(cells[1].get_text(" ", strip=True))
        key = key[:-1].strip()
        if key not in pairs and value is not None:
            pairs[key] = value
    return pairs


def _status_fields(soup: BeautifulSoup) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for row in _section_rows(soup, "Status"):
        pairs.update({k: v for k, v in _labelled_pairs(row).items() if k not in pairs})
    return pairs


def _parse_sentences(soup: BeautifulSoup, section_id: str, kind: str) -> list[MdocSentence]:
    """Read one sentences section.

    Layout: an <h5> reading "Active" or "Inactive", then alternating rows - a
    bare "Sentence N" marker followed by a row holding that sentence's tables.
    """
    sentences: list[MdocSentence] = []
    active = True
    pending = False

    for row in _section_rows(soup, section_id):
        heading = row.find("h5")
        if heading is not None:
            active = _clean(heading.get_text()) == "Active"
            pending = False
            continue

        if not row.find("tr"):  # a marker row, or the literal "none"
            text = (_clean(row.get_text(" ", strip=True)) or "").lower()
            pending = text.startswith("sentence")
            continue

        if not pending:
            continue
        pending = False

        f = _labelled_pairs(row)
        mcl_raw = f.get("MCL#") or ""
        sentences.append(
            MdocSentence(
                kind=kind,
                active=active,
                offense=f.get("Offense"),
                mcl=[p.strip() for p in mcl_raw.split("/") if p.strip()],
                court_file=f.get("Court File#"),
                county=f.get("County"),
                conviction_type=f.get("Conviction Type"),
                minimum_sentence=f.get("Minimum Sentence"),
                maximum_sentence=f.get("Maximum Sentence"),
                date_of_offense=_try_parse_date(f.get("Date of Offense")),
                date_of_sentence=_try_parse_date(f.get("Date of Sentence")),
                date_of_discharge=_try_parse_date(f.get("Date of Discharge")),
                discharge_reason=f.get("Discharge Reason"),
            )
        )
    return sentences


def _sniff_image_type(data: bytes) -> str | None:
    for magic, content_type in _IMAGE_MAGIC:
        if data.startswith(magic):
            return content_type
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def decode_data_uri(uri: str) -> MdocPhoto:
    """Decode a ``data:`` URI into bytes plus its *real* content type.

    The type declared in the URI is ignored: OTIS labels its JPEG mugshots
    ``image/gif``. Raises ValueError on anything that isn't a decodable image.
    """
    if not uri.startswith("data:"):
        raise ValueError("not a data: URI")
    header, _, payload = uri[len("data:") :].partition(",")
    if not payload:
        raise ValueError("data: URI has no payload")
    try:
        if header.rstrip().endswith(";base64"):
            data = base64.b64decode(payload, validate=False)
        else:
            data = unquote_to_bytes(payload)
    except (binascii.Error, ValueError) as e:
        raise ValueError(f"data: URI payload isn't decodable: {e}") from e

    content_type = _sniff_image_type(data)
    if content_type is None:
        raise ValueError("data: URI payload is not a recognized image format")
    return MdocPhoto(data=data, content_type=content_type)


def _extract_photo(soup: BeautifulSoup) -> MdocPhoto | None:
    """Pull the mugshot out of the profile.

    OTIS marks it ``alt="<NAME> Image"``, but it is also the only inline image
    on the page, so we fall back to the first decodable data URI rather than
    depending on the alt text staying put.
    """
    candidates = [
        src
        for src in (img.get("src") or "" for img in soup.find_all("img"))
        if src.startswith("data:image/")
    ]
    for src in candidates:
        try:
            return decode_data_uri(src)
        except ValueError:
            continue
    return None


def parse_mdoc_results(html: str) -> tuple[list[MdocSearchResult], int | None, bool]:
    """Parse an OTIS results page.

    Returns ``(rows, total_matches, has_next_page)``.

    ``total_matches`` comes from the page's own "N matches found" line and is
    **not trustworthy** - OTIS has reported 0 for a number whose profile then
    loaded perfectly well. It is returned for information; never branch on it.
    Trust the rows.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows: list[MdocSearchResult] = []
    for btn in soup.find_all("input", attrs={"name": "action:LoadProfile"}):
        number = _clean(btn.get("value"))
        if not number:
            continue
        tr = btn.find_parent("tr")
        cells = [_clean(td.get_text(" ", strip=True)) for td in tr.find_all("td")] if tr else []
        # Column order is the results header: number, last, first, dob, sex,
        # race, MCL, location, status, ... Short rows are padded rather than
        # indexed defensively at every use.
        padded = (cells + [None] * 9)[:9]
        rows.append(
            MdocSearchResult(
                mdoc_number=number,
                last_name=padded[1],
                first_name=padded[2],
                dob=_try_parse_date(padded[3]),
                sex=padded[4],
                race=padded[5],
                status=padded[8],
            )
        )

    m = re.search(r"([\d,]+)\s+matches found", html)
    total = int(m.group(1).replace(",", "")) if m else None
    has_next = bool(soup.find("input", attrs={"name": "action:Pagination", "value": "Next"}))
    return rows, total, has_next


def _normalize_name(s: str) -> str:
    """OTIS renders names in caps, occasionally with a doubled space where a
    middle name is missing. Title-case, and handle 'LAST, FIRST' just in case.
    """
    s = re.sub(r"\s+", " ", s).strip()
    if "," in s:
        last, _, rest = s.partition(",")
        last, rest = last.strip(), rest.strip()
        return f"{rest.title()} {last.title()}".strip() if rest else last.title()
    return s.title()


def parse_mdoc_html(html: str, page_url: str | None = None) -> MdocProfile:
    """Parse an OTIS profile page.

    `page_url` is accepted for call-site compatibility and is unused: the photo
    is inline, so there is no longer a relative URL to resolve against.
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    name_cell = soup.find("td", id="Name")
    name_raw = _value_beside(name_cell)
    if not name_raw:
        raise MdocParseError(
            "Couldn't read 'Name' - this doesn't look like an OTIS profile page. "
            "A search that matched nobody, or an expired session, returns the "
            "search form instead of a profile."
        )

    dob_raw = _bio_field(soup, "DateOfBirth")
    if not dob_raw:
        raise MdocParseError("Couldn't read 'Date of Birth' from the OTIS profile")
    try:
        dob = _parse_mdoc_date(dob_raw)
    except ValueError as e:
        raise MdocParseError(f"Couldn't parse Date of Birth: {e}") from e

    status = _status_fields(soup)

    return MdocProfile(
        legal_name=_normalize_name(name_raw),
        dob=dob,
        image_date=_try_parse_date(_bio_field(soup, "ImageDate")),
        status=status.get("Current Status"),
        facility=status.get("Assigned Location"),
        security_level=status.get("Security Level"),
        earliest_release_date=_try_parse_date(status.get("Earliest Release Date")),
        discharge_date=_try_parse_date(status.get("Discharge Date")),
        aliases=_section_list(soup, "Aliases"),
        marks=_section_list(soup, "Marks"),
        sentences=(
            _parse_sentences(soup, "Sentences", "prison")
            + _parse_sentences(soup, "Probation", "probation")
        ),
        photo=_extract_photo(soup),
        **{attr: _bio_field(soup, suffix) for attr, suffix in _BIO_FIELDS.items()},
    )


# --------------------------------------------------------------------------
# fetching
# --------------------------------------------------------------------------


def _configured_proxy() -> str | None:
    """`MDOC_PROXY` from settings, or None when it isn't configured.

    `settings` is built once at import, so changing `MDOC_PROXY` needs a
    backend restart. Opening and closing the tunnel it points at does not:
    the address stays the same, and only whether anything is listening on it
    changes, which surfaces as a `MdocFetchError` per request.
    """
    return settings.mdoc_proxy or None


def _title_of(html: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    return _clean(m.group(1)) or "" if m else ""


class _OtisBounced(Exception):
    """LoadProfile came back as the search form: a session OTIS didn't accept.

    Transient and says nothing about the offender, so it is retried rather than
    surfaced. Kept separate from MdocFetchError precisely so that the definitive
    failures - no such number, proxy unreachable - are not retried.
    """


# OTIS rejects a freshly-built session often enough to matter: measured 2
# failures in 8 single attempts against a profile that exists and loads fine on
# the next try. One attempt therefore meant roughly one import in four dying on
# an error toast, which is what this exists to stop.
PROFILE_ATTEMPTS = 3
PROFILE_RETRY_DELAYS = (0.6, 1.5)


async def _load_profile_once(number: str, proxy: str | None) -> str:
    """One full session walk on a clean cookie jar. Returns the profile HTML.

    A fresh client per attempt is the point: what fails is the session, so
    reusing its cookies would just reproduce the same rejection.
    """
    async with httpx.AsyncClient(
        proxy=proxy,
        timeout=HTTP_TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        try:
            await client.get(f"{BASE_URL}/Search")
            results = await client.post(
                f"{BASE_URL}/Search",
                data={**BLANK_SEARCH, "MDOCNumber": number, "action:Search": "Search"},
            )
            profile = await client.post(f"{BASE_URL}/Results", data={"action:LoadProfile": number})
        except httpx.HTTPError as e:
            # A transport failure, not an HTTP status: almost always the proxy.
            # Not retried - a proxy that is down stays down, and the message
            # below is more use than three slow repeats of it.
            raise MdocFetchError(
                f"Couldn't reach OTIS ({e}). It 403s this server's own IP, so "
                "MDOC_PROXY must point at a SOCKS5 proxy that egresses "
                "elsewhere, with something actually listening on it "
                "(infra/otis-tunnel.sh opens one)."
            ) from e

    # OTIS raises rather than 404s for a number that doesn't exist. Definitive,
    # so it is raised straight out of the retry loop rather than retried.
    if profile.status_code >= 500:
        raise MdocFetchError(
            f"OTIS has no offender with MDOC number {number} "
            f"(it answered {profile.status_code} {_title_of(profile.text)!r})."
        )
    if profile.status_code != 200 or PROFILE_TITLE not in _title_of(profile.text):
        raise _OtisBounced(
            f"({profile.status_code}, {_title_of(profile.text)!r}; the search "
            f"step returned {_title_of(results.text)!r})"
        )
    return profile.text


async def fetch_mdoc_profile(mdoc_number: str, proxy: str | None = None) -> MdocProfile:
    """Look an offender up by MDOC number and return their parsed profile.

    Three requests on one cookie jar, in this order - there is no shortcut,
    because ``action:LoadProfile`` is only honoured once a search has put a
    result set into the session:

        GET  /OTIS2/Search                            -> session cookies
        POST /OTIS2/Search   + action:Search          -> the results list
        POST /OTIS2/Results  + action:LoadProfile=N   -> the profile

    OTIS answers 200 with the search form when it rejects a step rather than
    signalling an error, so each step is verified by page title.

    The search step exists only to establish session state, and **nothing is
    decided from what it returns**, because what it returns is not trustworthy:
    for one real offender it reported "0 matches found" on one attempt and
    bounced to the search form on the next, yet ``LoadProfile`` fetched that
    profile correctly both times. Gating on it rejects lookups that work.

    ``LoadProfile`` is the authoritative step: it returns the offender asked
    for regardless of what the search listed, and answers 500 "Runtime Error"
    when no such number exists.
    """
    number = str(mdoc_number).strip()
    if not number.isdigit():
        raise ValueError("MDOC number must be digits")

    proxy = proxy or _configured_proxy()
    last_bounce = ""
    for attempt in range(PROFILE_ATTEMPTS):
        try:
            html = await _load_profile_once(number, proxy)
            break
        except _OtisBounced as e:
            last_bounce = str(e)
            if attempt + 1 < PROFILE_ATTEMPTS:
                await asyncio.sleep(PROFILE_RETRY_DELAYS[attempt])
    else:
        raise MdocFetchError(
            f"OTIS did not load a profile for MDOC number {number} after "
            f"{PROFILE_ATTEMPTS} attempts {last_bounce}. It rejects a new "
            "session intermittently; try again in a moment."
        )

    parsed = parse_mdoc_html(html)
    # Belt and braces. OTIS holds the selected offender in session state, so a
    # bug or a session mix-up upstream could hand back somebody else - and
    # attaching the wrong person's convictions to a member is the worst thing
    # this code could quietly do. Verified correct today; checked anyway.
    if parsed.mdoc_number and parsed.mdoc_number != number:
        raise MdocFetchError(
            f"OTIS returned MDOC number {parsed.mdoc_number} when asked for "
            f"{number}; refusing to use a profile that may be someone else's."
        )
    return parsed


async def search_mdoc(
    last_name: str = "",
    first_name: str = "",
    *,
    max_pages: int = 10,
    proxy: str | None = None,
) -> list[MdocSearchResult]:
    """Search OTIS by name and return every result row, following pagination.

    OTIS pages 20 rows at a time. `max_pages` caps that at 200 rows by default,
    because a bare surname can return hundreds and each page is a round trip
    through the proxy. When the cap is hit the list is simply short - it is
    logged in no way OTIS can tell us about, so **check `len()` against what you
    expected** rather than assuming completeness.

    A name search is a lead, not an identification. Several people share a name,
    and OTIS holds only those who passed through the Department of Corrections:
    county jail, federal custody and juvenile records never appear here, so an
    empty result does not mean someone has no record.
    """
    last_name, first_name = last_name.strip(), first_name.strip()
    if not last_name and not first_name:
        raise ValueError("Give at least a last name or a first name")

    async with httpx.AsyncClient(
        proxy=proxy or _configured_proxy(),
        timeout=HTTP_TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        try:
            await client.get(f"{BASE_URL}/Search")
            resp = await client.post(
                f"{BASE_URL}/Search",
                data={
                    **BLANK_SEARCH,
                    "LastName": last_name,
                    "FirstName": first_name,
                    "action:Search": "Search",
                },
            )
            resp.raise_for_status()

            out: list[MdocSearchResult] = []
            seen: set[str] = set()
            for _ in range(max_pages):
                rows, _total, has_next = parse_mdoc_results(resp.text)
                # Guard against a pagination that loops back on itself rather
                # than advancing, which would otherwise spin to max_pages.
                fresh = [r for r in rows if r.mdoc_number not in seen]
                if not fresh:
                    break
                seen.update(r.mdoc_number for r in fresh)
                out.extend(fresh)
                if not has_next:
                    break
                resp = await client.post(f"{BASE_URL}/Results", data={"action:Pagination": "Next"})
                resp.raise_for_status()
        except httpx.HTTPError as e:
            raise MdocFetchError(
                f"Couldn't reach OTIS ({e}). It 403s this server's own IP, so "
                "MDOC_PROXY must point at a SOCKS5 proxy that egresses "
                "elsewhere (infra/otis-tunnel.sh opens one)."
            ) from e
    return out


async def fetch_mdoc_image(photo_url: str) -> tuple[bytes, str]:
    """Return (bytes, content_type) for an offender photo.

    Since the rebuild these arrive as inline ``data:`` URIs rather than links,
    so no request is made in the normal case. HTTP URLs on an MDOC host are
    still accepted for anything holding an old link.
    """
    if photo_url.startswith("data:"):
        try:
            photo = decode_data_uri(photo_url)
        except ValueError as e:
            raise ValueError(f"Couldn't decode the inline MDOC photo: {e}") from e
        return photo.data, photo.content_type

    if not is_allowed_mdoc_url(photo_url):
        raise ValueError("Photo URL is not on an MDOC offender-search domain")
    async with httpx.AsyncClient(
        proxy=_configured_proxy(), timeout=HTTP_TIMEOUT, follow_redirects=True
    ) as client:
        try:
            resp = await client.get(photo_url)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise MdocFetchError(str(e)) from e

    # Trust sniffed bytes over the declared header - OTIS gets this wrong.
    sniffed = _sniff_image_type(resp.content)
    if sniffed:
        return resp.content, sniffed
    ct = (resp.headers.get("content-type") or "").split(";")[0].strip().lower()
    return resp.content, "image/jpeg" if ct in ("", "image/jpg") else ct
