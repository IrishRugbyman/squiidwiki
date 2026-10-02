"""Fill municipality.population with the latest official count.

One source per kind of place, each the most recent figure its publisher puts out:

- US cities, villages and townships: Census Bureau Population Estimates Program,
  the newest subcounty vintage found on www2.census.gov (sub-estYYYY.csv), whose
  last column is the July 1 estimate of that year.
- US ZIP-code districts and CDPs (places the estimates program does not cover):
  ACS 5-year table B01003, newest release, through api.census.gov with
  CENSUS_API_KEY from the repo .env (the API refuses keyless requests), or from
  the table-based summary file when no key is set.
- French communes: INSEE populations légales through geo.api.gouv.fr. The API
  does not say which millésime it serves, so INSEE_MILLESIME is pinned; check a
  commune against INSEE's PopRef PDF before bumping it each January.

A place no source covers (a Corsican hamlet, a neighborhood) is left as it is.

Dry run by default; --go writes, through the ORM so the audit log sees it.

Run from backend/:
  $PY -m app.scripts.import_populations           # show what would change
  $PY -m app.scripts.import_populations --go      # write
"""

import asyncio
import csv
import io
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

from sqlmodel import select

from app.core.config import settings
from app.core.database import _session_factories
from app.models.municipality import Municipality
from app.models.universe import Universe

US_STATES = {
    "michigan": "Michigan",
    "georgia": "Georgia",
    "illinois": "Illinois",
    "ohio": "Ohio",
    "tennessee": "Tennessee",
}
# A municipality named "Town, KY" sits in a universe named for another state
# (the Clarksville scene straddles the line); the suffix names its real state.
STATE_SUFFIX = {"KY": "Kentucky", "TN": "Tennessee", "GA": "Georgia", "MI": "Michigan"}

# Places whose Census row is not "<name> city|village|town". Keyed by
# (universe slug, municipality name): (SUMLEV, Census NAME, COUNTY or None).
PEP_OVERRIDES = {
    # A charter township is a county subdivision (061), not a place.
    ("michigan", "Clinton Township"): ("061", "Clinton charter township", "099"),
    # The consolidated government less Blythe and Hephzibah: the city proper.
    ("georgia", "Augusta"): (
        "162",
        "Augusta-Richmond County consolidated government (balance)",
        None,
    ),
}
# Census-designated places: no annual estimate, so ACS 5-year by GEO_ID.
ACS_PLACES = {
    ("tennessee", "Fort Campbell North, KY"): "1600000US2128486",
}

CORSICA = "corsica"
INSEE_MILLESIME = (
    2023  # geo.api.gouv.fr serves the populations légales in force: 2023 since 2026-01-01
)

UA = {"User-Agent": "squiidwiki-populations/1.0"}


def _get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read()


def _latest(template: str, years) -> tuple[int, bytes]:
    for y in years:
        try:
            return y, _get(template.format(y=y))
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
    raise SystemExit(f"no file found for {template} in {list(years)}")


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().casefold()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def load_pep() -> tuple[int, dict]:
    this = date.today().year
    year, raw = _latest(
        "https://www2.census.gov/programs-surveys/popest/datasets/2020-{y}/cities/totals/sub-est{y}.csv",
        range(this, this - 4, -1),
    )
    rows = list(csv.DictReader(io.StringIO(raw.decode("latin-1"))))
    return year, {"rows": rows, "col": f"POPESTIMATE{year}"}


def _acs_api_year(key: str) -> int:
    """The newest ACS 5-year release the API serves."""
    this = date.today().year
    for y in range(this - 1, this - 5, -1):
        try:
            _get(f"https://api.census.gov/data/{y}/acs/acs5?get=NAME&for=us:1&key={key}")
            return y
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise SystemExit(f"Census API refused the request (HTTP {e.code})") from None
    raise SystemExit("no ACS 5-year release found on api.census.gov")


def load_acs(geo_ids: set[str]) -> tuple[int, dict[str, int]]:
    """B01003 total population for `geo_ids` (ZCTAs `860Z200US.....`, places
    `1600000USss.....`), from the newest ACS 5-year release.

    Through api.census.gov when CENSUS_API_KEY is set: a handful of small
    requests. Without it, the table-based summary file, one 18 MB download.
    """
    key = settings.census_api_key
    if not key:
        this = date.today().year
        year, raw = _latest(
            "https://www2.census.gov/programs-surveys/acs/summary_file/{y}/table-based-SF/data/5YRData/acsdt5y{y}-b01003.dat",
            range(this - 1, this - 5, -1),
        )
        out = {}
        for line in raw.decode().splitlines()[1:]:
            geo, est, _ = line.split("|")
            if geo in geo_ids:
                out[geo] = int(est)
        return year, out

    year = _acs_api_year(key)
    base = f"https://api.census.gov/data/{year}/acs/acs5?get=GEO_ID,B01003_001E&key={key}"
    queries = []
    zctas = sorted(g.removeprefix("860Z200US") for g in geo_ids if g.startswith("860Z200US"))
    if zctas:
        queries.append("&for=" + urllib.parse.quote(f"zip code tabulation area:{','.join(zctas)}"))
    for g in sorted(geo_ids):
        if g.startswith("1600000US"):
            st, pl = g[9:11], g[11:]
            queries.append(f"&for=place:{pl}&in=state:{st}")
    out = {}
    for q in queries:
        try:
            table = json.loads(_get(base + q))
        except urllib.error.HTTPError as e:
            # The URL carries the key; report the status only.
            raise SystemExit(f"Census API refused an ACS request (HTTP {e.code})") from None
        head = table[0]
        gi, vi = head.index("GEO_ID"), head.index("B01003_001E")
        for row in table[1:]:
            out[row[gi]] = int(row[vi])
    return year, out


