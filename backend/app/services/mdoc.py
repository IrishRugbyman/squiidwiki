"""Fetch and parse MDOC OTIS offender profiles.

OTIS was rebuilt some time before 2026-08. Three things changed, and all three
break any code written against the old site:

1. **Nothing is addressable.** The old ``otis2profile.aspx?mdocNumber=NNNNNN``
   URLs 404. A profile is now held in *session state*: ``/OTIS2/Profile``
   renders whoever the session last loaded, and serves the search form to
   anyone else. There is no permalink to a profile and no way to link one.
2. **Reaching a profile takes three requests**, in order, on one cookie jar.
   See ``OtisSession.profile``. Posting ``action:LoadProfile`` without a search
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

**The move of 2026-10-31.** OTIS left ``mdocweb.state.mi.us/OTIS2`` for
``mdoc-offendersearch.michigan.gov``, and the old address now redirects. Two
things broke at once and failed silently, with no error and no rows: a POST to
the old address is redirected as a GET, which drops the form, and the search
form gained an ASP.NET anti-forgery token (``__RequestVerificationToken``)
that must be posted back with the search. ``_open_search`` handles both: it
reads the token off the search page and returns the host that page was
actually served from, so the POSTs follow the site if it moves again.

**The profile re-skin of 2026-11-04.** The profile page changed markup again, with no
change in content: section headings went from ``<h4>`` to ``<h2>`` (Marks stayed an
``<h4>``), the Active/Inactive sentence headings from ``<h5>`` to ``<h3>``, and a
probation sentence is announced by an ``<h4>`` with no id. The old parser found none of
the ``<h4 id=...>`` headings and returned a profile with no status, facility or
sentences, and a ``marks`` list that ran on through every heading after it, without
raising. ``parse_mdoc_html`` now locates sections by id on ``<h2>``/``<h4>``, ends one at
the next such heading, and raises ``MdocParseError`` when a section it reads is missing.
A probationer's or parolee's Status block carries "Supervision Begin Date" and
"Supervision Discharge Date" instead of release dates; those are not read.

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
import contextlib
import datetime
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field, replace
from urllib.parse import unquote_to_bytes, urlparse

import httpx
from bs4 import BeautifulSoup, Tag

from app.core.config import settings
from app.core.enums import DatePrecision
from app.core.fuzzy_date import FuzzyDate

BASE_URL = "https://mdoc-offendersearch.michigan.gov"
# The old host is kept for photo links stored before OTIS moved (2026-10-31).
ALLOWED_HOSTS = {"mdoc-offendersearch.michigan.gov", "mdocweb.state.mi.us"}
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

# Every field the search form posts, blank. OffenderStatus is ignored when
# searching by MDOC number (the only way this blank is used for a profile
# walk); for a real search OtisSession.search sets it, see DEFAULT_STATUS.
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


class MdocHttpError(MdocFetchError):
    """OTIS answered a search step with an HTTP error status.

    ``status`` is kept because callers act on it: 401/403/429 mean stop (OTIS or
    Cloudflare is refusing us), while a 5xx on one particular search term is that
    term's problem (an apostrophe breaks OTIS's own query) and not a reason to stop.
    """

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


class MdocBounced(MdocFetchError):
    """A search step came back as the search form instead of the results page.

    OTIS answers 200 with the form when it rejects a session, which reads as
    "no matches" if nobody checks the title.
    """


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
    location: str | None = None
    status: str | None = None
    parole_board_date: FuzzyDate | None = None
    max_date: FuzzyDate | None = None
    date_paroled: FuzzyDate | None = None


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


def _section_heading(soup: BeautifulSoup, section_id: str) -> Tag | None:
    """The heading of one profile section: an <h2> (an <h4> for Marks) with that id."""
    heading = soup.find(["h2", "h4"], id=section_id)
    return heading if isinstance(heading, Tag) else None


def _is_section_row(row: Tag) -> bool:
    """True for a row that opens a section. A sentence's own "Sentence N" <h4> has no id."""
    return row.find("h2") is not None or row.find("h4", id=True) is not None


