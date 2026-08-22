"""Name and date five NLMB deaths from the "Less Known Fallen Members" threads.

u/AlexRD19's November 2021 post gave a legal name, a date and a press link for five men
the sub barely talked about. Every one of the five checks out, and three of them land on a
Chicago police homicide record:

  Big Los    Carlos Alexander, 33   29 Oct 2012   HV539217, 079XX S ESCANABA AVE
  BabyCrack  Jason Hall, 25         31 Jan 2013   found in his cell at Menard, AP/WSIU
  Lil Tracy  Tracy Gipson, 18       shot 26 Jun 2013, died 27th   HW335531, 075XX S MERRILL
  Lil Boosie Malik Herron, 13       12 Apr 2014   hit-and-run in Gary, Indiana, NBC
  Ceige      Cornell M. Patrick, 27 30 Mar 2017   JA206745, 070XX S SOUTH SHORE DR

Big Los and BabyCrack were already here as names on a kill list with nothing attached.
The other three are new. Affiliates count as members in this database, which is what
settles the two the thread argued about: the poster corrected himself to say Ceige was
LAFA rather than NLMB, and hedged on whether Tracy repped it at all, so both carry their
own set as primary and NLMB alongside it.

Two dates worth knowing about. Tracy was shot at about 1:30am on 26 June and died the
next morning, so the incident is the 26th and his date of death the 27th. Ceige and
Dominique Scott were killed just after 11pm on Thursday 30 March by the Sun-Times, while
the police record timestamps both victims at 01:49 and 01:50 on the 31st; the incident
takes the press date and the police timestamp is recorded in the source note.

Lil Boosie gets no incident row. He was run down by a driver who was never found, and the
incident type enum offers only SHOOTING and MURDER, neither of which is a hit-and-run.

Idempotent: sources and members are found by URL and nickname, incidents by the id they
already have or by the member they were created for.
"""

import sys

from wikiapi import CHICAGO, Api, q

ACCESSED = "2026-08-22"

NLMB = "b2ca28cb-db68-4c0d-935f-5ebc5ad64502"
GUWOPGANG = "0d4f8f7f-251f-4d7f-a825-5c739d80b0d8"
LAFAS = "bfeb2849-1210-4664-bca2-3738deeef5f0"
CIVILIAN = "68c81ec4-d97b-4f9d-990e-c7152019751e"

BIG_LOS = "c75a0882-d50a-4ce2-80ed-047fcc65bd78"
BIG_LOS_INC = "0a3e82a1-f2d6-4897-973d-33a9635c0926"
BABY_CRACK = "3d10690d-2ca3-44da-aedd-8fc1428c9432"
BABY_CRACK_INC = "27126d3e-9e37-4e3a-a426-907acb1c184c"

