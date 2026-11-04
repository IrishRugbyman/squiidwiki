"""Citations replace the six source link tables; sources learn their kind.

Revision ID: 4a89130f7a88
Revises: 437b8ac567a8
Create Date: 2026-10-04

- `citation`: one row per (source, record), with a locator, a quote, a note,
  a position and a reading date. Copied from member_source, incident_source,
  set_source, municipality_source, court_case_source and business_source,
  which are dropped: no compatibility views, every client moves to the
  citation API in the same change.
- `source.kind`, `source.url_norm`, `source.lookup_system`, backfilled from the
  URL with a frozen copy of app/core/sources.py as of this revision.
- `source.published_at`: the 384 JSON 'null' values become SQL NULL.
- `member_custody_id.source_id` becomes ON DELETE SET NULL, as
  `member_alias.source_id` already is.

The unique index on (universe_id, lookup_system) is NOT created here: until
app/scripts/merge_lookup_sources.py has run, a universe holds many rows per
lookup system. Revision d8690312003c adds it.
"""

import sqlalchemy as sa

from alembic import op

revision = "4a89130f7a88"
down_revision = "437b8ac567a8"
branch_labels = None
depends_on = None

# (link table, entity column, entity table, old FK actions on entity, on source)
LINKS = [
    ("member_source", "member_id", "member", "", ""),
    ("incident_source", "incident_id", "incident", "", ""),
    ("set_source", "set_id", "sets", "", ""),
    (
        "municipality_source",
        "municipality_id",
        "municipality",
        "ON DELETE CASCADE",
        "ON DELETE CASCADE",
    ),
    ("court_case_source", "court_case_id", "court_case", "ON DELETE CASCADE", "ON DELETE CASCADE"),
    ("business_source", "business_id", "business", "ON DELETE CASCADE", "ON DELETE CASCADE"),
]
TARGETS = [
    ("member_id", "member"),
    ("incident_id", "incident"),
    ("set_id", "sets"),
    ("alliance_id", "alliance"),
    ("court_case_id", "court_case"),
    ("municipality_id", "municipality"),
    ("business_id", "business"),
]


def _frozen():
    """app/core/sources.py helpers as of this revision, frozen."""
    ns: dict = {}
    exec(_FROZEN_SOURCE, ns)
    return ns


_FROZEN_SOURCE = r"""
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
    '''Lowercase scheme and host, drop a trailing slash, strip tracking params.

    Deliberately conservative: query strings are load-bearing on court and
    records sites, so they stay.
    '''
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
    '''The host without `www.`, or None for a URL with no host (research-file:, r2:).'''
    if not url:
        return None
    host = urlsplit(url.strip()).netloc.casefold()
    return host.removeprefix("www.") or None


def lookup_system(url: str | None) -> LookupSystem | None:
    '''The custody lookup a URL belongs to: search page or one person's deep link.'''
    if not url:
        return None
    parts = urlsplit(url.strip())
    host = parts.netloc.casefold().removeprefix("www.")
    path = parts.path.casefold()
    if host == "bop.gov" and path.startswith(("/inmateloc", "/publicinfo/execute/inmateloc")):
        return LookupSystem.BOP
    if host == "mdocweb.state.mi.us" and path.startswith("/otis2"):
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
    '''The record number a lookup URL or source title points at, or None.'''
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
    '''A source's kind from its URL. A guess the researcher can override.'''
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


"""


