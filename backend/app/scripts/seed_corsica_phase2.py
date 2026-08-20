"""Seed phase 2 of the Corsica universe: the war that killed the fathers.

Phase 1 (`seed_corsica.py`) covers the Ziglioli case and the 1981-83 war that
made the Brise de Mer. This is the war that unmade it: between April 2008 and
November 2009 the founding generation killed each other off, and the book calls
the period "la mort des pères".

Dates and ages come from the chronology in Lazard & Galland, Vendetta, which is
the most reliable single list of them. Where it says "mort" rather than
"assassinat" that distinction is deliberate and is preserved here: Francis
Mariani died in an explosion that was never established as an attack.

**Clan sets are still not created.** `seed-scope.md` pencilled them in for this
phase, but no source to hand says reliably which man belonged to which clan, and
inventing that structure would be worse than leaving the members in the founding
set where the sources put them. Deferred until it can be sourced.

Idempotent, same as phase 1. Run from backend/:
  .venv/bin/python -m app.scripts.seed_corsica_phase2          # dry run
  .venv/bin/python -m app.scripts.seed_corsica_phase2 --apply
"""

import argparse
import asyncio
import sys
import uuid

from sqlalchemy import select, text

from app.core.database import _session_factories
from app.core.enums import (
    DatePrecision,
    IncidentType,
    MemberStatus,
    ParticipantOutcome,
    ParticipantRole,
    SourceReliability,
)
from app.core.fuzzy_date import FuzzyDate
from app.crud.incident import create_incident
from app.crud.member import create_member, update_member
from app.crud.municipality import create_municipality
from app.crud.source import create_source
from app.models import GangSet, Incident, Member, Municipality, Source
from app.schemas.incident import IncidentCreate, ParticipantCreate
from app.schemas.member import MemberCreate, MemberSetAffiliationIn, MemberUpdate
from app.schemas.municipality import MunicipalityCreate
from app.schemas.source import SourceCreate

UNIVERSE_SLUG = "corsica"
SET_NAME = "Brise de Mer"
GANG_NAME = "Brise de Mer"


def ymd(y, m, d):
    return FuzzyDate(year=y, month=m, day=d, precision=DatePrecision.YMD)


def yr(y, approx=False):
    return FuzzyDate(year=y, precision=DatePrecision.Y, approx=approx)


MUNICIPALITIES = ["Porto-Vecchio", "Casevecchie", "Ponte Leccia", "Lucciana", "Sartène"]

