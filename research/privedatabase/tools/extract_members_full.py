"""Extract EVERY person from the Chicago pages - members, victims, targets.

The decision this encodes: people named only as victims ("D.Rose (Buff City)")
are wanted as members too, tied to the set the source names for them. They
matter for stats, memory and future incidents.

Contexts a person can appear in, and what each asserts:
  roster line under MEMBRES          -> member of the page's set; "(décédé)" = dead
  sentence "X est un ..."            -> member of the page's set, with nation/status
  entry under a member's CORPS       -> victim, dead, of the set in their parens
  entry under FUSILLADES/ASSISTANCE  -> target, of the set in their parens
  set-level CORPS lists              -> victim, dead, of the set in their parens
  person page                        -> the subject, plus their events

Outputs (next to this script):
  extract-chicago-people.json   deduped people with set, status, aliases, provenance
  extract-chicago-events.json   perpetrator -> victim edges for the future incident pass
"""

import collections
import html as html_mod
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from chiparse import HDR, SETHDR, lines_of, parse_member  # noqa: E402
from db_sync import norm  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRATCH = pathlib.Path(
    "/tmp/claude-1000/-home-lbzgiu-squiidwiki/e162f253-b7e6-408b-a995-a5bb3bb9c68d/scratchpad"
)

VERB = re.compile(r"\b(est|était|etait|sont|étaient|a été|fut|deviendra|devient)\b", re.I)
DEADP = re.compile(r"d[ée]c[ée]d|tu[ée]e?\b|poignard|mort", re.I)
LOCKED = re.compile(r"incarcér|en prison", re.I)
PAREN = re.compile(r"^(.*?)\s*\(([^)]*)\)\s*$")
SETDESC = re.compile(
    r"est une? sets?|est une? alliance|ennemis? (directs? )?avec"
    r"|fusionn[eé]s? avec|cliqued up avec|est un quartier",
    re.I,
)
ADMIN_TITLES = {"BLOG", "CONTACT", "À PROPOS", "A PROPOS", "WHO WE ARE", "LEXIQUE", "DISCOGRAPHIE"}
PLACEHOLDER = re.compile(r"^\??\?+$|PAS DE PHOTO|AUCUNE PHOTO", re.I)
# Nation abbreviations that show up where a set name would: not sets.
NATION_PARENS = {
    "gd": "Gangster Disciples",
    "bd": "Black Disciples",
    "bds": "Black Disciples",
    "gds": "Gangster Disciples",
    "bps": "Black P. Stones",
    "stones": "Black P. Stones",
    "mc": "Mickey Cobras",
    "vl": "Vice Lords",
    "4ch": "4 Corner Hustlers",
    "igd": "Insane Gangster Disciples",
    "cvl": "Conservative Vice Lords",
    "tvl": "Traveling Vice Lords",
}
NOT_A_SET = {"innocent", "innocente", "innocents", "police", ""}

EVENT_KEY = {
    "bodies": "bodies",
    "shootings": "shootings",
    "assists": "assists",
    "wounded": "wounded",
}


def keyof(header_text):
    """Map a French event header to its event kind."""
    h = header_text.lower().strip()
    if h.startswith("assistance"):
        return "assists"
    if h.startswith(("fusillade", "fusilade")):
        return "shootings"
    if h.startswith("corps"):
        return "bodies"
    if h.startswith("bless"):
        return "wounded"
    return "other"