def upgrade() -> None:
    bind = op.get_bind()

    # 1. New source columns.
    op.add_column("source", sa.Column("url_norm", sa.String(), nullable=True))
    op.add_column("source", sa.Column("kind", sa.String(), nullable=False, server_default="OTHER"))
    op.add_column("source", sa.Column("lookup_system", sa.String(), nullable=True))

    # 2. JSON 'null' is not SQL NULL.
    op.execute("UPDATE source SET published_at = NULL WHERE published_at = 'null'::jsonb")

    # 3. Backfill from the URL.
    f = _frozen()
    rows = bind.execute(sa.text("SELECT id, url FROM source")).all()
    for sid, url in rows:
        system = f["lookup_system"](url)
        bind.execute(
            sa.text(
                "UPDATE source SET url_norm = :n, kind = :k, lookup_system = :l WHERE id = :id"
            ),
            {
                "n": f["normalise_url"](url),
                "k": f["classify_kind"](url).value,
                "l": system.value if system else None,
                "id": sid,
            },
        )
    op.alter_column("source", "url_norm", nullable=False, server_default="")
    op.create_index("ix_source_universe_url_norm", "source", ["universe_id", "url_norm"])

    # 4. The citation table.
    op.create_table(
        "citation",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("universe_id", sa.Uuid(), sa.ForeignKey("universe.id"), nullable=False),
        sa.Column(
            "source_id", sa.Uuid(), sa.ForeignKey("source.id", ondelete="RESTRICT"), nullable=False
        ),
        *(
            sa.Column(
                col, sa.Uuid(), sa.ForeignKey(f"{table}.id", ondelete="CASCADE"), nullable=True
            )
            for col, table in TARGETS
        ),
        sa.Column("locator", sa.String(), nullable=True),
        sa.Column("quote", sa.String(), nullable=True),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accessed_at", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "created_by_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.CheckConstraint(
            "num_nonnulls(member_id, incident_id, set_id, alliance_id, court_case_id, "
            "municipality_id, business_id) = 1",
            name="ck_citation_exactly_one_target",
        ),
    )
    op.create_index("ix_citation_universe_id", "citation", ["universe_id"])
    op.create_index("ix_citation_source_id", "citation", ["source_id"])
    for col, _ in TARGETS:
        op.create_index(
            f"uq_citation_{col}_source",
            "citation",
            [col, "source_id"],
            unique=True,
            postgresql_where=sa.text(f"{col} IS NOT NULL"),
        )

    # 5. Copy every link row. Position follows the order sources were added.
    for link, col, table, _, _ in LINKS:
        op.execute(
            f"""
            INSERT INTO citation (universe_id, source_id, {col}, position, created_at, updated_at)
            SELECT s.universe_id, l.source_id, l.{col},
                   row_number() OVER (PARTITION BY l.{col} ORDER BY s.created_at, s.id) - 1,
                   greatest(s.created_at, e.created_at), greatest(s.created_at, e.created_at)
            FROM {link} l
            JOIN source s ON s.id = l.source_id
            JOIN {table} e ON e.id = l.{col}
            """
            if table not in ("municipality",)
            else f"""
            INSERT INTO citation (universe_id, source_id, {col}, position, created_at, updated_at)
            SELECT s.universe_id, l.source_id, l.{col},
                   row_number() OVER (PARTITION BY l.{col} ORDER BY s.created_at, s.id) - 1,
                   s.created_at, s.created_at
            FROM {link} l
            JOIN source s ON s.id = l.source_id
            """
        )
        # 6. Abort the whole migration if a single row went missing.
        op.execute(
            f"""
            DO $$
            DECLARE a bigint; b bigint;
            BEGIN
              SELECT count(*) INTO a FROM {link};
              SELECT count(*) INTO b FROM citation WHERE {col} IS NOT NULL;
              IF a <> b THEN
                RAISE EXCEPTION '{link}: % link rows but % citations', a, b;
              END IF;
            END $$
            """
        )

    # 7. The link tables go.
    for link, *_ in LINKS:
        op.drop_table(link)

    # 8. Custody numbers lose their source rather than blocking its delete.
    op.drop_constraint("member_custody_id_source_id_fkey", "member_custody_id", type_="foreignkey")
    op.create_foreign_key(
        "member_custody_id_source_id_fkey",
        "member_custody_id",
        "source",
        ["source_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("member_custody_id_source_id_fkey", "member_custody_id", type_="foreignkey")
    op.create_foreign_key(
        "member_custody_id_source_id_fkey", "member_custody_id", "source", ["source_id"], ["id"]
    )
    for link, col, table, on_entity, on_source in LINKS:
        op.execute(
            f"""
            CREATE TABLE {link} (
                {col} uuid NOT NULL REFERENCES {table}(id) {on_entity},
                source_id uuid NOT NULL REFERENCES source(id) {on_source},
                PRIMARY KEY ({col}, source_id)
            )
            """
        )
        op.execute(
            f"INSERT INTO {link} ({col}, source_id) "
            f"SELECT {col}, source_id FROM citation WHERE {col} IS NOT NULL"
        )
    op.create_index("ix_court_case_source_source_id", "court_case_source", ["source_id"])
    # Citations of alliances had no table before this revision; they are lost.
    op.drop_table("citation")
    op.drop_index("ix_source_universe_url_norm", table_name="source")
    op.drop_column("source", "lookup_system")
    op.drop_column("source", "kind")
    op.drop_column("source", "url_norm")