MEMBERS = {
    "Richard Casanova": dict(
        status=MemberStatus.DEAD,
        dob=yr(1960, approx=True),
        date_of_death=ymd(2008, 4, 23),
        aliases=["le Menteur", "le Singe menteur"],
        from_date=yr(1980, approx=True),
        biography=(
            "Known as 'le Singe menteur', or simply 'le Menteur'. Drifted between the "
            "nationalists, where he was said to be one of the FLNC's bomb-makers, and "
            "the Brise de Mer. Picked up at Nice in 1980 carrying a .357 Magnum and "
            "suspected of planning to rob a jeweller's, which he denied; he told "
            "investigators he was armed out of a fascination with the autonomist "
            "movement and family atavism, and was released after eight months.\n\n"
            "Arrested at Lucciana on 3 March 2006 after fifteen years on the run. "
            "Assassinated at Porto-Vecchio on 23 April 2008, aged 48. His break with "
            "the group in the early 2000s is generally taken as the start of the war "
            "that destroyed the founding generation, and his killing opens the sequence "
            "the book calls 'la mort des pères'."
        ),
    ),
    "Francis Mariani": dict(
        status=MemberStatus.DEAD,
        dob=yr(1949, approx=True),
        date_of_death=ymd(2009, 1, 12),
        from_date=yr(1978, approx=True),
        biography=(
            "One of the founders of the Brise de Mer, and the figure around whom its "
            "legend grew. Escaped the Sainte-Claire prison in Bastia with Charles Pieri "
            "on 22 January 1984. Arrested with Pierre-Marie Santucci and Maurice Costa "
            "at Sartène on 5 July 2000, and walked out of Borgo prison with both of "
            "them on 31 May 2001 on a forged fax.\n\n"
            "On 13 March 2008, at the trial for the assassination of the nationalist "
            "Nicolas Montigny, he was sentenced to seven years and went on the run "
            "rather than serve it. He died on 12 January 2009, aged 59, in the "
            "explosion of an agricultural shed at Casevecchie. The book's chronology "
            "records this as a death and not an assassination, unlike every other entry "
            "around it, and that distinction is deliberate: the explosion was never "
            "established as an attack on him.\n\n"
            "Father of Jacques Mariani."
        ),
    ),
    "François Guazzelli": dict(
        status=MemberStatus.DEAD,
        dob=yr(1954, approx=True),
        date_of_death=ymd(2009, 11, 15),
        aliases=["Francis"],
        from_date=yr(1978, approx=True),
        biography=(
            "Known as Francis. Good-looking, with piercing blue eyes, and one of the "
            "most assiduous of the young men at the bar on the old port. One of three "
            "brothers in the group with Paul-Louis and Jean-Angelo, called Angelo; "
            "their father gave his occupation as farmer and their mother was a "
            "schoolteacher. A fourth brother took an entirely different path.\n\n"
            "With Sylvie Cappuri he had two sons who became figures in the next "
            "generation: Richard, born 2 December 1989, and Christophe, born 3 July "
            "1991. He carried Francis Mariani's coffin in January 2009 alongside "
            "Pierre-Marie Santucci; both pallbearers were dead within the year.\n\n"
            "Assassinated on 15 November 2009, aged 55, on the road up to the village "
            "of La Porta. The investigation produced surveillance and enquiries but not "
            "a single interview under caution."
        ),
    ),
    "Maurice Costa": dict(
        status=MemberStatus.DEAD,
        date_of_death=ymd(2012, 8, 7),
        from_date=yr(1985, approx=True),
        biography=(
            "Arrested at Sartène on 5 July 2000 with Francis Mariani and Pierre-Marie "
            "Santucci, and one of the three men who walked out of Borgo prison in "
            "sandals on 31 May 2001 on the strength of a forged fax purporting to come "
            "from the Ajaccio tribunal.\n\n"
            "Assassinated at Ponte Leccia on 7 August 2012, the last of the older "
            "generation to fall in the succession war."
        ),
    ),
    "Jacques Mariani": dict(
        status=MemberStatus.LOCKED,
        dob=ymd(1965, 11, 11),
        from_date=yr(1990, approx=True),
        biography=(
            "Born in Bastia on 11 November 1965, son of Francis Mariani. On 13 March "
            "2008 he was sentenced to fifteen years for the assassination of the "
            "nationalist militant Nicolas Montigny; his father, sentenced to seven "
            "years in the same case, went on the run instead and was dead within ten "
            "months.\n\n"
            "Served the end of that sentence at Moulins-Yzeure and was granted leave in "
            "2016, then released under an electronic tag. Re-arrested at La Baule on 18 "
            "December 2017. A central figure of the generation the book calls 'la "
            "guerre des fils'."
        ),
    ),
}

FAMILY = [("Francis Mariani", "son", "Jacques Mariani")]

