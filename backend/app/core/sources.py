"""What a source's URL says about it: its normal form, its kind, its lookup system.

Pure functions, no database. `normalise_url` and `lookup_system` mirror
`research/tools/wikilib/identity.py`, which resolves case-file references
against these same rows; keep the two in step (tests/test_source_meta.py pins
the shared vectors).
"""

import re
from enum import Enum
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


class SourceKind(str, Enum):
    COURT = "COURT"  # courts, prosecutors, government records
    PRESS = "PRESS"
    CUSTODY = "CUSTODY"  # prison and jail lookups
    SOCIAL = "SOCIAL"
    VIDEO = "VIDEO"  # video and music platforms
    WIKI = "WIKI"  # wikis, blogs, community databases
    MAP = "MAP"
    INTERNAL = "INTERNAL"  # files held by the research itself
    OTHER = "OTHER"


class LookupSystem(str, Enum):
    BOP = "BOP"
    MDOC_OTIS = "MDOC_OTIS"
    GDC = "GDC"


_TRACKING_PREFIXES = ("utm_",)
_TRACKING_EXACT = {"fbclid", "gclid", "mc_cid", "mc_eid"}


def normalise_url(url: str) -> str:
    """Lowercase scheme and host, drop a trailing slash, strip tracking params.

    Deliberately conservative: query strings are load-bearing on court and
    records sites, so they stay.
    """
    parts = urlsplit(url.strip())
    query = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in _TRACKING_EXACT and not k.lower().startswith(_TRACKING_PREFIXES)
    ]
    path = parts.path.rstrip("/") or "/"
    if path == "/":
        path = ""
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


def domain_of(url: str | None) -> str | None:
    """The host without `www.`, or None for a URL with no host (research-file:, r2:)."""
    if not url:
        return None
    host = urlsplit(url.strip()).netloc.casefold()
    return host.removeprefix("www.") or None


def lookup_system(url: str | None) -> LookupSystem | None:
    """The custody lookup a URL belongs to: search page or one person's deep link."""
    if not url:
        return None
    parts = urlsplit(url.strip())
    host = parts.netloc.casefold().removeprefix("www.")
    path = parts.path.casefold()
    if host == "bop.gov" and path.startswith(("/inmateloc", "/publicinfo/execute/inmateloc")):
        return LookupSystem.BOP
    if host == "mdocweb.state.mi.us" and path.startswith("/otis2"):
        return LookupSystem.MDOC_OTIS
    if host == "mdoc-offendersearch.michigan.gov":  # OTIS since 2026-10-31
        return LookupSystem.MDOC_OTIS
    if host == "services.gdc.ga.gov" and path.startswith("/gdc/offenderquery"):
        return LookupSystem.GDC
    return None


_LOCATOR_QUERY_KEYS = ("mdocnumber", "inmatenum")
_LOCATOR_PATTERNS = (
    re.compile(r"\b(\d{5}-\d{3})\b"),  # BOP register number
    re.compile(r"#\s*(\d{5,8})\b"),  # MDOC number as titles write it
    re.compile(r"\brecord\s+([A-Z0-9]{6,12})\b", re.IGNORECASE),  # GDC id
)


def lookup_locator(url: str | None = None, title: str | None = None) -> str | None:
    """The record number a lookup URL or source title points at, or None."""
    if url:
        for k, v in parse_qsl(urlsplit(url.strip()).query):
            if k.casefold() in _LOCATOR_QUERY_KEYS and v.strip():
                return v.strip()
    for pattern in _LOCATOR_PATTERNS:
        m = pattern.search(title or "")
        if m:
            return m.group(1)
    return None