SOURCES = [
    {
        "key": "los",
        "url": "https://www.dnainfo.com/chicago/20121031/south-chicago/father-football-fan-fatally-shot-near-home/",
        "title": "Father of Four Gunned Down Near His Home",
        "publication": "DNAinfo Chicago",
        "published_at": {"year": 2012, "month": 10, "day": 31, "precision": "YMD"},
        "reliability": "HIGH",
        "archive_url": "http://web.archive.org/web/20241117132841/https://www.dnainfo.com/chicago/20121031/south-chicago/father-football-fan-fatally-shot-near-home/",
        "notes": (
            "Carlos Alexander, 33, shot in the 7900 block of South Escanaba Avenue on the "
            "morning of Monday 29 October 2012. Police say he was walking outside his home "
            "about 10:30am when two unknown offenders approached, opened fire and fled on "
            "foot. Father of four. The 436th Chicago homicide of 2012. DNAinfo is defunct; "
            "read the archived copy. Chicago police record the case as HV539217 at 11:15."
        ),
    },
    {
        "key": "crack",
        "url": "https://www.wsiu.org/state-of-illinois/2013-02-02/menard-prison-inmate-identified",
        "title": "Menard Prison Inmate Identified",
        "publication": "Associated Press via WSIU",
        "published_at": {"year": 2013, "month": 2, "day": 2, "precision": "YMD"},
        "reliability": "HIGH",
        "notes": (
            "Randolph County coroner Randy Dudenbostel identifies the inmate found dead in "
            "his cell at Menard Correctional Center, Chester, as Jason Hall, 25, pronounced "
            "dead at 6:45pm on the Thursday before publication, which is 31 January 2013. "
            "Prison officials called the circumstances suspicious."
        ),
    },
    {
        "key": "tracy",
        "url": "https://www.dnainfo.com/chicago/20130703/south-shore-above-79th/it-still-doesnt-seem-real-teen-killed-week-after-hs-graduation/",
        "title": "'It Still Doesn't Seem Real': Teen Killed a Week After H.S. Graduation",
        "publication": "DNAinfo Chicago",
        "published_at": {"year": 2013, "month": 7, "day": 3, "precision": "YMD"},
        "reliability": "HIGH",
        "archive_url": "http://web.archive.org/web/20241129145741/https://www.dnainfo.com/chicago/20130703/south-shore-above-79th/it-still-doesnt-seem-real-teen-killed-week-after-hs-graduation/",
        "notes": (
            "Tracy Gipson, 18, riding in a car with friends in the 7500 block of South "
            "Merrill Avenue about 1:30am on 26 June 2013 when the car passed a group of six "
            "to eight people and someone opened fire, hitting him in the head. Taken to "
            "Jackson Park then Stroger, pronounced dead the next morning. He had graduated "
            "high school on 19 June and planned to join the Navy. His mother Evelyn Gipson "
            "says he was not in a gang. Chicago police record the case as HW335531."
        ),
    },
    {
        "key": "boosie",
        "url": "https://www.nbcchicago.com/news/local/gary-indiana-hit-run-malik-herron/72534/",
        "title": '"Vehicle of Interest" Located in Gary Hit-and-Run',
        "publication": "NBC Chicago",
        "published_at": {"year": 2014, "month": 4, "day": 14, "precision": "YMD"},
        "reliability": "HIGH",
        "archive_url": "http://web.archive.org/web/20250218002552/https://www.nbcchicago.com/news/local/gary-indiana-hit-run-malik-herron/72534/",
        "notes": (
            "Malik Herron, 13, and Robert Davis were walking in the 4900 block of Vermont "
            "Street in Gary, Indiana on the Saturday evening before publication - 12 April "
            "2014 - when a large dark vehicle left the road and struck them. Herron was "
            "pronounced dead; Davis survived with a dislocated arm and says the car was "
            "doing about 80. A vehicle of interest was found, the driver was not."
        ),
    },
    {
        "key": "ceige",
        "url": "http://chicago.homicidewatch.org/2017/04/03/cornell-patrick-dominique-scott-gunned-down-while-riding-in-van-in-south-shore-where-7-were-killed-in-12-hours-on-thursday/index.html",
        "title": "Cornell Patrick, Dominique Scott gunned down while riding in van in South Shore",
        "publication": "Homicide Watch Chicago / Chicago Sun-Times",
        "published_at": {"year": 2017, "month": 4, "day": 3, "precision": "YMD"},
        "reliability": "HIGH",
        "archive_url": "http://web.archive.org/web/20241115142253/http://chicago.homicidewatch.org/2017/04/03/cornell-patrick-dominique-scott-gunned-down-while-riding-in-van-in-south-shore-where-7-were-killed-in-12-hours-on-thursday/index.html",
        "notes": (
            "Cornell M. Patrick, 27, of South Deering and Dominique Victoria Scott, 23, of "
            "Gary, Indiana, riding in a grey van southbound on South Shore Drive just after "
            "11pm on Thursday 30 March 2017 when a black Jeep pulled alongside near 70th "
            "Street and a shooter opened fire. Scott was hit in the side of the head in the "
            "front passenger seat, Patrick in the side of the body in the back. The van "
            "crashed into a pole at 71st Street and both were pronounced dead at the scene. "
            "The sixth and seventh killed within an eight-block radius in twelve hours. "
            "Chicago police record both victims under case JA206745 but timestamp them "
            "01:49 and 01:50 on 31 March."
        ),
    },
    {
        "key": "thread_fallen",
        "url": "https://www.reddit.com/r/Chiraqology/comments/qsisez/less_known_fallen_members_2nlmb_edition/",
        "title": "Less Known Fallen Members 2 (NLMB Edition)",
        "publication": "Reddit - r/Chiraqology",
        "published_at": {"year": 2021, "month": 11, "day": 12, "precision": "YMD"},
        "reliability": "UNVERIFIED",
        "notes": (
            "u/AlexRD19's write-up, which supplied every legal name here and a press link "
            "for each. It adds what the press does not: that Big Los was Mally's uncle, "
            "that NLMB also goes by Boosie Gang for Malik Herron, that Herbo named Tracy in "
            "a song, and that Tracy was TTD, now GuwopGang. In the comments the poster "
            "corrects himself on Ceige: LAFA, not NLMB."
        ),
    },
    {
        "key": "thread_cards",
        "url": "https://www.reddit.com/r/Chiraqology/comments/rix0xq/richie_rich_nlmb_x_baby_crack_nlmb_funeral_cards/",
        "title": "Richie Rich (NLMB) x Baby Crack (NLMB) Funeral Cards",
        "publication": "Reddit - r/Chiraqology",
        "published_at": {"year": 2021, "month": 12, "day": 18, "precision": "YMD"},
        "reliability": "UNVERIFIED",
        "notes": (
            "Funeral card photo. u/LilTrouble060 sets out the run of NLMB losses: Baby "
            "Crack, Kobe, C-Moe and Pistol P in 2013, Big Los, Roc and Alamo in 2012. "
            "u/dream-tha-menace9 corrects two other dates in the same thread - Whitefolkz "
            "died November 2011, G Millz on Christmas Day 2016 - neither of which is "
            "applied here."
        ),
    },
]

