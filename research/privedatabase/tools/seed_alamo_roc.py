"""Merge the split Alamo/Roc murders into the one shooting they actually were.

NLMB Alamo and NLMB Roc were killed together: a drive-by outside a liquor store in the
2500 block of East 79th Street, South Shore, on the evening of Sunday 19 February 2012.
The privedatabase corpus lists bodies one name at a time under the man credited with
them, so the extraction turned one double murder into two undated, unlocated incidents -
one per victim, each with KTS Von as shooter. This script folds them back into one.

The date and the names did not come from the corpus, which carries neither. Two
r/Chiraqology threads (2021 and 2025) named the pair and dated the killing to 2012, and
the 2025 thread was posted on the thirteenth anniversary, which pointed at 19 February.
Three independent public records confirm it:

- Chicago's open crime data has two homicide records under one case number, HV164849,
  both stamped 2012-02-19 18:40 at 025XX E 79TH ST in community area 43 (South Shore),
  and the case carries an arrest.
- The RedEye homicide tracker, archived eight days after the shooting, lists
  `Jamal Harris, 19` and `Gregory Glinsey, 54` at 2500 E. 79th St. on 2/19/12.
- ABC7 and NBC Chicago reported the drive-by that night: seven shot, Harris found inside
  the store after running in, Glinsey shot outside and called an innocent victim by
  police. gunmemorial.org carries both street names - Gregory "Alamo" Glinsey, 53, and
  Jamal "Roc" Harris, 19 - so neither nickname rests on the forum threads alone.

This is therefore the first Chicago material here that is not UNVERIFIED. The press and
official rows are HIGH; the two threads stay UNVERIFIED and are kept because they carry
what the press does not (the NLMB affiliation, that Alamo was an OG, the Lil Herb lyric).

Two disagreements are recorded rather than resolved: RedEye gives Glinsey's age as 54
where the press, gunmemorial and the threads all say 53, and the 2025 thread's own author
says gas station where the press says liquor store. The shooter attribution is unchanged
and still research-sourced: no press account of this shooting names anyone, and while the
police case carries an arrest, no source held here says who was arrested. KTS Von and KTS
Dre keep their roles with `acquitted=False`, the documented baseline for a role attributed
by research rather than tested in court, and now carry notes saying exactly that.

Idempotent: sources are found by URL, the merge is a no-op once the second incident is
gone, and a photo whose caption is already attached is skipped.
"""

import os
import subprocess
import sys

from wikiapi import CHICAGO, Api, q

IMAGES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images")
ACCESSED = "2026-08-22"

# The two rows the corpus produced. SURVIVOR is Alamo's and already carries both KTS
# participants, so it keeps the most and is the one that stays.
SURVIVOR = "329465b9-10cd-40da-ba41-21326782b4d8"
DOOMED = "e80370c7-c681-438f-8853-7ec1c0a4493d"

ALAMO = "99a01654-e59b-46e4-970c-e9bb82374800"
ROC = "617fd8f3-5a49-493d-ba72-99aa755623b7"

LAT, LNG = 41.751767411, -87.563417608
LOCATION = "2500 block E. 79th St, South Shore, Chicago (liquor store at 79th & Marquette Ave)"