# Host suffix -> kind. Checked longest suffix first, so "storage.courtlistener.com"
# and "courtlistener.com" both land on COURT.
_HOST_KINDS: dict[str, SourceKind] = {
    # courts, prosecutors, government
    "justice.gov": SourceKind.COURT,
    "courtlistener.com": SourceKind.COURT,
    "govinfo.gov": SourceKind.COURT,
    "uscourts.gov": SourceKind.COURT,
    "courts.michigan.gov": SourceKind.COURT,
    "michigan.gov": SourceKind.COURT,
    "law.georgia.gov": SourceKind.COURT,
    "gov": SourceKind.COURT,
    "gouv.fr": SourceKind.COURT,
    "legifrance.gouv.fr": SourceKind.COURT,
    "courtcaseresearch.com": SourceKind.COURT,
    "casetext.com": SourceKind.COURT,
    "justia.com": SourceKind.COURT,
    "leagle.com": SourceKind.COURT,
    "pacermonitor.com": SourceKind.COURT,
    # social
    "instagram.com": SourceKind.SOCIAL,
    "facebook.com": SourceKind.SOCIAL,
    "fb.com": SourceKind.SOCIAL,
    "reddit.com": SourceKind.SOCIAL,
    "redd.it": SourceKind.SOCIAL,
    "x.com": SourceKind.SOCIAL,
    "twitter.com": SourceKind.SOCIAL,
    "tiktok.com": SourceKind.SOCIAL,
    "threads.net": SourceKind.SOCIAL,
    # video and music
    "youtube.com": SourceKind.VIDEO,
    "youtu.be": SourceKind.VIDEO,
    "vimeo.com": SourceKind.VIDEO,
    "spotify.com": SourceKind.VIDEO,
    "soundcloud.com": SourceKind.VIDEO,
    "audiomack.com": SourceKind.VIDEO,
    "genius.com": SourceKind.VIDEO,
    "worldstarhiphop.com": SourceKind.VIDEO,
    # wikis, blogs, community databases
    "wordpress.com": SourceKind.WIKI,
    "blogspot.com": SourceKind.WIKI,
    "wikipedia.org": SourceKind.WIKI,
    "grokipedia.com": SourceKind.WIKI,
    "fandom.com": SourceKind.WIKI,
    "detroitstreetgangs.com": SourceKind.WIKI,
    "urbandictionary.com": SourceKind.WIKI,
    "gunmemorial.org": SourceKind.WIKI,
    "findagrave.com": SourceKind.WIKI,
    "medium.com": SourceKind.WIKI,
    "substack.com": SourceKind.WIKI,
    # maps
    "maps.app.goo.gl": SourceKind.MAP,
    "openstreetmap.org": SourceKind.MAP,
    # press
    "clickondetroit.com": SourceKind.PRESS,
    "fox2detroit.com": SourceKind.PRESS,
    "detroitnews.com": SourceKind.PRESS,
    "freep.com": SourceKind.PRESS,
    "wxyz.com": SourceKind.PRESS,
    "cbsnews.com": SourceKind.PRESS,
    "mlive.com": SourceKind.PRESS,
    "nbcnews.com": SourceKind.PRESS,
    "nytimes.com": SourceKind.PRESS,
    "apnews.com": SourceKind.PRESS,
    "bridgedetroit.com": SourceKind.PRESS,
    "outliermedia.org": SourceKind.PRESS,
    "corsematin.com": SourceKind.PRESS,
    "corsenetinfos.corsica": SourceKind.PRESS,
    "francetvinfo.fr": SourceKind.PRESS,
    "lemonde.fr": SourceKind.PRESS,
    "leparisien.fr": SourceKind.PRESS,
    "ledauphine.com": SourceKind.PRESS,
    "lefigaro.fr": SourceKind.PRESS,
    "nicematin.com": SourceKind.PRESS,
    "chicagotribune.com": SourceKind.PRESS,
    "suntimes.com": SourceKind.PRESS,
    "ajc.com": SourceKind.PRESS,
    "wsbtv.com": SourceKind.PRESS,
    "tennessean.com": SourceKind.PRESS,
    "dispatch.com": SourceKind.PRESS,
    "cleveland.com": SourceKind.PRESS,
    "toledoblade.com": SourceKind.PRESS,
    "waynecounty.com": SourceKind.COURT,
    "govdelivery.com": SourceKind.COURT,
    "michbar.org": SourceKind.COURT,
    "3rdcc.org": SourceKind.COURT,
    "yahoo.com": SourceKind.PRESS,
    "aol.com": SourceKind.PRESS,
    "france24.com": SourceKind.PRESS,
    "deadlinedetroit.com": SourceKind.PRESS,
    "motorcitymuckraker.com": SourceKind.PRESS,
    "audacy.com": SourceKind.PRESS,
    "spokesman-recorder.com": SourceKind.PRESS,
    "thesource.com": SourceKind.PRESS,
    "complex.com": SourceKind.PRESS,
    "xxlmag.com": SourceKind.PRESS,
    "thefader.com": SourceKind.PRESS,
    "20min.ch": SourceKind.PRESS,
    "europe1.fr": SourceKind.PRESS,
    "lecanardenchaine.fr": SourceKind.PRESS,
    "thehamtramckreview.com": SourceKind.PRESS,
    "wilx.com": SourceKind.PRESS,
    "wosu.org": SourceKind.PRESS,
    "wsiu.org": SourceKind.PRESS,
    "cwbchicago.com": SourceKind.PRESS,
    "officer.com": SourceKind.PRESS,
    "powmag.net": SourceKind.PRESS,
    "downtownpublications.com": SourceKind.PRESS,
    "homicidewatch.org": SourceKind.PRESS,
    "crimeindetroit.com": SourceKind.WIKI,
    "gangsterreport.com": SourceKind.WIKI,
    "kollegekidd.com": SourceKind.WIKI,
    "trapaganda.com": SourceKind.WIKI,
    "fakeshoredrive.com": SourceKind.WIKI,
    "grandbanditisme.com": SourceKind.WIKI,
    "projectcoldcase.org": SourceKind.WIKI,
    "imdb.com": SourceKind.WIKI,
    "famousbirthdays.com": SourceKind.WIKI,
    "music.apple.com": SourceKind.VIDEO,
    "arcgis.com": SourceKind.MAP,
}
_INTERNAL_SCHEMES = ("research-file", "wiki-media", "r2")
_INTERNAL_HOSTS = ("wiki.lbzgiu.xyz",)
_PRESS_HINTS = re.compile(
    r"(news|times|tribune|post|herald|gazette|journal|daily|press|tv|radio|fox|abc|nbc|cbs"
    r"|wdiv|wjbk|wxyz|kare|kmov|wsb|matin|info)"
)


