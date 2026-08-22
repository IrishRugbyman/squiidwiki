"""Name, date and illustrate five more NLMB deaths, from Part 1 of the same series.

u/AlexRD19's October 2021 post covered three, and a Reddit sweep for the rest of the
roster turned up two more with hard dates. What is carried, and how well each is held up:

  Breezy Lord  Terrence Brooks, 32   26 Nov 2019  Sun-Times + case JC525875, 083XX S CRANDON
  Tedo G       Tristan Rogers, 34     5 Apr 2020  Sun-Times confirms the hit-and-run, not the name
  Marquis      Marquis Macon-Lewis, 23  1 Oct 2022 Sun-Times + case JF418383, 003XX W 110TH
  Kobe         -                     10 Aug 2013  anniversary post only
  Millie       Camille Johnson, 32   12 Jun 2019  the thread only

Each carries a photograph, which is the other thing the threads have that nothing else
does: Breezy, Tedo G and Millie from Lightshot captures inside the posts, Kobe and Marquis
from the Reddit image host.

Three of the five are worth being careful about, and the notes on each source say so:

- **Tedo G's name is not in the article.** The Sun-Times piece confirms a 34-year-old man
  struck at 2:10am on 5 April 2020 in the 1700 block of East 67th Street and describes the
  car, but never names him. Tristan Rogers comes from the thread alone.
- **Kobe has a date and nothing else.** An August 2026 post says he was killed thirteen
  years ago that day, which gives 10 August 2013 and agrees with a separate thread putting
  him among the 2013 losses. Police recorded a homicide that morning in the 2400 block of
  East 79th Street, the block beside where Alamo and Roc were killed, but nothing ties that
  record to him by name, so his incident is dated and left unlocated.
- **Millie's death is not a police matter.** A commenter says natural causes at 32. The
  Cook County medical examiner's archive holds no woman of that age dying that day, which
  is what you would expect for a natural death that needed no investigation, so it neither
  supports nor contradicts. She is the Dell Mob row already here, now also NLMB.

Marquis is a straight correction: the thread calls him Marquis Lewis and 21, the Sun-Times
names him Marquis Macon-Lewis and 23. The man killed hours earlier on the same block, whom
the thread calls Arab G of Welch World, was Laparish Brown, 30. He is not seeded here - a
separate shooting needs its own incident and its own look.
"""

import os
import subprocess
import sys

from wikiapi import CHICAGO, Api, q

IMAGES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images")
ACCESSED = "2026-08-22"

NLMB = "b2ca28cb-db68-4c0d-935f-5ebc5ad64502"
KOBE = "c8e91a92-5f0f-4d12-b116-906446516f1f"
KOBE_INC = "b337eed4-c6ec-4761-8683-86d374febeee"
MARQUIS = "157e6867-6d32-4891-b45e-3126f52c1070"
MARQUIS_INC = "6f2d9d61-c0ff-43da-b7cb-9ddcaf123170"
MILLIE = "12df2da3-f1f3-4c77-8611-b9263302718e"