LOS_BIO = "Father of four. Friends said he was out of the life and taking care of his family."
# Nothing survives the strip: his set, status, date, sentence and the way he died are
# all columns, the incarceration row and the incident. An empty bio is the right answer,
# and the column is NOT NULL, so it must be "" rather than None.
CRACK_BIO = ""
TRACY_BIO = (
    "Graduated high school on 19 June 2013, eight days before he died, and was planning to "
    "join the Navy to help pay for college. A star point guard. His mother Evelyn says he "
    "was not in a gang."
)
BOOSIE_BIO = (
    "Thirteen. His mother had moved the family out to Indiana to keep him away from the "
    "violence. NLMB also goes by Boosie Gang for him."
)
CEIGE_BIO = "From South Deering."
SCOTT_BIO = "From Gary, Indiana. In the front passenger seat, and not the reason for the shooting."

LOS_NARRATIVE = (
    "Carlos Alexander was walking outside his home in the 7900 block of South Escanaba "
    "Avenue, South Chicago, at about 10:30 on the morning of Monday 29 October 2012, "
    "returning from a corner store, when two men approached him and opened fire before "
    "fleeing on foot. He was 33 and the father of four. Chicago police record the case as "
    "HV539217. It was the 436th homicide in Chicago that year, putting the city past its "
    "total for all of 2011."
)
CRACK_NARRATIVE = (
    "Jason Hall was found dead in his cell at Menard Correctional Center in Chester, "
    "Illinois, and pronounced dead at 6:45pm on Thursday 31 January 2013. He was 25. "
    "Prison officials called the circumstances suspicious. He was serving thirteen years "
    "and was scheduled for parole in November 2015."
)
TRACY_NARRATIVE = (
    "Tracy Gipson, 18, was riding in a car with friends in the 7500 block of South Merrill "
    "Avenue, South Shore, at about 1:30 in the morning of 26 June 2013. As the car passed a "
    "group of six to eight people on the sidewalk, someone in the group opened fire and hit "
    "him in the head. He was taken to Jackson Park Hospital, transferred to Stroger, and "
    "pronounced dead the next morning. Chicago police record the case as HW335531."
)
CEIGE_NARRATIVE = (
    "Cornell Patrick, 27, and Dominique Scott, 23, were riding in a grey van southbound on "
    "South Shore Drive just after 11pm on Thursday 30 March 2017 when a black Jeep pulled "
    "alongside near 70th Street and a shooter opened fire. Scott, in the front passenger "
    "seat, was hit in the side of the head; Patrick was hit in the side of the body in the "
    "back seat. The van crashed into a pole at 71st Street and both were pronounced dead at "
    "the scene. They were the sixth and seventh people killed within an eight-block radius "
    "of South Shore in twelve hours. Chicago police record both under case JA206745."
)