INCIDENTS = [
    (
        "casanova-2008",
        IncidentType.MURDER,
        ymd(2008, 4, 23),
        "Porto-Vecchio",
        "Porto-Vecchio, Corse-du-Sud",
        "Richard Casanova was shot dead at Porto-Vecchio on 23 April 2008, aged 48, "
        "two years after being taken at Lucciana at the end of a fifteen-year cavale. "
        "His break with the Brise de Mer in the early 2000s had already set the group "
        "against itself; his killing began the run of deaths that removed almost the "
        "whole founding generation within two years.",
        [("Richard Casanova", ParticipantRole.VICTIM, ParticipantOutcome.KILLED)],
    ),
    (
        "mariani-2009",
        IncidentType.BOMBING,
        ymd(2009, 1, 12),
        "Casevecchie",
        "An agricultural shed, Casevecchie, Haute-Corse",
        "Francis Mariani died on 12 January 2009, aged 59, in the explosion of an "
        "agricultural shed at Casevecchie, while on the run from the seven-year "
        "sentence handed down in the Montigny case ten months earlier.\n\n"
        "Recorded here as a death rather than an assassination, following the book's "
        "own chronology, which uses 'mort' for this entry and 'assassinat' for every "
        "other killing around it. The explosion was never established as an attack, and "
        "no participant is recorded as having caused it.",
        [("Francis Mariani", ParticipantRole.VICTIM, ParticipantOutcome.KILLED)],
    ),
    (
        "guazzelli-2009",
        IncidentType.MURDER,
        ymd(2009, 11, 15),
        "La Porta",
        "The road up to La Porta, Haute-Corse",
        "Francis Guazzelli was shot dead on 15 November 2009, aged 55, on the road "
        "leading up to the village of La Porta, on his way to go hunting. He was the "
        "third of the founders to die inside twelve months, after Francis Mariani in "
        "January and Pierre-Marie Santucci in February. The enquiry ran to surveillance "
        "and investigative acts but never produced an interview under caution.",
        [("François Guazzelli", ParticipantRole.VICTIM, ParticipantOutcome.KILLED)],
    ),
    (
        "costa-2012",
        IncidentType.MURDER,
        ymd(2012, 8, 7),
        "Ponte Leccia",
        "Ponte Leccia, Haute-Corse",
        "Maurice Costa was assassinated at Ponte Leccia on 7 August 2012. One of the "
        "three men freed from Borgo by the forged fax in 2001, he was the last of the "
        "older generation to be killed in the succession war.",
        [("Maurice Costa", ParticipantRole.VICTIM, ParticipantOutcome.KILLED)],
    ),
]