SOURCES = [
    {
        "key": "part1",
        "url": "https://www.reddit.com/r/Chiraqology/comments/qg6p1k/less_known_fallen_members_1nlmb_edition/",
        "title": "Less Known Fallen Members 1 (NLMB Edition)",
        "publication": "Reddit - r/Chiraqology",
        "published_at": {"year": 2021, "month": 10, "day": 26, "precision": "YMD"},
        "reliability": "UNVERIFIED",
        "notes": (
            "u/AlexRD19 on Millie, Breezy Lord and Tedo G, with a photograph of each. It "
            "gives Millie as Camille Johnson, died 12 June 2019, a mother, repping NLMB and "
            "Dell Mob; Breezy as Terrance Brooks, chased and killed in MLVB territory, "
            "father of two, close to Joc, Lon, Trigga, WhyteBoy and Ramo; and Tedo G as "
            "Tristan Rogers, close to Kobe, Joc, WhyteBoy and G Rell, also a father. "
            "u/Joey926 adds that Millie repped Dell Mob, had OJ of Dell Mob tattooed on her "
            "face, and died of natural causes. In the comments the poster notes G-Red and "
            "Breezy share the surname Brooks and are most likely brothers, and that the "
            "article spells Breezy's first name Terrence where a legal firm has Terrance."
        ),
    },
    {
        "key": "breezy",
        "url": "https://chicago.suntimes.com/crime/2019/11/26/20985026/terrance-brooks-south-chicago-shooting-homicide-gun-violence-crandon",
        "title": "Man fatally shot in South Chicago",
        "publication": "Chicago Sun-Times",
        "published_at": {"year": 2019, "month": 11, "day": 26, "precision": "YMD"},
        "reliability": "HIGH",
        "notes": (
            "Terrence Brooks, 32, shot at about 9:15pm on Tuesday 26 November 2019 in the "
            "8300 block of South Crandon Avenue, South Chicago. He had just got out of a "
            "vehicle when a man approached and opened fire, chasing him down the street and "
            "shooting as he went; he was hit several times in the head and died at the "
            "scene. No one in custody. Chicago police record the case as JC525875."
        ),
    },
    {
        "key": "tedo",
        "url": "https://chicago.suntimes.com/crime/2020/4/9/21214702/police-seek-car-wanted-fatal-hit-and-run-67-street-woodlawn",
        "title": "Police seek car wanted in fatal hit-and-run on 67th Street in Woodlawn",
        "publication": "Chicago Sun-Times",
        "published_at": {"year": 2020, "month": 4, "day": 9, "precision": "YMD"},
        "reliability": "HIGH",
        "notes": (
            "A 34-year-old man struck and killed at about 2:10am on Sunday 5 April 2020 in "
            "the 1700 block of East 67th Street, Woodlawn. The driver of a dark four-door "
            "sedan with likely front-end damage fled west. The article does not name the "
            "man; Tristan Rogers comes from the r/Chiraqology thread, and the age and the "
            "circumstances are what match."
        ),
    },
    {
        "key": "marquis",
        "url": "https://chicago.suntimes.com/crime/2022/10/1/23382858/man-killed-in-roseland-shooting-hours-after-another-fatally-shot-in-same-block",
        "title": "Man killed in Roseland shooting hours after another fatally shot in same block",
        "publication": "Chicago Sun-Times",
        "published_at": {"year": 2022, "month": 10, "day": 1, "precision": "YMD"},
        "reliability": "HIGH",
        "notes": (
            "Marquis Macon-Lewis, 23, found with multiple gunshot wounds at about 9:05pm on "
            "Saturday 1 October 2022 in the 300 block of West 110th Street, Roseland, and "
            "pronounced dead at the University of Chicago Medical Center. Laparish Brown, "
            "30, had been shot in the head in the same block earlier that afternoon. "
            "Witnesses heard shots and saw no one; no arrests. The thread that names him "
            "NLMB/ScoGang gives his name as Marquis Lewis and his age as 21; this is the "
            "correction. Chicago police record the two under JF418383 and JF417847."
        ),
    },
    {
        "key": "kobe",
        "url": "https://www.reddit.com/r/Chiraqology/comments/1vkd8kt/rip_kobe_nlmb_he_was_killed_on_this_day_13_years/",
        "title": "RIP Kobe (NLMB). He was Killed on this day 13 years ago.",
        "publication": "Reddit - r/Chiraqology",
        "published_at": {"year": 2026, "month": 8, "day": 10, "precision": "YMD"},
        "reliability": "UNVERIFIED",
        "notes": (
            "Anniversary post carrying his photograph, dated 10 August 2026 and saying he "
            "was killed thirteen years earlier, which gives 10 August 2013. A separate "
            "thread lists him among the 2013 NLMB losses alongside C-Moe and Pistol P. "
            "Chicago police recorded a homicide at 04:02 that morning in the 2400 block of "
            "East 79th Street, case HW401231, one block from where Alamo and Roc were "
            "killed, but no source names the victim, so that record is not claimed for him."
        ),
    },
]

BREEZY_BIO = "Father of two. Close to Joc, Lon, Trigga, WhyteBoy and Ramo."
TEDO_BIO = "A father. Close to Kobe, Joc, WhyteBoy and G Rell."
MILLIE_BIO = (
    "A mother, and a woman in a set of men: shorties repped her, and some go by MillieWay "
    "or Millie2x for her. She carried OJ's name tattooed on her face."
)

BREEZY_NARRATIVE = (
    "Terrence Brooks, 32, had just got out of a vehicle in the 8300 block of South Crandon "
    "Avenue, South Chicago, at about 9:15pm on Tuesday 26 November 2019 when a man walked "
    "up and opened fire. The gunman chased him down the street shooting as he went. Brooks "
    "was hit several times in the head, collapsed nearby and was pronounced dead at the "
    "scene. Chicago police record the case as JC525875, and r/Chiraqology places the block "
    "in MLVB territory."
)
MARQUIS_NARRATIVE = (
    "Marquis Macon-Lewis, 23, was found with multiple gunshot wounds at about 9:05pm on "
    "Saturday 1 October 2022 in the 300 block of West 110th Street, Roseland, and died at "
    "the University of Chicago Medical Center. Laparish Brown, 30, known on the street as "
    "Arab G of Welch World, had been shot in the head in the same block that afternoon. "
    "Witnesses heard the shots and saw no one. Chicago police record the case as JF418383."
)
KOBE_NARRATIVE = (
    "Killed on 10 August 2013. The place is not established: no source names him in a "
    "police record, and the date rests on an anniversary post that carries his photograph."
)