def ensure_sources(api):
    """Create any source that is not already present, and return {key: id}."""
    ids = {}
    for spec in SOURCES:
        spec = dict(spec)
        key = spec.pop("key")
        rows = q(f"SELECT id FROM source WHERE url = '{spec['url']}'")
        if rows:
            ids[key] = rows[0]["id"]
            print(f"source exists   {key:14s} {ids[key]}")
            continue
        made = api.call(
            "POST", "sources/", {"universe_id": CHICAGO, "accessed_at": ACCESSED, **spec}
        )
        if "_error" in made:
            sys.exit(f"source create failed for {key}: {made}")
        ids[key] = made["id"]
        print(f"source created  {key:14s} {ids[key]}")
    return ids


def ensure_member(api, nickname, payload):
    """Find a member by nickname, or create it; return the id."""
    rows = q(f"SELECT id FROM member WHERE nickname = '{nickname}' AND universe_id = '{CHICAGO}'")
    if rows:
        print(f"member exists   {nickname:12s} {rows[0]['id']}")
        return rows[0]["id"]
    made = api.call("POST", "members/", {"universe_id": CHICAGO, "nickname": nickname, **payload})
    if "_error" in made:
        sys.exit(f"member create failed for {nickname}: {made}")
    print(f"member created  {nickname:12s} {made['id']}")
    return made["id"]


def update_member(api, member_id, who, payload, source_ids):
    """PATCH a member, merging the given sources into whatever it already has."""
    cur = api.call("GET", f"members/{member_id}?universe_id={CHICAGO}")
    payload = dict(payload)
    payload["source_ids"] = sorted(set(cur.get("source_ids", [])) | set(source_ids))
    r = api.call("PATCH", f"members/{member_id}?universe_id={CHICAGO}", payload)
    if "_error" in r:
        sys.exit(f"{who} update failed: {r}")
    print(f"member updated  {who:12s} {r.get('legal_name')} d. {r['date_of_death']['year']}")


def date_incident(api, incident_id, date, location, lat, lng, narrative, sources):
    """Date and locate an existing incident, keeping its participants and their flags."""
    rows = q(
        "SELECT member_id, role, outcome, acquitted, notes FROM incident_participant "
        f"WHERE incident_id = '{incident_id}'"
    )
    participants = [
        {
            "member_id": r["member_id"],
            "role": r["role"],
            "outcome": r["outcome"],
            "acquitted": r["acquitted"],
            "notes": r["notes"],
        }
        for r in rows
    ]
    r = api.call(
        "PATCH",
        f"incidents/{incident_id}?universe_id={CHICAGO}",
        {
            "date": date,
            "location_text": location,
            "lat": lat,
            "lng": lng,
            "narrative": narrative,
            "verified": True,
            "participants": participants,
            "source_ids": sources,
        },
    )
    if "_error" in r:
        sys.exit(f"incident {incident_id} failed: {r}")
    print(f"incident dated  {incident_id[:8]}     {location}")


