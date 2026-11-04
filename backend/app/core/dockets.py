"""Reading a court and a docket number out of what custody records and research notes say.

`member_incarceration.case_id` is free text, and the same case turns up written
several ways: `2:17-cr-20740`, `2:17-cr-20740 (E.D. Mich.)`, an OTIS court file
`09912345-FC`, `Wayne Circuit 11-054321-FC (MDOC #123456)`, or a court with no
number at all. `parse_case_ref` turns one of those, with the spell's notes for
context, into a court and a normalised docket, so every spelling of a case
resolves to one `court_case` row.

It never guesses. A federal docket with no court in the text or the notes, or a
court with no docket, comes back as None, and the caller reports it.
"""

import datetime
import re
from dataclasses import dataclass, field

from app.core.enums import CourtCaseKind, CourtJurisdiction

# Bluebook state abbreviations, for the district courts this research reaches
# and their neighbours. A district named in the notes in full ("Eastern
# District of Michigan") is rewritten to the short form the dockets use.
_STATES = {
    "Alabama": "Ala.",
    "Arizona": "Ariz.",
    "Arkansas": "Ark.",
    "California": "Cal.",
    "Colorado": "Colo.",
    "Florida": "Fla.",
    "Georgia": "Ga.",
    "Illinois": "Ill.",
    "Indiana": "Ind.",
    "Iowa": "Iowa",
    "Kentucky": "Ky.",
    "Louisiana": "La.",
    "Michigan": "Mich.",
    "Minnesota": "Minn.",
    "Mississippi": "Miss.",
    "Missouri": "Mo.",
    "New Jersey": "N.J.",
    "New York": "N.Y.",
    "North Carolina": "N.C.",
    "North Dakota": "N.D.",
    "Ohio": "Ohio",
    "Oklahoma": "Okla.",
    "Pennsylvania": "Pa.",
    "South Carolina": "S.C.",
    "Tennessee": "Tenn.",
    "Texas": "Tex.",
    "Virginia": "Va.",
    "West Virginia": "W. Va.",
    "Wisconsin": "Wis.",
}
_DIRECTIONS = {
    "Eastern": "E.",
    "Western": "W.",
    "Northern": "N.",
    "Southern": "S.",
    "Middle": "M.",
    "Central": "C.",
}

_STATE_ABBR = "|".join(re.escape(a) for a in sorted(set(_STATES.values()), key=len, reverse=True))
# "E.D. Mich.", "M.D. Tenn.", "S.D. W.Va.", "D.N.D." (a one-district state).
_SHORT_DISTRICT = re.compile(
    rf"\b(?:([NSEWMC])\.\s?D\.\s?({_STATE_ABBR}|W\.\s?Va\.)|D\.\s?(N\.\s?D\.|S\.\s?D\.|Minn\.|N\.J\.|Colo\.|Ariz\.|S\.C\.|Kan\.|Neb\.))"
)
_LONG_DISTRICT = re.compile(
    rf"\b(?:(Eastern|Western|Northern|Southern|Middle|Central) )?District of ({'|'.join(_STATES)})\b"
)
_FEDERAL_DOCKET = re.compile(r"\b(\d):(\d{2})-(cr|cv|mj|mc)-(\d{1,6})\b", re.IGNORECASE)

# A state court file is one token: OTIS's "09912345-FC", "13004321-FH-C30",
# "150000054321-FH", "CRW012345-FH", "95002601FCA", or an older "01011952-03".
# The format varies by county and decade, so the shape is checked loosely and
# the court comes from the county, which is what actually places the case.
_STATE_FILE = re.compile(r"^(?=.*\d)[A-Z0-9]{2,}(?:-[A-Z0-9]+)*$")
_MI_CIRCUIT = re.compile(r"^(\w[\w.]*) Circuit (\d{2}-\d{5,6}-[A-Z]{2})\b")
_COUNTY = re.compile(r"County:\s*([A-Z][A-Za-z. ]+?)\s*(?:\n|\||$)")
# A research note writes the county in prose: "Bench trial, Wayne County Circuit Court."
_COUNTY_PROSE = re.compile(r"\b((?:St\. )?[A-Z][a-z]+) County\b")


@dataclass
class CaseRef:
    jurisdiction: CourtJurisdiction
    court: str
    docket: str
    kind: CourtCaseKind = CourtCaseKind.CRIMINAL
    # The text as it was found, when it differs from `docket`: stored as an
    # alias so the next record that writes it the same way resolves here.
    aliases: list[str] = field(default_factory=list)


def _one_district(abbr: str) -> str:
    """A state with one district: "D.N.D." for initials, "D. Minn." for a word."""
    abbr = abbr.replace(" ", "")
    return f"D.{abbr}" if re.fullmatch(r"(?:[A-Z]\.)+", abbr) else f"D. {abbr}"


def _short(direction: str | None, state: str) -> str:
    abbr = _STATES[state]
    if direction is None:
        return _one_district(abbr)
    return f"{_DIRECTIONS[direction]}D. {abbr}"


def federal_court(text: str) -> str | None:
    """The district court named in `text`, in short form, or None."""
    m = _SHORT_DISTRICT.search(text)
    if m:
        if m.group(1):
            state = re.sub(r"\s+", " ", m.group(2)).replace("W.Va.", "W. Va.")
            return f"{m.group(1)}.D. {state}"
        return _one_district(m.group(3))
    m = _LONG_DISTRICT.search(text)
    if m:
        return _short(m.group(1), m.group(2))
    return None


def normalise_federal_docket(office: str, year: str, kind: str, number: str) -> str:
    """`3:23-cr-180` and `3:23-cr-00180` are one docket; PACER pads to five digits."""
    return f"{office}:{year}-{kind.lower()}-{int(number):05d}"