SOURCES = [
    {
        "key": "abc7",
        "url": "https://abc7chicago.com/archive/8550420/",
        "title": (
            "7 shot, Jamal Harris, Gregory Glinsey dead, in Southeast Side drive-by "
            "near liquor store on East 79th Street"
        ),
        "publication": "ABC7 Chicago",
        "published_at": {"year": 2012, "month": 2, "day": 20, "precision": "YMD"},
        "reliability": "HIGH",
        "notes": (
            "A gunman in a beige vehicle opened fire outside the liquor store, hitting "
            "seven people. Harris, 19, was shot in the chest and found inside the store, "
            "having run in after being hit; Glinsey, 53, was shot in the chest outside. "
            "Five teenagers were wounded, one 14-year-old needing surgery at Comer "
            "Children's Hospital. No shooter named; police were still searching."
        ),
    },
    {
        "key": "nbc",
        "url": "https://www.nbcchicago.com/news/local/2-dead-5-wounded-in-shooting/1949848/",
        "title": "2 Dead, 5 Injured in Shooting at Liquor Store",
        "publication": "NBC Chicago",
        "published_at": {"year": 2012, "month": 2, "precision": "YM"},
        "reliability": "HIGH",
        "notes": (
            "Second press account of the same shooting. Puts Glinsey at 53 and describes "
            "him as an innocent victim who had celebrated his mother's 80th birthday the "
            "day before."
        ),
    },
    {
        "key": "cpd",
        "url": "https://data.cityofchicago.org/Public-Safety/Crimes-2001-to-Present/ijzp-q8t2",
        "title": "Chicago Police recorded crime, case HV164849",
        "publication": "City of Chicago Data Portal",
        "published_at": {"year": 2012, "precision": "Y", "approx": True},
        "reliability": "HIGH",
        "notes": (
            "Two HOMICIDE / FIRST DEGREE MURDER records share case number HV164849, both "
            "stamped 2012-02-19T18:40 at 025XX E 79TH ST, community area 43 (South Shore), "
            "location STREET, arrest true, at 41.751767411 / -87.563417608. The dataset "
            "carries no victim names, so it fixes the date, the place and the fact that "
            "two people died together, not who they were."
        ),
    },
    {
        "key": "redeye",
        "url": "http://homicides.redeyechicago.com/date/2012/2/",
        "title": "Tracking homicides in Chicago - February 2012",
        "publication": "RedEye Chicago",
        "published_at": {"year": 2012, "month": 2, "precision": "YM"},
        "reliability": "HIGH",
        "archive_url": (
            "https://web.archive.org/web/20120227224302/"
            "http://homicides.redeyechicago.com/date/2012/2/"
        ),
        "notes": (
            "Snapshot taken 27 February 2012, eight days after the shooting. Lists "
            "'Jamal Harris, 19' and 'Gregory Glinsey, 54' on 2/19/12 at 2500 E. 79th St., "
            "South Shore, gunshot. The site is dead; only the archived copy is readable. "
            "Its age of 54 for Glinsey is the only source that disagrees with 53."
        ),
    },
    {
        "key": "gunmemorial",
        "url": "https://gunmemorial.org/2012/02/19/jamal-roc-harris",
        "title": 'Jamal "Roc" Harris, age 19',
        "publication": "Gun Memorial",
        "published_at": {"year": 2012, "month": 2, "day": 19, "precision": "YMD"},
        "reliability": "MEDIUM",
        "notes": (
            'Carries both street names in public - Jamal "Roc" Harris and Gregory '
            '"Alamo" Glinsey, 53 - which is why neither nickname rests on the forum '
            "threads alone. Rated MEDIUM rather than HIGH because some fields, including "
            "the NLMB affiliation recorded for Harris, are contributed by site users."
        ),
    },
    {
        "key": "reddit2021",
        "url": "https://www.reddit.com/r/Chiraqology/comments/mco6tr/nlmb_alamo_killed_in_2012_with_nlmb_roc/",
        "title": "Nlmb Alamo killed in 2012 with Nlmb Roc",
        "publication": "Reddit - r/Chiraqology",
        "published_at": {"year": 2021, "month": 3, "day": 25, "precision": "YMD"},
        "reliability": "UNVERIFIED",
        "notes": (
            "Photo post by u/kushkoopa. u/kushkoopa gives Alamo's age as 53 and calls him "
            "a No Limit OG; u/LilTrouble060 describes three or four mass shootings on NLMB "
            "between 2011 and 2013 and says Wet, Herb and three others were also hit; "
            "u/Lilbig6029 says KTS Von killed both Roc and Alamo, prompted by a lyric "
            "rather than by knowledge. Whether G Herbo was wounded in this particular "
            "shooting is argued in the thread and left unresolved - the press names no "
            "wounded, all five being minors."
        ),
    },
    {
        "key": "reddit2025",
        "url": "https://www.reddit.com/r/Chiraqology/comments/1it586g/it_has_been_13_years_since_the_murders_of_nlmb/",
        "title": "It has been 13 years since the murders of NLMB Alamo & NLMB Roc",
        "publication": "Reddit - r/Chiraqology",
        "published_at": {"year": 2025, "month": 2, "day": 19, "precision": "YMD"},
        "reliability": "UNVERIFIED",
        "notes": (
            "Anniversary post by u/Substantial-Gear6393, whose date is what pointed at "
            "19 February. It says the two were killed outside a gas station and that Roc "
            "tried to escape inside the store; the press says liquor store, and confirms "
            "Roc was found inside. u/madayuhsuck says Alamo was not an intended target, "
            "just an old head standing outside, which matches police calling him an "
            "innocent victim. The same commenter's account of Fazoland's death and the "
            "origin of NLMB is disputed inside the thread and is not carried here."
        ),
    },
]