def split_paren(line):
    """Return (name, paren_text or '')."""
    m = PAREN.match(line.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return line.strip(), ""


def paren_meaning(paren):
    """Classify a paren: ('dead', extra), ('set', set_name, dead?), ('nation', gang), ('none',)."""
    if not paren:
        return ("none",)
    if DEADP.search(paren.split(",")[0]) or norm(paren) in ("decede", "decedee"):
        return ("dead", paren)
    first = paren.split(",")[0].strip()
    rest = paren[len(first) :]
    dead = bool(DEADP.search(rest)) if rest else False
    key = norm(first)
    if key in NATION_PARENS:
        return ("nation", NATION_PARENS[key], dead)
    if key in NOT_A_SET or len(first) < 2:
        return ("none",)
    return ("set", first, dead)


def good_name(n):
    """A usable person name: short, real, not a placeholder."""
    if not n or len(n) < 2 or len(n) > 34:
        return False
    if PLACEHOLDER.search(n):
        return False
    return bool(re.search(r"[A-Za-z0-9]", n))


def extract():
    """Walk every Chicago page and collect people and events."""
    pages = json.loads((ROOT / "raw/pages.json").read_text())
    owner = json.loads((SCRATCH / "wp_owner4.json").read_text())
    alliance_pages = set(json.loads((SCRATCH / "chi_alliance_pages.json").read_text()))

    people = []  # raw sightings; deduped later
    events = []

    def see(
        name,
        *,
        set_title=None,
        nation=None,
        dead=False,
        locked=False,
        aliases=None,
        page=None,
        origin=None,
    ):
        if not good_name(name):
            return
        people.append(
            {
                "name": name.strip(),
                "set": set_title,
                "nation": nation,
                "dead": dead,
                "locked": locked,
                "aliases": aliases or [],
                "page": page,
                "origin": origin,
            }
        )

    for p in pages:
        pid = str(p["ID"])
        if owner.get(p["slug"]) != "chicago":
            continue
        if p["title"].strip().upper() in ADMIN_TITLES:
            continue
        L = lines_of(p)
        if not L:
            continue

        title = html_mod.unescape(p["title"]).strip()
        is_alliance_page = pid in alliance_pages
        is_set_page = bool(SETDESC.search(L[0])) or any(SETHDR.match(x) for x in L)
        page_set = title if (is_set_page and not is_alliance_page) else None

        # Person page: subject is line 0 if it reads like a person sentence.
        subject = None
        if not is_set_page and not is_alliance_page:
            if not VERB.search(L[0]):
                continue  # not a person page either (nav page, list page)
            subject = parse_member(L[0])
            if not good_name(subject["name"]):
                continue
            m = re.search(
                r"membre (?:officiel )?(?:du|de la|de l'|des)\s+([A-Z][\w$./'\- ]{1,25})", L[0]
            )
            subj_set = m.group(1).strip().rstrip(".") if m else None
            see(
                subject["name"],
                set_title=subj_set,
                nation=subject["nation"],
                dead=subject["dead"],
                locked=subject["locked"],
                aliases=subject["aliases"],
                page=pid,
                origin="person-page",
            )

        current = subject  # the member whose events we are reading
        event = None  # open event kind, or None
        in_roster = False  # inside a MEMBRES-style set section
        in_relations = False  # inside ALLIÉS/ENNEMIS - those lines are sets, not people

        for line in L[1:]:
            sh = SETHDR.match(line)
            if sh:
                head = (sh.group(1) or "").upper()
                in_roster = head.startswith(("MEMBRES", "LISTE DES MEMBRES"))
                in_relations = head.startswith(("ALLI", "ENNEMIS"))
                event = "bodies" if "CORPS" in head else None
                current = None
                continue
            h = HDR.match(line)
            if h:
                event = keyof(h.group(1))
                in_relations = False
                continue

            # A sentence introduces a member of this page's set.
            if in_relations and not VERB.search(line):
                continue  # an ally/enemy set name, never a person
            if VERB.search(line) and (len(line) > 24 or re.search(r"\b(est|était)\s+une?\b", line)):
                in_relations = False
                m = parse_member(line)
                if good_name(m["name"]):
                    see(
                        m["name"],
                        set_title=page_set,
                        nation=m["nation"],
                        dead=m["dead"],
                        locked=m["locked"],
                        aliases=m["aliases"],
                        page=pid,
                        origin="member-sentence",
                    )
                    current = m
                event = None
                continue

            # A short entry line.
            name, paren = split_paren(line)
            if not good_name(name):
                continue
            meaning = paren_meaning(paren)

            if meaning[0] == "set":
                # Someone from another set: a victim/target of an event.
                vset, vdead = meaning[1], meaning[2]
                kind = event or "bodies"
                dead = vdead or kind == "bodies"
                see(name, set_title=vset, dead=dead, page=pid, origin=f"event-{kind}")
                perp = current["name"] if current else None
                events.append(
                    {
                        "page": pid,
                        "kind": kind,
                        "perp": perp,
                        "perp_set": page_set,
                        "victim": name,
                        "victim_set": vset,
                        "victim_dead": dead,
                    }
                )
                continue

            if meaning[0] == "nation":
                kind = event or "bodies"
                dead = meaning[2] or kind == "bodies"
                see(name, nation=meaning[1], dead=dead, page=pid, origin=f"event-{kind}")
                events.append(
                    {
                        "page": pid,
                        "kind": kind,
                        "perp": current["name"] if current else None,
                        "perp_set": page_set,
                        "victim": name,
                        "victim_set": None,
                        "victim_dead": dead,
                    }
                )
                continue

            # No paren, or "(décédé)": a roster name of this page's set.
            dead = meaning[0] == "dead"
            if is_alliance_page and in_roster:
                continue  # alliance rosters list sets, not people
            if page_set:
                see(name, set_title=page_set, dead=dead, page=pid, origin="roster")
            elif subject and event:
                # On a person page an unparenthesised event entry is still a victim.
                see(name, dead=dead or event == "bodies", page=pid, origin=f"event-{event}")
                events.append(
                    {
                        "page": pid,
                        "kind": event,
                        "perp": subject["name"],
                        "perp_set": None,
                        "victim": name,
                        "victim_set": None,
                        "victim_dead": dead or event == "bodies",
                    }
                )

    return people, events


def dedupe(people):
    """Collapse sightings into one record per (person, set)."""
    by_key = {}
    for s in people:
        key = (norm(s["name"]), norm(s["set"] or ""))
        r = by_key.setdefault(
            key,
            {
                "name": s["name"],
                "set": s["set"],
                "nation": None,
                "dead": False,
                "locked": False,
                "aliases": [],
                "pages": [],
                "origins": [],
            },
        )
        if len(s["name"]) > len(r["name"]):
            r["name"] = s["name"]
        r["nation"] = r["nation"] or s["nation"]
        r["dead"] = r["dead"] or s["dead"]
        r["locked"] = r["locked"] or s["locked"]
        for a in s["aliases"]:
            if norm(a) not in {norm(x) for x in r["aliases"]} and norm(a) != norm(r["name"]):
                r["aliases"].append(a)
        if s["page"] not in r["pages"]:
            r["pages"].append(s["page"])
        if s["origin"] not in r["origins"]:
            r["origins"].append(s["origin"])

    # Fold setless records into a set-linked one when the name maps to exactly
    # one set; a name on several sets stays split (different people).
    by_name = collections.defaultdict(list)
    for key, r in by_key.items():
        by_name[key[0]].append((key, r))
    out = []
    for _, group in by_name.items():
        linked = [(k, r) for k, r in group if k[1]]
        loose = [(k, r) for k, r in group if not k[1]]
        if linked and loose and len(linked) == 1:
            k, keep = linked[0]
            for _, r in loose:
                keep["dead"] = keep["dead"] or r["dead"]
                keep["locked"] = keep["locked"] or r["locked"]
                keep["nation"] = keep["nation"] or r["nation"]
                for a in r["aliases"]:
                    if norm(a) not in {norm(x) for x in keep["aliases"]}:
                        keep["aliases"].append(a)
                keep["pages"] += [p for p in r["pages"] if p not in keep["pages"]]
                keep["origins"] += [o for o in r["origins"] if o not in keep["origins"]]
            out.append(keep)
            out.extend(r for _, r in linked[1:])
        else:
            out.extend(r for _, r in group)
    return out


def main():
    """Run the extraction and report."""
    people, events = extract()
    deduped = dedupe(people)
    (pathlib.Path(__file__).parent / "extract-chicago-people.json").write_text(
        json.dumps(deduped, ensure_ascii=False, indent=1)
    )
    (pathlib.Path(__file__).parent / "extract-chicago-events.json").write_text(
        json.dumps(events, ensure_ascii=False, indent=1)
    )
    print(f"sightings          : {len(people)}")
    print(f"deduped people     : {len(deduped)}")
    print(f"  with a set       : {sum(1 for r in deduped if r['set'])}")
    print(f"  dead             : {sum(1 for r in deduped if r['dead'])}")
    print(f"  locked           : {sum(1 for r in deduped if r['locked'])}")
    print(f"  with aliases     : {sum(1 for r in deduped if r['aliases'])}")
    print(f"events             : {len(events)}")
    print("origins:", dict(collections.Counter(o for r in deduped for o in r["origins"])))


if __name__ == "__main__":
    main()