def classify_kind(url: str | None) -> SourceKind:
    """A source's kind from its URL. A guess the researcher can override."""
    if not url:
        return SourceKind.OTHER
    parts = urlsplit(url.strip())
    if parts.scheme.casefold() in _INTERNAL_SCHEMES:
        return SourceKind.INTERNAL
    host = parts.netloc.casefold().removeprefix("www.")
    if not host:
        return SourceKind.INTERNAL
    if host in _INTERNAL_HOSTS:
        return SourceKind.INTERNAL
    if lookup_system(url):
        return SourceKind.CUSTODY
    if host.endswith("google.com") and (
        parts.path.startswith("/maps") or "mymaps" in parts.path or "/maps/d" in parts.path
    ):
        return SourceKind.MAP
    if host == "isbnsearch.org" or host.endswith("books.google.com"):
        return SourceKind.OTHER
    for suffix in sorted(_HOST_KINDS, key=len, reverse=True):
        if host == suffix or host.endswith("." + suffix):
            return _HOST_KINDS[suffix]
    if host.endswith((".gov", ".gouv.fr", ".us")) and (".state." in host or host.endswith(".gov")):
        return SourceKind.COURT
    if _PRESS_HINTS.search(host.split(".")[0]):
        return SourceKind.PRESS
    return SourceKind.OTHER


# The canonical source each lookup system is merged into, per universe.
LOOKUP_CANONICAL: dict[LookupSystem, dict[str, str]] = {
    LookupSystem.BOP: {
        "title": "BOP inmate locator",
        "url": "https://www.bop.gov/inmateloc/",
        "publication": "Federal Bureau of Prisons",
    },
    LookupSystem.MDOC_OTIS: {
        "title": "MDOC Offender Tracking Information System (OTIS)",
        "url": "https://mdocweb.state.mi.us/otis2/otis2.html",
        "publication": "Michigan Department of Corrections",
    },
    LookupSystem.GDC: {
        "title": "GDC offender query",
        "url": "https://services.gdc.ga.gov/GDC/OffenderQuery/jsp/OffQryForm.jsp",
        "publication": "Georgia Department of Corrections",
    },
}