def parse_case_ref(case_id: str | None, notes: str | None = None) -> CaseRef | None:
    """The court and docket a spell's case text names, or None when it names no
    docket, or a federal docket whose court nothing states."""
    raw = " ".join((case_id or "").split())
    if not raw:
        return None

    m = _FEDERAL_DOCKET.search(raw)
    if m:
        court = federal_court(raw) or federal_court(notes or "")
        if court is None:
            return None
        docket = normalise_federal_docket(*m.groups())
        kind = {"mj": CourtCaseKind.MAGISTRATE, "cv": CourtCaseKind.CIVIL}.get(
            m.group(3).lower(), CourtCaseKind.CRIMINAL
        )
        aliases = [raw] if raw != docket else []
        return CaseRef(CourtJurisdiction.US_FEDERAL, court, docket, kind, aliases)

    county_match = _COUNTY.search(notes or "") or _COUNTY_PROSE.search(notes or "")
    m = _MI_CIRCUIT.match(raw)
    if m:
        county = m.group(1)
        return CaseRef(
            CourtJurisdiction.US_STATE,
            f"{county} County Circuit Court",
            m.group(2),
            aliases=[raw],
        )
    if _STATE_FILE.match(raw.upper()) and county_match:
        county = county_match.group(1).strip()
        return CaseRef(CourtJurisdiction.US_STATE, f"{county} County Circuit Court", raw.upper())
    return None


# --- what a record says about how a defendant's part ended -----------------------

_OTIS_CONVICTION = re.compile(r"Conviction type:\s*(\w+)", re.IGNORECASE)
_PENDING = re.compile(
    r"pending trial|held pending|awaiting trial|pleaded not guilty|consented to detention",
    re.IGNORECASE,
)
_PLEA = re.compile(r"guilty plea|pleaded guilty|binding plea|\bplea\b|nolo", re.IGNORECASE)
_VERDICT = re.compile(r"jury verdict|convicted|found guilty|\bverdict\b|bench trial", re.IGNORECASE)
# A term, a judgment or a sentence being imposed, in digits or in words
# ("Ten years and three months ... imposed by Judge ...").
_SENTENCED = re.compile(
    r"\b(?:sentence|sentenced|imposed|judgment|years?|months?|life)\b", re.IGNORECASE
)


def disposition_from_notes(notes: str | None) -> str:
    """PLEADED, CONVICTED or PENDING, from an OTIS block or a research note.

    A spell is custody, and custody after sentencing means a plea or a verdict;
    a note that says neither but carries a term reads as CONVICTED. Held
    awaiting trial is PENDING.
    """
    text = notes or ""
    m = _OTIS_CONVICTION.search(text)
    if m:
        kind = m.group(1).lower()
        return "PLEADED" if kind in ("plea", "nolo") else "CONVICTED"
    if _PENDING.search(text):
        return "PENDING"
    if _PLEA.search(text):
        return "PLEADED"
    if _VERDICT.search(text) or _SENTENCED.search(text):
        return "CONVICTED"
    return "PENDING"


_OTIS_OFFENSE = re.compile(r"Offense:\s*([^\n|]+)")
_OTIS_MCL = re.compile(r"\bMCL\s+([^\n|]+)")
_NOTABLE = re.compile(r"homicide|murder|manslaughter|assault", re.IGNORECASE)
# Resisting an officer is filed under "Assault/Resist/Obstruct" and is not the
# assault the rule is about.
_NOT_NOTABLE = re.compile(r"resist/obstruct", re.IGNORECASE)


def otis_charge(notes: str | None) -> dict | None:
    """The count an OTIS spell records, as a `court_case_defendant.charges` entry."""
    offense = _OTIS_OFFENSE.search(notes or "")
    if not offense:
        return None
    mcl = _OTIS_MCL.search(notes or "")
    return {
        "count": None,
        "statute": f"MCL {mcl.group(1).strip()}" if mcl else None,
        "offense": offense.group(1).strip(),
        "disposition": disposition_from_notes(notes),
        "offense_date": otis_offense_date(notes),
    }


_OTIS_OFFENSE_DATE = re.compile(r"Date of offense:\s*([A-Z][a-z]{2} \d{1,2}, \d{4})")


def otis_offense_date(notes: str | None) -> dict | None:
    """The offence date OTIS gives a count ("Date of offense: Feb 14, 2011"), as
    a FuzzyDate. Two files against one man often differ only by this."""
    m = _OTIS_OFFENSE_DATE.search(notes or "")
    if not m:
        return None
    try:
        d = datetime.datetime.strptime(m.group(1), "%b %d, %Y").date()
    except ValueError:
        return None
    return {
        "year": d.year,
        "month": d.month,
        "day": d.day,
        "precision": "YMD",
        "approx": False,
        "circa_text": None,
    }


_SEVERITY = (
    re.compile(r"homicide|murder|manslaughter", re.IGNORECASE),
    re.compile(r"assault|robbery|carjacking|kidnap", re.IGNORECASE),
)


def lead_charge(charges: list[dict]) -> dict | None:
    """The count that best names a case for one defendant: a homicide over an
    assault or robbery over anything else, the first listed within a tier."""
    if not charges:
        return None
    for tier in _SEVERITY:
        for c in charges:
            if tier.search(c.get("offense") or ""):
                return c
    return charges[0]


def is_notable_state_offense(notes: str | None) -> bool:
    """A homicide or assault count, the rule for making a state case of a court file."""
    offense = _OTIS_OFFENSE.search(notes or "")
    if not offense:
        return False
    text = offense.group(1)
    return bool(_NOTABLE.search(text)) and not _NOT_NOTABLE.search(text)