def main():
    """Name, date and source the five, creating the three that are not here yet."""
    api = Api()
    mode = api.call("GET", "admin/db-mode")
    if mode.get("mode") != "prod":
        sys.exit(f"backend is in {mode.get('mode')!r} mode, refusing to write")

    src = ensure_sources(api)
    cpd = q("SELECT id FROM source WHERE title LIKE 'Chicago Police recorded crime%'")
    cpd_id = cpd[0]["id"] if cpd else None
    threads = [src["thread_fallen"], src["thread_cards"]]

    def srcs(*keys):
        out = [src[k] for k in keys] + threads
        return out + [cpd_id] if cpd_id else out

    # --- Big Los ------------------------------------------------------------
    update_member(
        api,
        BIG_LOS,
        "Big Los",
        {
            "legal_name": "Carlos Alexander",
            "status": "DEAD",
            "date_of_death": {"year": 2012, "month": 10, "day": 29, "precision": "YMD"},
            "biography": LOS_BIO,
        },
        srcs("los"),
    )
    date_incident(
        api,
        BIG_LOS_INC,
        {"year": 2012, "month": 10, "day": 29, "precision": "YMD"},
        "7900 block S. Escanaba Ave, South Chicago",
        41.751331394,
        -87.554103407,
        LOS_NARRATIVE,
        srcs("los"),
    )

    # --- BabyCrack ----------------------------------------------------------
    update_member(
        api,
        BABY_CRACK,
        "BabyCrack",
        {
            "legal_name": "Jason Hall",
            "status": "DEAD",
            "date_of_death": {"year": 2013, "month": 1, "day": 31, "precision": "YMD"},
            "biography": CRACK_BIO,
        },
        srcs("crack"),
    )
    date_incident(
        api,
        BABY_CRACK_INC,
        {"year": 2013, "month": 1, "day": 31, "precision": "YMD"},
        "Menard Correctional Center, Chester, Illinois",
        None,
        None,
        CRACK_NARRATIVE,
        srcs("crack"),
    )

    # --- Lil Tracy ----------------------------------------------------------
    tracy = ensure_member(
        api,
        "Lil Tracy",
        {
            "legal_name": "Tracy Gipson",
            "status": "DEAD",
            "biography": TRACY_BIO,
            "affiliations": [
                {"set_id": GUWOPGANG, "is_primary": True},
                {"set_id": NLMB, "is_primary": False},
            ],
        },
    )
    update_member(
        api,
        tracy,
        "Lil Tracy",
        {
            "legal_name": "Tracy Gipson",
            "status": "DEAD",
            "date_of_death": {"year": 2013, "month": 6, "day": 27, "precision": "YMD"},
            "biography": TRACY_BIO,
        },
        srcs("tracy"),
    )

    if not q(f"SELECT 1 FROM incident_participant WHERE member_id = '{tracy}'"):
        made = api.call(
            "POST",
            "incidents/",
            {
                "universe_id": CHICAGO,
                "type": "MURDER",
                "date": {"year": 2013, "month": 6, "day": 26, "precision": "YMD"},
                "location_text": "7500 block S. Merrill Ave, South Shore, Chicago",
                "lat": 41.75829879,
                "lng": -87.572473045,
                "narrative": TRACY_NARRATIVE,
                "verified": True,
                "participants": [
                    {
                        "member_id": tracy,
                        "role": "VICTIM",
                        "outcome": "KILLED",
                        "acquitted": False,
                        "notes": "Tracy Gipson, 18. Shot in the head in the back of a "
                        "passing car; died the following morning at Stroger.",
                    }
                ],
                "source_ids": srcs("tracy"),
            },
        )
        if "_error" in made:
            sys.exit(f"Tracy incident create failed: {made}")
        print(f"incident created {made['id'][:8]}    Lil Tracy")
    else:
        print("incident exists  Lil Tracy")

    # --- Lil Boosie: no incident, the type enum has nothing for a hit-and-run --
    boosie = ensure_member(
        api,
        "Lil Boosie",
        {
            "legal_name": "Malik Herron",
            "status": "DEAD",
            "biography": BOOSIE_BIO,
            "affiliations": [{"set_id": NLMB, "is_primary": True}],
        },
    )
    update_member(
        api,
        boosie,
        "Lil Boosie",
        {
            "legal_name": "Malik Herron",
            "status": "DEAD",
            "date_of_death": {"year": 2014, "month": 4, "day": 12, "precision": "YMD"},
            "biography": BOOSIE_BIO,
        },
        srcs("boosie"),
    )

    # --- Ceige and Dominique Scott -----------------------------------------
    ceige = ensure_member(
        api,
        "Ceige",
        {
            "legal_name": "Cornell M. Patrick",
            "status": "DEAD",
            "biography": CEIGE_BIO,
            "affiliations": [
                {"set_id": LAFAS, "is_primary": True},
                {"set_id": NLMB, "is_primary": False},
            ],
        },
    )
    scott = ensure_member(
        api,
        "Dominique Scott",
        {
            "legal_name": "Dominique Victoria Scott",
            "nickname_unknown": True,
            "status": "DEAD",
            "biography": SCOTT_BIO,
            "affiliations": [{"set_id": CIVILIAN, "is_primary": True}],
        },
    )
    for member_id, who in ((ceige, "Ceige"), (scott, "Dominique Scott")):
        update_member(
            api,
            member_id,
            who,
            {
                "status": "DEAD",
                "date_of_death": {"year": 2017, "month": 3, "day": 30, "precision": "YMD"},
            },
            srcs("ceige"),
        )

    existing = q(
        "SELECT DISTINCT incident_id FROM incident_participant "
        f"WHERE member_id IN ('{ceige}', '{scott}')"
    )
    if existing:
        incident_id = existing[0]["incident_id"]
        print(f"incident exists {incident_id[:8]}")
    else:
        made = api.call(
            "POST",
            "incidents/",
            {
                "universe_id": CHICAGO,
                "type": "MURDER",
                "date": {"year": 2017, "month": 3, "day": 30, "precision": "YMD"},
                "location_text": "S. South Shore Dr at 70th St, South Shore, Chicago",
                "lat": 41.766823898,
                "lng": -87.56648168,
                "narrative": CEIGE_NARRATIVE,
                "verified": True,
                "participants": [
                    {
                        "member_id": ceige,
                        "role": "VICTIM",
                        "outcome": "KILLED",
                        "acquitted": False,
                        "notes": "Cornell M. Patrick, 27. Shot in the side of the body in the "
                        "back seat of the van.",
                    },
                    {
                        "member_id": scott,
                        "role": "VICTIM",
                        "outcome": "KILLED",
                        "acquitted": False,
                        "notes": "Dominique Victoria Scott, 23. Shot in the side of the head "
                        "in the front passenger seat.",
                    },
                ],
                "source_ids": srcs("ceige"),
            },
        )
        if "_error" in made:
            sys.exit(f"Ceige incident create failed: {made}")
        print(f"incident created {made['id'][:8]}    Ceige and Dominique Scott")

    # BabyCrack's sentence belongs in its own table, not in prose.
    if not q(f"SELECT id FROM member_incarceration WHERE member_id = '{BABY_CRACK}'"):
        r = api.call(
            "POST",
            f"members/{BABY_CRACK}/incarcerations?universe_id={CHICAGO}",
            {
                "facility": "Menard Correctional Center",
                "notes": (
                    "Thirteen years for a vehicular hijacking with a weapon in 2009, "
                    "scheduled for parole in November 2015. Killed inside."
                ),
            },
        )
        if isinstance(r, dict) and "_error" in r:
            print(f"  incarceration not created: {r['_error']} {r['_body'][:140]}")
        else:
            print("incarceration   BabyCrack    Menard, 13 years")
    else:
        print("incarceration   BabyCrack    already present")


if __name__ == "__main__":
    main()