PHOTOS = [
    (
        KOBE,
        "kobe-chiraqology.jpg",
        "image/jpeg",
        "Kobe, from the r/Chiraqology post marking 13 years since his death",
    ),
    (
        MARQUIS,
        "marquis-macon-lewis-chiraqology.jpg",
        "image/jpeg",
        "Marquis Macon-Lewis, from the r/Chiraqology post identifying him",
    ),
    (
        MILLIE,
        "millie-nlmb-chiraqology.png",
        "image/png",
        "Millie in an NLMB shirt, from Less Known Fallen Members 1",
    ),
]


def ensure_sources(api):
    """Create any source not already present; return {key: id}."""
    ids = {}
    for spec in SOURCES:
        spec = dict(spec)
        key = spec.pop("key")
        rows = q(f"SELECT id FROM source WHERE url = '{spec['url']}'")
        if rows:
            ids[key] = rows[0]["id"]
            print(f"source exists   {key:9s} {ids[key]}")
            continue
        made = api.call(
            "POST", "sources/", {"universe_id": CHICAGO, "accessed_at": ACCESSED, **spec}
        )
        if "_error" in made:
            sys.exit(f"source create failed for {key}: {made}")
        ids[key] = made["id"]
        print(f"source created  {key:9s} {ids[key]}")
    return ids


def patch_member(api, member_id, who, payload, source_ids):
    """PATCH a member, merging sources into whatever it already carries."""
    cur = api.call("GET", f"members/{member_id}?universe_id={CHICAGO}")
    payload = dict(payload)
    payload["source_ids"] = sorted(set(cur.get("source_ids", [])) | set(source_ids))
    r = api.call("PATCH", f"members/{member_id}?universe_id={CHICAGO}", payload)
    if "_error" in r:
        sys.exit(f"{who} update failed: {r}")
    print(f"member updated  {who:12s} {r.get('legal_name') or '(no legal name)'}")
    return r


def make_member(api, nickname, payload):
    """Find a member by nickname or create it."""
    rows = q(f"SELECT id FROM member WHERE nickname = '{nickname}' AND universe_id = '{CHICAGO}'")
    if rows:
        print(f"member exists   {nickname:12s} {rows[0]['id']}")
        return rows[0]["id"]
    made = api.call("POST", "members/", {"universe_id": CHICAGO, "nickname": nickname, **payload})
    if "_error" in made:
        sys.exit(f"member create failed for {nickname}: {made}")
    print(f"member created  {nickname:12s} {made['id']}")
    return made["id"]


def patch_incident(api, incident_id, payload):
    """PATCH an incident, rebuilding participants so acquitted and notes survive."""
    rows = q(
        "SELECT member_id, role, outcome, acquitted, notes FROM incident_participant "
        f"WHERE incident_id = '{incident_id}'"
    )
    payload = dict(payload)
    payload["participants"] = [
        {
            "member_id": r["member_id"],
            "role": r["role"],
            "outcome": r["outcome"],
            "acquitted": r["acquitted"],
            "notes": r["notes"],
        }
        for r in rows
    ]
    r = api.call("PATCH", f"incidents/{incident_id}?universe_id={CHICAGO}", payload)
    if "_error" in r:
        sys.exit(f"incident {incident_id} failed: {r}")
    print(f"incident dated  {incident_id[:8]}     {payload.get('location_text') or '(unlocated)'}")


