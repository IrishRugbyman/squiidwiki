"""Seed Chicago incidents from the extracted perpetrator -> victim event edges.

Input: extract-chicago-events.json (6,301 directed edges of kind bodies /
shootings / assists). Grouping is per victim, not per edge:

  one MURDER incident per killed victim   all bodies-edges on that victim become
                                          SHOOTER rows, assist-edges become
                                          ASSISTED rows, the victim is
                                          VICTIM/KILLED. Creating it fires the
                                          death sync (status, death_incident_id,
                                          and date_of_death when a year is known).
  one SHOOTING incident per targeted      all shootings-edges on that victim
  victim                                  become SHOOTER rows; the victim is
                                          VICTIM/UNKNOWN, never KILLED, so these
                                          count as shootings and survived-hits,
                                          not kills.

Set-level claims (a set's CORPS list names a victim but no individual shooter)
become incident_set_participant rows, and only when the incident has no named
shooter from that same set - per the house rule that set participants are for
attribution without a name.

Dry-run by default; --go writes through the local API (port 8001, prod DB).
"""

import collections
import html
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, "/home/lbzgiu/squiidape/squiidwiki/research/privedatabase/tools")
from db_sync import candidates, norm  # noqa: E402

API = "http://localhost:8001/api/v1"
U = "59d23911-6fee-4156-8839-ac3c248a3b46"  # Metro Chicago
R = pathlib.Path("/home/lbzgiu/squiidape/squiidwiki/research/privedatabase")
SITE = "https://privedatabase.wordpress.com/"

DATE_UNKNOWN = {"precision": "UNKNOWN"}