def _section_rows(soup: BeautifulSoup, section_id: str) -> list[Tag]:
    """Every <tr> between one section heading and the next.

    The page is one flat table, so sections aren't nested containers - they're
    delimited by their headings, and we walk siblings until the next one.
    """
    heading = _section_heading(soup, section_id)
    if heading is None:
        return []
    start = heading.find_parent("tr")
    if start is None:
        return []
    rows: list[Tag] = []
    for sibling in start.find_next_siblings("tr"):
        if _is_section_row(sibling):
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

    Layout: an <h3> reading "Active" or "Inactive", then alternating rows - a
    "Sentence N" marker (bare text in prison sections, an <h4> in probation)
    followed by a row holding that sentence's tables.
    """
    sentences: list[MdocSentence] = []
    active = True
    pending = False

    for row in _section_rows(soup, section_id):
        heading = row.find("h3")
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


# Results-table header text (lower-cased) -> MdocSearchResult field. Columns are
# located by their header, not by position: the table lost its MCL column at
# some point before 2026-11 and a positional read then put the parole-board
# date in `status` without any error.
_RESULT_COLUMNS = {
    "offender number": "mdoc_number",
    "last name": "last_name",
    "first name": "first_name",
    "date of birth": "dob",
    "sex": "sex",
    "race": "race",
    "location": "location",
    "status": "status",
    "parole board jurisdiction date": "parole_board_date",
    "maximum date": "max_date",
    "date paroled": "date_paroled",
}
_RESULT_DATE_FIELDS = {"dob", "parole_board_date", "max_date", "date_paroled"}


def parse_mdoc_results(html: str) -> tuple[list[MdocSearchResult], int | None, bool]:
    """Parse an OTIS results page.

    Returns ``(rows, total_matches, has_next_page)``.

    ``total_matches`` comes from the page's own "N matches found" line and is
    **not trustworthy** - OTIS has reported 0 for a number whose profile then
    loaded perfectly well. It is returned for information; never branch on it.
    Trust the rows.

    Raises ``MdocParseError`` when the page lists offenders but has no
    recognisable header row, rather than guessing at column positions.
    """
    soup = BeautifulSoup(html, "html.parser")
    buttons = soup.find_all("input", attrs={"name": "action:LoadProfile"})
    columns: list[str | None] = []
    if buttons:
        header = soup.find("tr", class_="ResultsHeader")
        if header is None:
            raise MdocParseError("The OTIS results table has no header row; its layout changed")
        columns = [
            _RESULT_COLUMNS.get((_clean(td.get_text(" ", strip=True)) or "").lower())
            for td in header.find_all("td")
        ]
        if "mdoc_number" not in columns:
            raise MdocParseError("The OTIS results header has no 'Offender Number' column")

    rows: list[MdocSearchResult] = []
    for btn in buttons:
        number = _clean(btn.get("value"))
        if not number:
            continue
        tr = btn.find_parent("tr")
        cells = [_clean(td.get_text(" ", strip=True)) for td in tr.find_all("td")] if tr else []
        values: dict[str, object] = {}
        for field_name, text in zip(columns, cells, strict=False):
            if field_name is None or field_name == "mdoc_number":
                continue
            values[field_name] = (
                _try_parse_date(text) if field_name in _RESULT_DATE_FIELDS else text
            )
        rows.append(MdocSearchResult(mdoc_number=number, **values))

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


# Sections the parser reads. A genuinely empty one renders a "none" row and parses
# as empty; a missing heading means the layout moved, and is an error rather than
# a profile with silently empty fields.
_REQUIRED_SECTIONS = ("Status", "Aliases", "Marks", "Sentences", "Probation")


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

    for section_id in _REQUIRED_SECTIONS:
        if _section_heading(soup, section_id) is None:
            raise MdocParseError(
                f"The OTIS profile has no {section_id!r} section; the page layout changed "
                "and the parser needs updating."
            )
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


_TOKEN_RE = re.compile(r'<input[^>]*name="__RequestVerificationToken"[^>]*value="([^"]+)"', re.I)


def search_token(html: str) -> str | None:
    """The anti-forgery token the search form must post back, or None."""
    m = _TOKEN_RE.search(html)
    return m.group(1) if m else None


async def _open_search(client: httpx.AsyncClient) -> tuple[str, str]:
    """GET the search page and return (base URL it was served from, token).

    The base is taken from where the GET landed, not from ``BASE_URL``, because
    a redirect turns a POST into a GET and silently drops the form: that is how
    the move of 2026-10-31 broke every lookup without raising anything. A page
    with no token means the form changed again, and that is raised rather than
    searched past, since a search without it returns the bare form, which reads
    as "no matches".
    """
    page = await client.get(f"{BASE_URL}/Search")
    page.raise_for_status()
    token = search_token(page.text)
    if not token:
        raise MdocFetchError(
            f"The OTIS search page ({page.url}, {_title_of(page.text)!r}) carries no "
            "anti-forgery token; the form has changed and the lookup code needs updating."
        )
    base = str(page.url.copy_with(query=None, fragment=None)).rsplit("/Search", 1)[0]
    return base, token


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

# The form's own vocabularies, verbatim: a value outside these is posted as-is
# and OTIS answers with the bare form, which reads as "no matches".
SEX_VALUES = ("Either", "Male", "Female")
RACE_VALUES = (
    "All",
    "Native American",
    "Asian",
    "Black",
    "Latino",
    "Middle Eastern/North African",
    "Pacific Islander",
    "White",
)
STATUS_VALUES = (
    "Active Offenders",
    "All",
    "Prison",
    "Parole",
    "Probation",
    "Discharged",
    "Abscond1",
    "Abscond2",
)
DEFAULT_MAX_PAGES = 10
# Live, 2026-11-04: the widest option, and the only one that returns discharged
# offenders. "All" hides them and "Discharged" returns nothing. See OtisSession.search.
DEFAULT_STATUS = "Active Offenders"
OTIS_PAGE_SIZE = 25


@dataclass(frozen=True)
class MdocSearchOutcome:
    """What a search walked: the rows, OTIS's own count, and whether it stopped short.

    ``total`` is the page's "N matches found" line (None when absent) and, as
    ``parse_mdoc_results`` warns, is not trustworthy on its own. ``truncated``
    is exact: True only when ``max_pages`` ran out while OTIS still offered a
    next page, so the rows are a prefix of the result set.
    """

    rows: list[MdocSearchResult]
    total: int | None
    truncated: bool


def _check_choice(name: str, value: str, allowed: tuple[str, ...]) -> str:
    if value not in allowed:
        raise ValueError(f"{name} must be one of {', '.join(allowed)}; got {value!r}")
    return value


class OtisSession:
    """One OTIS session: one cookie jar, one anti-forgery token, many requests.

    Use as ``async with OtisSession() as otis:`` then ``await otis.search(...)``
    and ``await otis.profile(number)``. The search page is fetched once on
    entry, so several searches share one GET. OTIS holds the result set in
    session state, so a ``profile`` call runs its own search by number first and
    replaces whatever result list the session held: finish paging a search
    before asking for profiles.

    A session OTIS rejects is rebuilt from scratch (new client, new cookies,
    new token) by ``profile``; ``search`` does not retry, because a rejected
    search form parses as an honest-looking empty result only when the token is
    missing, and that case raises in ``_open_search``.
    """

    def __init__(self, proxy: str | None = None) -> None:
        self._proxy = proxy or _configured_proxy()
        self._stack: contextlib.AsyncExitStack | None = None
        self._client: httpx.AsyncClient | None = None
        self._base = ""
        self._token = ""

    async def __aenter__(self) -> OtisSession:
        await self._open()
        return self

    async def __aexit__(self, *exc) -> bool:
        await self._close()
        return False

    async def _open(self) -> None:
        stack = contextlib.AsyncExitStack()
        try:
            client = await stack.enter_async_context(
                httpx.AsyncClient(
                    proxy=self._proxy,
                    timeout=HTTP_TIMEOUT,
                    follow_redirects=True,
                    headers={"User-Agent": USER_AGENT},
                )
            )
            try:
                self._base, self._token = await _open_search(client)
            except httpx.HTTPError as e:
                raise self._unreachable(e) from e
        except BaseException:
            await stack.aclose()
            raise
        self._stack, self._client = stack, client

    async def _close(self) -> None:
        stack, self._stack, self._client = self._stack, None, None
        if stack is not None:
            await stack.aclose()

    @staticmethod
    def _unreachable(e: Exception) -> MdocFetchError:
        # A transport failure, not an HTTP status: almost always the proxy.
        # Not retried - a proxy that is down stays down, and this message is
        # more use than three slow repeats of it.
        return MdocFetchError(
            f"Couldn't reach OTIS ({e}). It 403s this server's own IP, so "
            "MDOC_PROXY must point at a SOCKS5 proxy that egresses "
            "elsewhere, with something actually listening on it "
            "(infra/otis-tunnel.sh opens one)."
        )

    def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("OtisSession is not open; use it as an async context manager")
        return self._client

    def _form(self, **fields: str) -> dict[str, str]:
        return {
            **BLANK_SEARCH,
            **fields,
            "action:Search": "Search",
            "__RequestVerificationToken": self._token,
        }

    def _checked_results(self, resp: httpx.Response) -> str:
        """The page text of a results page, or the error OTIS's answer amounts to."""
        title = _title_of(resp.text)
        if resp.status_code >= 400:
            raise MdocHttpError(
                resp.status_code, f"OTIS answered {resp.status_code} {title!r} to a search step"
            )
        if RESULTS_TITLE not in title:
            raise MdocBounced(
                f"OTIS returned {title!r} instead of the results page; it rejected the session"
            )
        return resp.text

    async def search_pages(
        self,
        *,
        last_name: str = "",
        first_name: str = "",
        mdoc_number: str = "",
        sex: str = "Either",
        race: str = "All",
        age: int | str | None = None,
        status: str = DEFAULT_STATUS,
        tattoos: str = "",
    ) -> AsyncIterator[tuple[list[MdocSearchResult], int | None, bool]]:
        """Run the search form and yield ``(rows, total, has_next)`` one page at a time.

        The next page is requested only when the caller asks for it, so a caller
        can pace the requests, stop early, or cap the walk without a wasted
        round trip. ``search`` is the usual way in; this is for callers that
        need that control. Raises ``MdocHttpError`` for an HTTP error status and
        ``MdocBounced`` when OTIS answers with the form instead of results.

        Arguments and validation are those of ``search``.
        """
        last_name, first_name = last_name.strip(), first_name.strip()
        mdoc_number, tattoos = str(mdoc_number or "").strip(), tattoos.strip()
        _check_choice("sex", sex, SEX_VALUES)
        _check_choice("race", race, RACE_VALUES)
        _check_choice("status", status, STATUS_VALUES)
        if mdoc_number and not mdoc_number.isdigit():
            raise ValueError("MDOC number must be digits")
        age_text = "" if age is None else str(age).strip()
        if age_text and not (age_text.isdigit() and 0 < int(age_text) < 130):
            raise ValueError("age must be a whole number between 1 and 129")
        if not (last_name or first_name or mdoc_number or tattoos):
            raise ValueError("Give at least a name, an MDOC number or a tattoo/marks text")

        client = self._http()
        try:
            resp = await client.post(
                f"{self._base}/Search",
                data=self._form(
                    LastName=last_name,
                    FirstName=first_name,
                    MDOCNumber=mdoc_number,
                    Sex=sex,
                    Race=race,
                    Age=age_text,
                    OffenderStatus=status,
                    MarksScarsTattoos=tattoos,
                ),
            )
            while True:
                rows, total, has_next = parse_mdoc_results(self._checked_results(resp))
                yield rows, total, has_next
                if not has_next:
                    return
                resp = await client.post(
                    f"{self._base}/Results", data={"action:Pagination": "Next"}
                )
        except httpx.HTTPError as e:
            raise self._unreachable(e) from e

    async def search(
        self,
        *,
        last_name: str = "",
        first_name: str = "",
        mdoc_number: str = "",
        sex: str = "Either",
        race: str = "All",
        age: int | str | None = None,
        status: str = DEFAULT_STATUS,
        tattoos: str = "",
        max_pages: int = DEFAULT_MAX_PAGES,
    ) -> MdocSearchOutcome:
        """Run the search form and follow pagination.

        Every field of the OTIS form is a parameter. ``sex``, ``race`` and
        ``status`` must be one of ``SEX_VALUES`` / ``RACE_VALUES`` /
        ``STATUS_VALUES`` (ValueError otherwise). ``status`` defaults to
        ``DEFAULT_STATUS``, see the observations below for why that is not the
        option its label suggests. At least one of a name, an MDOC number or a
        tattoo/marks substring is required.

        OTIS pages 25 rows at a time; ``max_pages`` caps the walk (a bare
        surname can return hundreds, each page a round trip through the proxy).
        Check ``truncated`` rather than assuming the rows are complete.

        A name search is a lead, not an identification. Several people share a
        name, and OTIS holds only those who passed through the Department of
        Corrections: county jail, federal custody and juvenile records never
        appear here, so an empty result does not mean someone has no record.

        LIVE OBSERVATIONS (2026-11-04, a handful of requests):
          * One token serves any number of searches in a session (six in a row
            worked), and a ``Search`` POST may follow a ``Results`` pagination.
          * A tattoo-only search is accepted (``tattoos`` alone: thousands of
            matches for a common word), and tattoos + status + race + sex
            combine as ANDed filters (each added filter shrank the total).
            ``tattoos`` is a substring match on the marks text.
          * ``age`` is a fuzzy filter, not an exact one: age 30 returned people
            aged 27 to 32 by date of birth, age 45 returned 42 to 47. It
            narrows a list; never read it as the age of a hit.
          * ``status`` is NOT what its labels say. For a name search, "Active
            Offenders" is the widest option and the only one that returns
            discharged people (status ``Dischrg``); "All" returned a strict
            subset without them (6 vs 7 and 5 vs 10 hits in two probes), and
            "Discharged" returned 0 rows every time. Hence DEFAULT_STATUS is
            "Active Offenders". A search by ``mdoc_number`` ignores ``status``
            entirely (a discharged man was found under "Prison").
          * The results table has no MCL column (see ``parse_mdoc_results``);
            its race text is the long form ("Black or African American") while
            the filter takes the short one ("Black"). The results page also
            has a ``pageSize`` field (10, 25, 50, 100); this client leaves the
            default 25.
        """
        if max_pages < 1:
            raise ValueError("max_pages must be at least 1")
        out: list[MdocSearchResult] = []
        seen: set[str] = set()
        total: int | None = None
        truncated = False
        pages = self.search_pages(
            last_name=last_name,
            first_name=first_name,
            mdoc_number=mdoc_number,
            sex=sex,
            race=race,
            age=age,
            status=status,
            tattoos=tattoos,
        )
        count = 0
        async for rows, page_total, has_next in pages:
            count += 1
            if count == 1:
                total = page_total
            # Guard against a pagination that loops back on itself rather
            # than advancing, which would otherwise spin to max_pages.
            fresh = [r for r in rows if r.mdoc_number not in seen]
            if not fresh:
                break
            seen.update(r.mdoc_number for r in fresh)
            out.extend(fresh)
            if not has_next:
                break
            if count == max_pages:
                truncated = True
                break
        await pages.aclose()
        return MdocSearchOutcome(rows=out, total=total, truncated=truncated)

    async def _profile_once(self, number: str) -> str:
        client = self._http()
        try:
            results = await client.post(f"{self._base}/Search", data=self._form(MDOCNumber=number))
            profile = await client.post(
                f"{self._base}/Results", data={"action:LoadProfile": number}
            )
        except httpx.HTTPError as e:
            raise self._unreachable(e) from e

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

    async def profile(self, mdoc_number: str) -> MdocProfile:
        """Load and parse one offender's profile by MDOC number.

        Two requests on this session, in this order - there is no shortcut,
        because ``action:LoadProfile`` is only honoured once a search has put a
        result set into the session:

            POST /Search   + MDOCNumber + token  -> the results list
            POST /Results  + action:LoadProfile=N -> the profile

        OTIS answers 200 with the search form when it rejects a step rather than
        signalling an error, so each step is verified by page title. The search
        step exists only to establish session state, and **nothing is decided
        from what it returns**: for one real offender it reported "0 matches
        found" on one attempt and bounced to the search form on the next, yet
        ``LoadProfile`` fetched that profile correctly both times.

        A bounced ``LoadProfile`` is retried up to ``PROFILE_ATTEMPTS`` times
        on a rebuilt session (new cookies, new token): what fails is the
        session, so reusing it would reproduce the rejection. ``LoadProfile``
        answering 500 means no such number and is not retried.
        """
        number = str(mdoc_number).strip()
        if not number.isdigit():
            raise ValueError("MDOC number must be digits")

        last_bounce = ""
        for attempt in range(PROFILE_ATTEMPTS):
            try:
                html = await self._profile_once(number)
                break
            except _OtisBounced as e:
                last_bounce = str(e)
                if attempt + 1 < PROFILE_ATTEMPTS:
                    await asyncio.sleep(PROFILE_RETRY_DELAYS[attempt])
                    await self._close()
                    await self._open()
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


async def fetch_mdoc_profile(mdoc_number: str, proxy: str | None = None) -> MdocProfile:
    """Look an offender up by MDOC number: a one-profile ``OtisSession``."""
    number = str(mdoc_number).strip()
    if not number.isdigit():
        raise ValueError("MDOC number must be digits")
    async with OtisSession(proxy) as otis:
        return await otis.profile(number)


async def search_mdoc(*, proxy: str | None = None, **fields) -> MdocSearchOutcome:
    """One search in a one-search ``OtisSession``; see ``OtisSession.search``."""
    async with OtisSession(proxy) as otis:
        return await otis.search(**fields)


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