SOURCES = [
    (
        "Maurice Costa, figure présumée du grand banditisme corse, a été assassiné",
        "https://www.france24.com/fr/20120807-maurice-costa-assassinat-corse-dirigeant"
        "-presume-grand-banditisme-costa-brise-mer-ponte-leccia",
        "France 24",
        ymd(2012, 8, 7),
        SourceReliability.HIGH,
        "Consulted 2026-08-20.",
    ),
    (
        "Francis Guazzelli, considéré comme un pilier du gang de la Brise de mer, a été tué",
        "https://www.franceinfo.fr/france/francis-guazzelli-considere-comme-un-pilier-du-gang"
        "-de-la-brise-de-mer-a-ete-tue-de-plusieurs-balles-dimanche-matin_232917.html",
        "franceinfo",
        yr(2013),
        SourceReliability.HIGH,
        "Consulted 2026-08-20. Carries the portrait of Guazzelli used on his member page, "
        "captioned 'Francis Guazzelli (F2)'.",
    ),
    (
        "Gang de la Brise de mer : aux origines de la haine",
        "https://www.leparisien.fr/faits-divers/gang-de-la-brise-de-mer-aux-origines-de-la-haine"
        "-06-05-2024-SRFFH7OJ7JB37PQJ47D5MFLMNU.php",
        "Le Parisien",
        ymd(2024, 5, 6),
        SourceReliability.HIGH,
        "Consulted 2026-08-20. Its lead montage is the source of the Francis Mariani "
        "portrait, captioned 'Francis Mariani (à droite, en bas) et Francis Guazzelli "
        "(au-dessus)'. Paywalled beyond the opening.",
    ),
]


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    dry = not args.apply

    created: list[str] = []
    skipped: list[str] = []

    async with _session_factories["prod"]() as s:
        row = (
            await s.execute(
                text("SELECT id FROM universe WHERE slug = :slug"), {"slug": UNIVERSE_SLUG}
            )
        ).first()
        if row is None:
            print(f"Universe '{UNIVERSE_SLUG}' not found", file=sys.stderr)
            return 1
        uni: uuid.UUID = row[0]

        actor_row = (
            await s.execute(
                text(
                    "SELECT id, email FROM users WHERE global_role = 'ADMIN' "
                    "ORDER BY created_at LIMIT 1"
                )
            )
        ).first()
        actor: uuid.UUID = actor_row[0]
        print(f"universe={uni}  actor={actor_row[1]}  mode={'DRY RUN' if dry else 'APPLY'}\n")

        async def existing(model, **where):
            stmt = select(model).where(model.universe_id == uni)
            for k, v in where.items():
                stmt = stmt.where(getattr(model, k) == v)
            return (await s.execute(stmt)).scalars().first()

        gang_row = (
            await s.execute(
                text("SELECT id FROM gang WHERE universe_id = :u AND name = :n"),
                {"u": uni, "n": GANG_NAME},
            )
        ).first()
        brise_set = await existing(GangSet, name=SET_NAME)
        if gang_row is None or brise_set is None:
            print("Phase 1 must be seeded first (gang/set missing)", file=sys.stderr)
            return 1
        gang_id: uuid.UUID = gang_row[0]

        muni: dict[str, uuid.UUID] = {
            m.name: m.id
            for m in (
                await s.execute(select(Municipality).where(Municipality.universe_id == uni))
            ).scalars()
        }
        for name in MUNICIPALITIES:
            if name in muni:
                skipped.append(f"municipality {name}")
                continue
            created.append(f"municipality {name}")
            if dry:
                muni[name] = uuid.uuid4()
                continue
            obj = await create_municipality(
                s, MunicipalityCreate(universe_id=uni, name=name), actor
            )
            muni[name] = obj.id

        mem: dict[str, uuid.UUID] = {}
        for legal_name, d in MEMBERS.items():
            found = await existing(Member, legal_name=legal_name)
            if found:
                mem[legal_name] = found.id
                skipped.append(f"member {legal_name}")
                continue
            created.append(f"member {legal_name}")
            if dry:
                mem[legal_name] = uuid.uuid4()
                continue
            obj = await create_member(
                s,
                MemberCreate(
                    universe_id=uni,
                    legal_name=legal_name,
                    aliases=d.get("aliases"),
                    biography=d.get("biography", ""),
                    status=d.get("status", MemberStatus.UNKNOWN),
                    dob=d.get("dob"),
                    date_of_death=d.get("date_of_death"),
                    gang_id=gang_id,
                    affiliations=[
                        MemberSetAffiliationIn(
                            set_id=brise_set.id, is_primary=True, from_date=d.get("from_date")
                        )
                    ],
                ),
                actor,
            )
            mem[legal_name] = obj.id

        # Family after every id exists: `family` holds member UUIDs.
        for who, rel, other in FAMILY:
            if who not in mem or other not in mem:
                continue
            current = await existing(Member, legal_name=who)
            fam = dict(current.family or {}) if current else {}
            ids = set(fam.get(rel) or [])
            if str(mem[other]) in ids:
                skipped.append(f"family {who} {rel} {other}")
                continue
            created.append(f"family {who} {rel} {other}")
            if dry:
                continue
            ids.add(str(mem[other]))
            fam[rel] = sorted(ids)
            await update_member(s, mem[who], uni, MemberUpdate(family=fam))

        for title, url, pub, published, rating, notes in SOURCES:
            if await existing(Source, title=title):
                skipped.append(f"source {title[:40]}")
                continue
            created.append(f"source {title[:40]}")
            if dry:
                continue
            await create_source(
                s,
                SourceCreate(
                    universe_id=uni,
                    url=url,
                    title=title,
                    publication=pub,
                    published_at=published,
                    reliability=rating,
                    notes=notes,
                ),
                actor,
            )

        for key, itype, date, muni_name, location, narrative, participants in INCIDENTS:
            sortable = date.to_sortable_date() if date else None
            if await existing(Incident, type=itype, sortable_date=sortable):
                skipped.append(f"incident {key}")
                continue
            created.append(f"incident {key}")
            if dry:
                continue
            await create_incident(
                s,
                IncidentCreate(
                    universe_id=uni,
                    type=itype,
                    date=date,
                    municipality_id=muni.get(muni_name),
                    location_text=location,
                    narrative=narrative,
                    participants=[
                        ParticipantCreate(member_id=mem[n], role=r, outcome=o)
                        for n, r, o in participants
                        if n in mem
                    ],
                ),
                actor,
            )

    print(f"created ({len(created)}):")
    for c in created:
        print(f"  + {c}")
    if skipped:
        print(f"\nalready present ({len(skipped)}):")
        for k in skipped:
            print(f"  = {k}")
    if dry:
        print("\nDRY RUN, nothing written. Re-run with --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