# ---------------------------------------------------------------- DB + API I/O
def q(sql):
    """Run a query against squiidwiki_prod and return rows as JSON."""
    r = subprocess.run(
        [
            "psql",
            "-d",
            "squiidwiki_prod",
            "-t",
            "-A",
            "-c",
            f"SELECT coalesce(json_agg(t),'[]') FROM ({sql}) t;",
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode:
        sys.exit(f"psql failed: {r.stderr.strip()}")
    return json.loads(r.stdout)


class Api:
    """API client that logs in and transparently re-logs-in on 401 (15-min tokens)."""

    def __init__(self):
        """Log in immediately so the first call carries a token."""
        self.token = None
        self.login()

    def login(self):
        """Fetch a fresh admin access token."""
        body = json.dumps({"email": "admin@squiidwiki.dev", "password": "admin1234"}).encode()
        r = urllib.request.Request(
            f"{API}/auth/login",
            method="POST",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(r, timeout=30) as x:
            self.token = json.load(x)["access_token"]

    def call(self, method, path, payload=None, _retried=False):
        """Call the API; return the JSON body, or {"_error": code} on an HTTP error."""
        r = urllib.request.Request(
            f"{API}/{path}",
            method=method,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            },
        )
        try:
            with urllib.request.urlopen(r, timeout=30) as x:
                raw = x.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            if e.code == 401 and not _retried:
                self.login()
                return self.call(method, path, payload, _retried=True)
            return {"_error": e.code, "_body": e.read()[:200].decode(errors="replace")}


# ------------------------------------------------------------------ resolution
def clean_title(t):
    """Normalise unicode lookalikes the site mixes in."""
    return (t or "").replace("×", "x").replace("’", "'").strip()


events = json.loads((R / "data/extract-chicago-events.json").read_text())
people = json.loads((R / "data/extract-chicago-people.json").read_text())
am = json.loads((R / "data/alias-map.json").read_text())["alias"]

setidx = {}  # name key -> set id
set_name = {}  # set id -> display name
for r in q(
    f"SELECT id,name,coalesce(name_variants,'[]'::jsonb) nv "
    f"FROM sets WHERE universe_id='{U}' AND is_reserved=false"
):
    set_name[r["id"]] = r["name"]
    for k in candidates(r["name"]):
        setidx.setdefault(k, r["id"])
    for v in r["nv"] or []:
        # A variant carries three slots: the acronym lives in `initials` and the
        # set number in `number`, so indexing only `name` loses "SKD" and "078".
        for slot in ("name", "initials", "number"):
            for k in candidates(v.get(slot) or ""):
                setidx.setdefault(k, r["id"])

allidx = {}  # name key -> alliance id
for r in q(f"SELECT id,name FROM alliance WHERE universe_id='{U}'"):
    for k in candidates(r["name"]):
        allidx.setdefault(k, r["id"])


def resolve_scopes(title):
    """Every set/alliance the title could mean, best-first.

    A slashed title like 'Tyquan World/E-Block' names two sets; a member lookup
    must try both, so this returns them all - direct set hits (longest match key
    first, so the full title outranks a split part), then alliances, then the
    alias-map canon, then a unique key prefix. Scopes are set ids or
    ('A', alliance id) pairs, matching the `scoped` member index.
    """
    title = clean_title(title)
    if not title:
        return []
    out = []

    def add(scope):
        if scope not in out:
            out.append(scope)

    keys = sorted(candidates(title), key=len, reverse=True)
    for k in keys:
        if k in setidx:
            add(setidx[k])
    for k in keys:
        if k in allidx:
            add(("A", allidx[k]))
    canon = next((am[k] for k in keys if k in am), None)
    if canon:
        for k in sorted(candidates(canon), key=len, reverse=True):
            if k in setidx:
                add(setidx[k])
    n = norm(title)
    if len(n) >= 4:
        pre = {sid for k, sid in setidx.items() if k.startswith(n)}
        if len(pre) == 1:
            add(pre.pop())
    return out


def claimable_set(title):
    """The set id a set-level claim resolves to, or None (alliances can't claim)."""
    return next((s for s in resolve_scopes(title) if not isinstance(s, tuple)), None)


# Members: (name key, scope) -> member id, where scope is a set id, an
# ('A', alliance id) pair, or absent for the name-only fallback index.
member_sets = collections.defaultdict(set)  # member id -> their set ids
for r in q(
    f"SELECT ms.member_id, ms.set_id FROM member_set ms JOIN member m ON m.id=ms.member_id WHERE m.universe_id='{U}'"
):
    member_sets[r["member_id"]].add(r["set_id"])

scoped = {}  # (name key, scope) -> member id
by_name = collections.defaultdict(set)  # name key -> member ids
display = {}  # member id -> nickname
status = {}  # member id -> status
for r in q(
    f"SELECT id, nickname, status, coalesce(aliases,'[]'::jsonb) al, alliance_id::text aid "
    f"FROM member WHERE universe_id='{U}'"
):
    display[r["id"]] = r["nickname"]
    status[r["id"]] = r["status"]
    keys = {norm(r["nickname"] or "")} | {norm(a) for a in (r["al"] or []) if isinstance(a, str)}
    keys.discard("")
    for k in keys:
        by_name[k].add(r["id"])
        for sid in member_sets[r["id"]]:
            scoped.setdefault((k, sid), r["id"])
        if r["aid"]:
            scoped.setdefault((k, ("A", r["aid"])), r["id"])

# Person-page subjects: name key -> the set title their own page states.
subject_set = {}
for p in people:
    if "person-page" in p["origins"] and p["set"]:
        subject_set.setdefault(norm(p["name"]), p["set"])

# Alliance pages state no set, so a member sentence there scopes its people to
# the alliance itself (their DB records carry alliance_id, not a set).
ALLIANCE_PAGE = {"479": "MoeTown", "7971": "Dro City", "7490": "MoeTown"}

# Person pages whose subject set the regex could not parse, read by hand:
# CEO "est considéré comme le patron actuel du 50 Strong"; Lil Dee "est le
# demi frère de Booka du même set" - Booka is 600.
PAGE_SUBJECT_SET = {"4231": "50 Strong", "4749": "600"}

_page_text = None
# Anchored to the subject ("Il est décédé"), not any mention of death - a page
# like D.Rose's says "à la mort de Lil Steve" about someone else entirely.
DEADRE = re.compile(
    r"\b(il|elle) (est|était) [^.]{0,30}(d[ée]c[ée]d|mort)|a été (tu[ée]|abattu|poignard)", re.I
)
LOCKEDRE = re.compile(r"\b(il|elle) est [^.]{0,30}(incarc[ée]r|en prison)", re.I)


def page_status(page_id):
    """(dead, locked) asserted by a person page's opening prose, before any event list."""
    global _page_text
    if _page_text is None:
        _page_text = {}
        for p in json.loads((R / "raw/pages.json").read_text()):
            txt = html.unescape(re.sub(r"<[^>]+>", " ", p["content"] or ""))
            txt = re.split(r"CORPS|FUSILLADES|ASSISTANCE", txt)[0]
            _page_text[str(p["ID"])] = txt[:400]
    txt = _page_text.get(page_id, "")
    return bool(DEADRE.search(txt)), bool(LOCKEDRE.search(txt))


def resolve_person(name, set_title, perp_page=None):
    """Return (member_id, exact: bool) or (None, False).

    Tries every scope the set title could mean, then the person's own page's
    set (perps from person pages), then a unique bare-name match. A still
    ambiguous perp from a person page falls back on the status the page
    asserts: 'il est décédé' picks the one DEAD member of that name.
    """
    k = norm(name or "")
    if not k:
        return None, False
    scopes = resolve_scopes(set_title) if set_title else []
    if not scopes and perp_page in ALLIANCE_PAGE:
        scopes = resolve_scopes(ALLIANCE_PAGE[perp_page])
    if not scopes and perp_page:
        st = PAGE_SUBJECT_SET.get(perp_page) or subject_set.get(k)
        scopes = resolve_scopes(st) if st else []
    for scope in scopes:
        mid = scoped.get((k, scope))
        if mid:
            return mid, True
    ids = by_name.get(k, set())
    if len(ids) == 1:
        return next(iter(ids)), bool(scopes)
    if len(ids) > 1 and perp_page and perp_page not in ALLIANCE_PAGE:
        dead, locked = page_status(perp_page)
        want = "DEAD" if dead else "LOCKED" if locked else None
        match = [m for m in ids if status[m] == want] if want else []
        if len(match) == 1:
            return match[0], False
    # The source writes a man as "<SET> <Name>" - "KTS Von", "PBG Kemo" - while the
    # database files him under the bare name on that very set, because a name must
    # not restate the set it sits in. Strip the tag and look for the bare name
    # inside the tagged set: it is the same man, said the long way.
    if not ids:
        head, _, rest = (name or "").partition(" ")
        if rest and head.isupper():
            for scope in resolve_scopes(head):
                mid = scoped.get((norm(rest), scope))
                if mid:
                    return mid, True

    # "G Herbo ou Lil Herb" names one man twice; either half may be the record.
    if not ids and re.search(r"\s+ou\s+", name):
        for part in re.split(r"\s+ou\s+", name):
            mid, exact = resolve_person(part, set_title, perp_page)
            if mid:
                return mid, exact
    return None, False


# ------------------------------------------------------------------- grouping
def blank():
    """Empty per-incident accumulator."""
    return {
        "shooters": {},  # member id -> exact match?
        "assists": {},
        "set_claims": set(),
        "years": set(),
        "pages": set(),
    }


murders = collections.defaultdict(blank)
shootings = collections.defaultdict(blank)
drop = collections.Counter()
deferred_assists = []

for e in events:
    if e["kind"] not in ("bodies", "shootings", "assists"):
        drop[f"kind-{e['kind']}"] += 1
        continue
    vid, _ = resolve_person(e["victim"], e["victim_set"])
    if not vid:
        drop["victim-unresolved"] += 1
        continue
    mid, exact = (
        resolve_person(e["perp"], e["perp_set"], perp_page=e["page"])
        if e["perp"]
        else (None, False)
    )
    if mid == vid:
        drop["self-edge"] += 1
        continue

    if e["kind"] == "assists":
        deferred_assists.append((vid, mid, exact, e))
        continue
    g = murders[vid] if e["kind"] == "bodies" else shootings[vid]
    if mid:
        g["shooters"][mid] = g["shooters"].get(mid, False) or exact
    else:
        sid = claimable_set(e["perp_set"]) if e["perp_set"] else None
        if sid:
            g["set_claims"].add(sid)
        else:
            drop["perp-unresolved"] += 1
    if e.get("victim_year"):
        g["years"].add(e["victim_year"])
    g["pages"].add(e["page"])

# Assists attach to the victim's murder when one exists (or the source says the
# target died); otherwise to their shooting incident.
for vid, mid, exact, e in deferred_assists:
    g = murders[vid] if (vid in murders or e["victim_dead"]) else shootings[vid]
    if mid:
        g["assists"][mid] = g["assists"].get(mid, False) or exact
    else:
        drop["assist-perp-unresolved"] += 1
        continue
    g["pages"].add(e["page"])

# A member both shooting and assisting on the same incident keeps SHOOTER
# (the participant table has one row per member per incident).
for g in list(murders.values()) + list(shootings.values()):
    for mid in list(g["assists"]):
        if mid in g["shooters"]:
            del g["assists"][mid]
    # A set claim is redundant once a named shooter from that set is aboard.
    named_sets = set().union(*(member_sets[m] for m in g["shooters"]), set())
    g["set_claims"] -= named_sets


def payload(vid, g, murder):
    """Build the IncidentCreate body for one grouped incident."""
    parts = [
        {
            "member_id": vid,
            "role": "VICTIM",
            "outcome": "KILLED" if murder else "UNKNOWN",
        }
    ]
    note = "Set not stated at this mention; matched by name across the site."
    for mid, exact in sorted(g["shooters"].items()):
        parts.append(
            {"member_id": mid, "role": "SHOOTER", "outcome": "UNKNOWN"}
            | ({} if exact else {"notes": note})
        )
    for mid, exact in sorted(g["assists"].items()):
        parts.append(
            {"member_id": mid, "role": "ASSISTED", "outcome": "UNKNOWN"}
            | ({} if exact else {"notes": note})
        )
    date = DATE_UNKNOWN
    if len(g["years"]) == 1:
        date = {"year": g["years"].copy().pop(), "precision": "Y"}
    narrative = ""
    if not murder and len(g["shooters"]) + len(g["set_claims"]) > 1:
        narrative = (
            "Aggregates every shooting the source attributes against this member; "
            "the source does not distinguish separate occasions."
        )
    elif murder and len(g["years"]) > 1:
        narrative = f"Source pages disagree on the year: {sorted(g['years'])}."
    return {
        "universe_id": U,
        "type": "MURDER" if murder else "SHOOTING",
        "date": date,
        "narrative": narrative or None,
        "participants": parts,
        "set_participants": [
            {"set_id": sid, "role": "SHOOTER", "outcome": "UNKNOWN"}
            for sid in sorted(g["set_claims"])
        ],
    }


# --------------------------------------------------------------------- report
n_m, n_s = len(murders), len(shootings)
print(f"edges: {len(events)}  ->  {n_m} murders + {n_s} shootings = {n_m + n_s} incidents")
print("dropped:", dict(drop))
print(
    "murder rows   : "
    f"shooters {sum(len(g['shooters']) for g in murders.values())}, "
    f"assists {sum(len(g['assists']) for g in murders.values())}, "
    f"set claims {sum(len(g['set_claims']) for g in murders.values())}, "
    f"dated {sum(1 for g in murders.values() if len(g['years']) == 1)}, "
    f"year conflicts {sum(1 for g in murders.values() if len(g['years']) > 1)}"
)
print(
    "shooting rows : "
    f"shooters {sum(len(g['shooters']) for g in shootings.values())}, "
    f"assists {sum(len(g['assists']) for g in shootings.values())}, "
    f"set claims {sum(len(g['set_claims']) for g in shootings.values())}"
)
both = set(murders) & set(shootings)
print(f"victims with both a murder and a prior-shooting incident: {len(both)}")

if "--go" not in sys.argv:
    for vid in list(murders)[:3]:
        print("\nsample murder:", display[vid])
        print(json.dumps(payload(vid, murders[vid], True), indent=1)[:600])
    print("\nDRY RUN - re-run with --go")
    sys.exit()

# ------------------------------------------------------------------- seeding
api = Api()

existing = q(f"SELECT id FROM incident WHERE universe_id='{U}'")
if existing:
    if "--wipe" not in sys.argv:
        sys.exit(f"{len(existing)} incidents already in the universe - pass --wipe to replace")
    wiped = 0
    for r in existing:
        x = api.call("DELETE", f"incidents/{r['id']}?universe_id={U}")
        if x and x.get("_error"):
            sys.exit(f"wipe failed on {r['id']}: {x} - fix the delete path, nothing was seeded")
        wiped += 1
    print(f"wiped {wiped} existing incidents")

existing_src = q(f"SELECT id FROM source WHERE universe_id='{U}' AND url='{SITE}'")
if existing_src:
    SRC = existing_src[0]["id"]
else:
    src = api.call(
        "POST",
        "sources/",
        {
            "universe_id": U,
            "url": SITE,
            "title": "privedatabase.wordpress.com",
            "publication": "privedatabase",
            "reliability": "UNVERIFIED",
            "accessed_at": "2026-08-21",
            "notes": (
                "Full harvest of the site, 2026-08-21. Street research, never tested in "
                "court; every attribution seeded from it is a research attribution."
            ),
        },
    )
    if not src or src.get("_error"):
        sys.exit(f"source create failed: {src}")
    SRC = src["id"]
print(f"source: {SRC}")

made = err = 0
t0 = time.time()
for murder, group in ((True, murders), (False, shootings)):
    for vid, g in group.items():
        body = payload(vid, g, murder) | {"source_ids": [SRC]}
        x = api.call("POST", "incidents/", body)
        if x and x.get("_error"):
            err += 1
            if err <= 5:
                print("  fail:", display[vid], x["_error"], x["_body"][:120])
        else:
            made += 1
        if made % 500 == 0 and made:
            print(f"  {made} incidents in {time.time() - t0:.0f}s")
print(f"created {made} incidents, {err} failed, in {time.time() - t0:.0f}s")