NARRATIVE = (
    "Drive-by shooting outside a liquor store in the 2500 block of East 79th Street, "
    "South Shore, on the evening of Sunday 19 February 2012. A gunman in a beige vehicle "
    "opened fire on a group outside the store and hit seven people. Jamal “Roc” "
    "Harris (19, NLMB) was shot in the chest and ran into the store, where he was found; "
    "Gregory “Alamo” Glinsey (53) was shot in the chest outside. Both died at "
    "the scene. Five teenagers aged 13 to 16 were wounded, one of whom needed surgery. "
    "Police described Glinsey as an innocent victim rather than an intended target. "
    "Chicago Police recorded both deaths under case HV164849 at 18:40 and the case "
    "carries an arrest, but no source held here says who was arrested, and no press "
    "account of the shooting names a shooter."
)

VON_NOTE = (
    "Attributed by the privedatabase corpus, which lists both Roc (NLMB) and Alamo (NLMB) "
    "among KTS Von's bodies. No press account of this shooting names a shooter. Chicago "
    "Police case HV164849 carries an arrest, but no source held here identifies who was "
    "arrested, so this remains a research attribution and was never tested in court."
)
DRE_NOTE = (
    "Attributed by the privedatabase corpus, which lists Alamo (NLMB) among KTS Dre's "
    "assists. He is not named in any press or official record of this shooting."
)
ALAMO_NOTE = (
    "Gregory Glinsey, 53. Shot in the chest outside the store and pronounced dead at the "
    "scene. Police described him as an innocent victim, not an intended target."
)
ROC_NOTE = (
    "Jamal Harris, 19. Shot in the chest, ran into the store and was found inside, where he died."
)

ALAMO_BIO = (
    "Gregory Glinsey, named in public as Gregory “Alamo” Glinsey. Killed on "
    "Sunday 19 February 2012 outside a liquor store in the 2500 block of East 79th Street "
    "in South Shore, when a gunman in a beige vehicle opened fire on the group standing "
    "outside and shot seven people. He was 53, was hit in the chest and died at the scene. "
    "Chicago police described him as an innocent victim rather than an intended target, "
    "and r/Chiraqology says the same thing in its own words: an old head standing outside "
    "the store. He is remembered there as a No Limit OG who taught the younger generation. "
    "Jamal “Roc” Harris, 19, was killed in the same burst and five teenagers "
    "aged 13 to 16 were wounded. The privedatabase corpus lists him among the bodies "
    "attributed to KTS Von, with KTS Dre assisting; no press or official source names a "
    "shooter, though Chicago Police case HV164849 carries an arrest. His age is given as "
    "53 by the press, by gunmemorial.org and by the forum threads, and as 54 by the "
    "RedEye homicide tracker."
)

ROC_BIO = (
    "Jamal Harris, named in public as Jamal “Roc” Harris. NLMB. Killed at 19 on "
    "Sunday 19 February 2012, in the drive-by outside a liquor store in the 2500 block of "
    "East 79th Street in South Shore that also killed Gregory “Alamo” Glinsey, "
    "a 53-year-old bystander, and wounded five teenagers aged 13 to 16. Shot in the chest, "
    "he ran into the store and was found inside. The privedatabase corpus lists him among "
    "the bodies attributed to KTS Von; no press or official source names a shooter, though "
    "Chicago Police case HV164849 carries an arrest. Lil Herb remembered him in a lyric "
    "quoted on r/Chiraqology: “Roc was wild as hell, couldn’t ever stay out of "
    "jail, died in the field, he was just born L’s.”"
)

PHOTOS = [
    (
        ALAMO,
        "alamo-glinsey-chiraqology.jpg",
        'Gregory "Alamo" Glinsey, from the r/Chiraqology post marking 13 years since the murders',
    ),
    (
        ROC,
        "roc-harris-chiraqology.jpg",
        'Jamal "Roc" Harris, from the r/Chiraqology post marking 13 years since the murders',
    ),
]


def ensure_sources(api):
    """Create every source that is not already present, and return {key: id}."""
    ids = {}
    for spec in SOURCES:
        spec = dict(spec)
        key = spec.pop("key")
        rows = q(f"SELECT id FROM source WHERE url = '{spec['url']}'")
        if rows:
            ids[key] = rows[0]["id"]
            print(f"source exists   {key:12s} {ids[key]}")
            continue
        made = api.call(
            "POST", "sources/", {"universe_id": CHICAGO, "accessed_at": ACCESSED, **spec}
        )
        if "_error" in made:
            sys.exit(f"source create failed for {key}: {made}")
        ids[key] = made["id"]
        print(f"source created  {key:12s} {ids[key]}")
    return ids