def main():
    """Apply everything Part 1 and the sweep established."""
    api = Api()
    mode = api.call("GET", "admin/db-mode")
    if mode.get("mode") != "prod":
        sys.exit(f"backend is in {mode.get('mode')!r} mode, refusing to write")

    src = ensure_sources(api)

    # --- Breezy Lord (new) --------------------------------------------------
    breezy = make_member(
        api,
        "Breezy Lord",
        {
            "legal_name": "Terrence Brooks",
            "status": "DEAD",
            "biography": BREEZY_BIO,
            "affiliations": [{"set_id": NLMB, "is_primary": True}],
        },
    )
    patch_member(
        api,
        breezy,
        "Breezy Lord",
        {
            "legal_name": "Terrence Brooks",
            "status": "DEAD",
            "biography": BREEZY_BIO,
            "date_of_death": {"year": 2019, "month": 11, "day": 26, "precision": "YMD"},
        },
        [src["breezy"], src["part1"]],
    )

    if not q(f"SELECT 1 FROM incident_participant WHERE member_id = '{breezy}'"):
        made = api.call(
            "POST",
            "incidents/",
            {
                "universe_id": CHICAGO,
                "type": "MURDER",
                "date": {"year": 2019, "month": 11, "day": 26, "precision": "YMD"},
                "location_text": "8300 block S. Crandon Ave, South Chicago",
                "lat": 41.743533066,
                "lng": -87.568543393,
                "narrative": BREEZY_NARRATIVE,
                "verified": True,
                "participants": [
                    {
                        "member_id": breezy,
                        "role": "VICTIM",
                        "outcome": "KILLED",
                        "acquitted": False,
                        "notes": "Terrence Brooks, 32. Chased down the street on foot "
                        "and shot several times in the head.",
                    }
                ],
                "source_ids": [src["breezy"], src["part1"]],
            },
        )
        if "_error" in made:
            sys.exit(f"Breezy incident failed: {made}")
        print(f"incident created {made['id'][:8]}    Breezy Lord")
    else:
        print("incident exists  Breezy Lord")

    # --- Tedo G (new). Hit-and-run, so no incident row. ----------------------
    tedo = make_member(
        api,
        "Tedo G",
        {
            "legal_name": "Tristan Rogers",
            "status": "DEAD",
            "biography": TEDO_BIO,
            "affiliations": [{"set_id": NLMB, "is_primary": True}],
        },
    )
    patch_member(
        api,
        tedo,
        "Tedo G",
        {
            "legal_name": "Tristan Rogers",
            "status": "DEAD",
            "biography": TEDO_BIO,
            "date_of_death": {"year": 2020, "month": 4, "day": 5, "precision": "YMD"},
        },
        [src["tedo"], src["part1"]],
    )

    # --- Marquis (existing) -------------------------------------------------
    patch_member(
        api,
        MARQUIS,
        "Marquis",
        {
            "legal_name": "Marquis Macon-Lewis",
            "status": "DEAD",
            "date_of_death": {"year": 2022, "month": 10, "day": 1, "precision": "YMD"},
        },
        [src["marquis"]],
    )
    patch_incident(
        api,
        MARQUIS_INC,
        {
            "date": {"year": 2022, "month": 10, "day": 1, "precision": "YMD"},
            "location_text": "300 block W. 110th St, Roseland, Chicago",
            "lat": 41.692268,
            "lng": -87.627851,
            "narrative": MARQUIS_NARRATIVE,
            "verified": True,
            "source_ids": [src["marquis"]],
        },
    )

    # --- Kobe (existing): a date and a photograph, no place ------------------
    patch_member(
        api,
        KOBE,
        "Kobe",
        {
            "status": "DEAD",
            "date_of_death": {"year": 2013, "month": 8, "day": 10, "precision": "YMD"},
        },
        [src["kobe"]],
    )
    patch_incident(
        api,
        KOBE_INC,
        {
            "date": {"year": 2013, "month": 8, "day": 10, "precision": "YMD"},
            "narrative": KOBE_NARRATIVE,
            "source_ids": [src["kobe"]],
        },
    )

    # --- Millie (existing, Dell Mob): add NLMB, name and date ---------------
    cur = api.call("GET", f"members/{MILLIE}?universe_id={CHICAGO}")
    affs = [
        {"set_id": a["set_id"], "is_primary": a.get("is_primary", False)}
        for a in (cur.get("affiliations") or [])
    ]
    if not any(a["set_id"] == NLMB for a in affs):
        affs.append({"set_id": NLMB, "is_primary": False})
    patch_member(
        api,
        MILLIE,
        "Millie",
        {
            "legal_name": "Camille Johnson",
            "status": "DEAD",
            "biography": MILLIE_BIO,
            "date_of_death": {"year": 2019, "month": 6, "day": 12, "precision": "YMD"},
            "affiliations": affs,
        },
        [src["part1"]],
    )

    # --- photographs --------------------------------------------------------
    all_photos = PHOTOS + [
        (
            breezy,
            "breezy-lord-chiraqology.png",
            "image/png",
            "Breezy Lord, from Less Known Fallen Members 1",
        ),
        (tedo, "tedo-g-chiraqology.png", "image/png", "Tedo G, from Less Known Fallen Members 1"),
    ]
    for member_id, filename, ctype, caption in all_photos:
        path = os.path.join(IMAGES, filename)
        if not os.path.exists(path):
            sys.exit(f"missing photo: {path}")
        if q(f"SELECT 1 FROM media WHERE member_id = '{member_id}' AND caption = '{caption}'"):
            print(f"photo exists    {filename}")
            continue
        r = subprocess.run(
            [
                "curl",
                "-sS",
                "-X",
                "POST",
                "http://localhost:8001/api/v1/media/",
                "-H",
                f"Authorization: Bearer {api.token}",
                "-F",
                f"file=@{path};type={ctype}",
                "-F",
                f"universe_id={CHICAGO}",
                "-F",
                f"member_id={member_id}",
                "-F",
                f"caption={caption}",
            ],
            capture_output=True,
            text=True,
        )
        ok = '"id"' in r.stdout
        print(f"photo {'uploaded' if ok else 'FAILED  '}  {filename}  {r.stdout[:110]}")


if __name__ == "__main__":
    main()