def pep_lookup(pep: dict, state: str, name: str, override) -> int | None:
    col = pep["col"]
    if override:
        sumlev, census_name, county = override
        hits = [
            r
            for r in pep["rows"]
            if r["STNAME"] == state
            and r["SUMLEV"] == sumlev
            and r["NAME"] == census_name
            and (county is None or r["COUNTY"] == county)
        ]
    else:
        wanted = {f"{name} city", f"{name} village", f"{name} town"}
        hits = [
            r
            for r in pep["rows"]
            if r["STNAME"] == state and r["SUMLEV"] == "162" and r["NAME"] in wanted
        ]
    values = {int(r[col]) for r in hits}
    if len(values) > 1:
        raise SystemExit(f"{name}, {state}: several Census rows disagree {values}; add an override")
    return values.pop() if values else None


def insee_lookup(name: str) -> int | None:
    q = urllib.parse.urlencode({"nom": name, "fields": "nom,population,codeDepartement"})
    hits = [
        c
        for c in json.loads(_get(f"https://geo.api.gouv.fr/communes?{q}"))
        if c.get("codeDepartement") in ("2A", "2B") and _fold(c["nom"]) == _fold(name)
    ]
    if len(hits) > 1:
        raise SystemExit(f"{name}: {len(hits)} Corsican communes share the name")
    return hits[0].get("population") if hits else None


async def main(go: bool) -> int:
    async with _session_factories["prod"]() as s:
        rows = (
            await s.execute(
                select(Municipality, Universe.slug).join(
                    Universe, Universe.id == Municipality.universe_id
                )
            )
        ).all()

        # Every US universe needs both files; they are fetched once, up front.
        pep_year, pep = load_pep()
        acs_ids = {ACS_PLACES[(slug, m.name)] for m, slug in rows if (slug, m.name) in ACS_PLACES}
        acs_ids |= {
            f"860Z200US{m.name}"
            for m, slug in rows
            if slug in US_STATES and re.fullmatch(r"\d{5}", m.name)
        }
        acs_year, acs = load_acs(acs_ids)
        pep_label = f"US Census Bureau, Vintage {pep_year} estimates"
        acs_label = f"US Census Bureau, ACS 5-year {acs_year - 4}-{acs_year}"

        changed = missing = 0
        for m, slug in sorted(rows, key=lambda r: (r[1], r[0].name)):
            found: tuple[int, int, str] | None = None
            if slug in US_STATES:
                name, state = m.name, US_STATES[slug]
                if (hit := re.fullmatch(r"(.+), ([A-Z]{2})", m.name)) and hit[2] in STATE_SUFFIX:
                    name, state = hit[1], STATE_SUFFIX[hit[2]]
                if (slug, m.name) in ACS_PLACES:
                    v = acs.get(ACS_PLACES[(slug, m.name)])
                    found = (v, acs_year, acs_label) if v is not None else None
                elif re.fullmatch(r"\d{5}", m.name):
                    v = acs.get(f"860Z200US{m.name}")
                    found = (
                        (v, acs_year, f"{acs_label}, ZIP code tabulation area")
                        if v is not None
                        else None
                    )
                elif m.parent_id is None:
                    v = pep_lookup(pep, state, name, PEP_OVERRIDES.get((slug, m.name)))
                    found = (v, pep_year, pep_label) if v is not None else None
            elif slug == CORSICA:
                v = insee_lookup(m.name)
                found = (
                    (v, INSEE_MILLESIME, f"INSEE, populations légales {INSEE_MILLESIME}")
                    if v is not None
                    else None
                )

            if found is None:
                if m.parent_id is None:
                    missing += 1
                    print(f"  --      {slug:10} {m.name}: no figure")
                continue
            pop, year, label = found
            current = (m.population, m.population_year, m.population_source)
            if current == found:
                continue
            changed += 1
            was = (
                f" (was {m.population:,} in {m.population_year})"
                if m.population is not None
                else ""
            )
            print(f"  {pop:>9,} {slug:10} {m.name} [{year}]{was}")
            if go:
                m.population, m.population_year, m.population_source = pop, year, label
                s.add(m)

        if go:
            await s.commit()
        print(f"\n{changed} to update, {missing} top-level places without a figure")
        if not go:
            print("dry run - pass --go to write")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main("--go" in sys.argv[1:])))