def kts_participants():
    """Return the KTS Von and KTS Dre member ids already on the surviving incident."""
    rows = q(
        "SELECT m.nickname, ip.member_id FROM incident_participant ip "
        "JOIN member m ON m.id = ip.member_id "
        f"WHERE ip.incident_id = '{SURVIVOR}' AND ip.role IN ('SHOOTER', 'ASSISTED')"
    )
    by_role = {r["nickname"]: r["member_id"] for r in rows}
    if "Von" not in by_role:
        sys.exit(f"expected KTS Von on {SURVIVOR}, found {by_role}")
    return by_role["Von"], by_role.get("Dre")


def main():
    """Merge the two incidents, then name, date, source and illustrate both victims."""
    api = Api()

    mode = api.call("GET", "admin/db-mode")
    if mode.get("mode") != "prod":
        sys.exit(f"backend is in {mode.get('mode')!r} mode, refusing to write")

    src = ensure_sources(api)
    all_sources = [src[k] for k in ("abc7", "nbc", "cpd", "redeye", "gunmemorial")]
    all_sources += [src["reddit2021"], src["reddit2025"]]

    von_id, dre_id = kts_participants()

    # Drop Roc's duplicate incident first. death_incident_id is ON DELETE SET NULL, so
    # this releases Roc; the sync on the PATCH below then links him to the survivor.
    # Done in this order because _sync_killed_participants never moves a member that
    # already points at a different incident.
    if q(f"SELECT id FROM incident WHERE id = '{DOOMED}'"):
        gone = api.call("DELETE", f"incidents/{DOOMED}?universe_id={CHICAGO}")
        if isinstance(gone, dict) and "_error" in gone:
            sys.exit(f"could not delete the duplicate incident: {gone}")
        print(f"incident merged {DOOMED} deleted into {SURVIVOR}")
    else:
        print(f"incident merged {DOOMED} already gone")

    participants = [
        {
            "member_id": von_id,
            "role": "SHOOTER",
            "outcome": "UNKNOWN",
            "acquitted": False,
            "notes": VON_NOTE,
        },
        {
            "member_id": ALAMO,
            "role": "VICTIM",
            "outcome": "KILLED",
            "acquitted": False,
            "notes": ALAMO_NOTE,
        },
        {
            "member_id": ROC,
            "role": "VICTIM",
            "outcome": "KILLED",
            "acquitted": False,
            "notes": ROC_NOTE,
        },
    ]
    if dre_id:
        participants.insert(
            1,
            {
                "member_id": dre_id,
                "role": "ASSISTED",
                "outcome": "UNKNOWN",
                "acquitted": False,
                "notes": DRE_NOTE,
            },
        )

    inc = api.call(
        "PATCH",
        f"incidents/{SURVIVOR}?universe_id={CHICAGO}",
        {
            "type": "MURDER",
            "date": {"year": 2012, "month": 2, "day": 19, "precision": "YMD"},
            "location_text": LOCATION,
            "lat": LAT,
            "lng": LNG,
            "narrative": NARRATIVE,
            "verified": True,
            "participants": participants,
            "source_ids": all_sources,
        },
    )
    if "_error" in inc:
        sys.exit(f"incident update failed: {inc}")
    print(f"incident dated  {inc['date']} at {inc['location_text']}")

    for member_id, legal, bio, who in (
        (ALAMO, "Gregory Glinsey", ALAMO_BIO, "Alamo"),
        (ROC, "Jamal Harris", ROC_BIO, "Roc"),
    ):
        cur = api.call("GET", f"members/{member_id}?universe_id={CHICAGO}")
        merged = sorted(set(cur.get("source_ids", [])) | set(all_sources))
        upd = api.call(
            "PATCH",
            f"members/{member_id}?universe_id={CHICAGO}",
            {
                "legal_name": legal,
                "status": "DEAD",
                "date_of_death": {"year": 2012, "month": 2, "day": 19, "precision": "YMD"},
                "biography": bio,
                "source_ids": merged,
            },
        )
        if "_error" in upd:
            sys.exit(f"{who} update failed: {upd}")
        print(f"member updated  {who:6s} {upd['legal_name']} d. {upd['date_of_death']}")

    for member_id, filename, caption in PHOTOS:
        path = os.path.join(IMAGES, filename)
        if not os.path.exists(path):
            sys.exit(f"missing photo: {path}")
        if q(f"SELECT id FROM media WHERE member_id = '{member_id}' AND caption = '{caption}'"):
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
                f"file=@{path};type=image/jpeg",
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
        print(f"photo {filename}: {r.stdout[:160]}{r.stderr[:160]}")


if __name__ == "__main__":
    main()
