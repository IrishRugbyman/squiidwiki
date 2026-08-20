"""The robberies the Brise de Mer was actually built on, and Casanova's part in them.

Every phase so far recorded how these men died. None recorded what they did for
a living. The gang's three signature jobs sit in Vendetta's chronology and had
no home in the schema until `ROBBERY` was added to IncidentType in migration
5eeb3fbbbd24.

That gap fell hardest on Richard Casanova, who the book's index describes as
"cerveau présumé du casse de l'UBS à Genève en 1990" and whose page carried no
trace of it. His biography is rewritten here to add the heist, along with the
two relationships the index gives and the earlier phases missed: spiritual son
of Michel Tomi, and brother-in-law of Jean-Luc Germani.

Idempotent. Run from backend/:
  .venv/bin/python -m app.scripts.seed_corsica_robberies          # dry run
  .venv/bin/python -m app.scripts.seed_corsica_robberies --apply
"""

import argparse
import asyncio
import uuid

from sqlalchemy import select, text

from app.core.database import _session_factories
from app.core.enums import DatePrecision, IncidentType, ParticipantOutcome, ParticipantRole
from app.core.fuzzy_date import FuzzyDate
from app.crud.incident import create_incident
from app.crud.member import update_member
from app.models import Incident, Member, Municipality
from app.schemas.incident import IncidentCreate, ParticipantCreate
from app.schemas.member import MemberUpdate


def ymd(y, m, d):
    return FuzzyDate(year=y, month=m, day=d, precision=DatePrecision.YMD)


CASANOVA_BIO = (
    "Known as 'le Singe menteur', or simply 'le Menteur'. Founder member of the Brise "
    "de Mer, brother-in-law of Jean-Luc Germani through Germani's sister Sandra, and "
    "spiritual son of Michel Tomi, the godfather of gaming in Africa. Godfather too, in "
    "the ordinary sense, of Francis Guazzelli's elder son Richard, who carries his name."
    "\n\n"
    "Presumed mastermind of the robbery of the Union des Banques Suisses in Geneva on 25 "
    "March 1990, in which 125 million francs, some 19 million euros, were taken. It is "
    "the largest job in the gang's history and the one he is best known for.\n\n"
    "He drifted between the nationalists, where he was said to be one of the FLNC's "
    "bomb-makers, and the Brise de Mer. Picked up at Nice in 1980 carrying a .357 Magnum "
    "and suspected of planning to rob a jeweller's, which he denied; he told "
    "investigators he was armed out of a fascination with the autonomist movement and "
    "family atavism, and was released after eight months.\n\n"
    "By the 2000s he was doing business on his own account, which Francis Mariani "
    "watched with mistrust, and Mariani came to suspect him of being behind the 2001 "
    "attempt on his life. Arrested at Lucciana on 3 March 2006 after fifteen years on "
    "the run, and freed on bail that November, the two hundred thousand euros paid by a "
    "handful of friends. Assassinated at Porto-Vecchio on 23 April 2008, aged 48. His "
    "break with the group is generally taken as the start of the war that destroyed the "
    "founding generation, and his killing opens the sequence the book calls 'la mort des "
    "pères'."
)

# (key, date, municipality or None, location_text, narrative, participants)
ROBBERIES = [
    (
        "ubs-1990",
        ymd(1990, 3, 25),
        None,
        "Union des Banques Suisses, Geneva, Switzerland",
        "On 25 March 1990 the Union des Banques Suisses in Geneva was robbed of 125 "
        "million francs, about 19 million euros. It is the largest single job in the "
        "Brise de Mer's history and the one that turned the gang from a Bastia crew into "
        "a fortune. Richard Casanova is named in the sources as its presumed mastermind."
        "\n\n"
        "Recorded outside Corsica deliberately: the money was made abroad and brought "
        "home, which is most of the point.",
        [
            (
                "Richard Casanova",
                ParticipantRole.SHOOTER,
                ParticipantOutcome.UNHARMED,
                "Presumed mastermind, 'cerveau présumé' in the sources. They credit him "
                "with organising the job, not with being at the counter, and no court "
                "established either.",
            )
        ],
    ),
    (
        "paris-bastia-1991",
        ymd(1991, 7, 17),
        "Lucciana",
        "A Paris-Bastia flight, landing at Bastia-Poretta",
        "On 17 July 1991 close to 6 million francs were taken from the hold of a "
        "Paris-Bastia flight by a robber who had hidden himself in it. No one was hurt "
        "and nobody was charged.",
        [],
    ),
    (
        "poretta-plane-1992",
        ymd(1992, 8, 11),
        "Lucciana",
        "An aircraft on the tarmac, Bastia-Poretta airport",
        "On 11 August 1992 four men arrived by helicopter at Bastia-Poretta, robbed an "
        "aircraft standing on the tarmac of 7 million francs carried in its hold, and "
        "left the same way. The style is the gang at its most confident: daylight, an "
        "airport, and an exit nobody could follow.",
        [],
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
        uni = (await s.execute(text("SELECT id FROM universe WHERE slug = 'corsica'"))).first()[0]
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

        muni = {
            m.name: m.id
            for m in (
                await s.execute(select(Municipality).where(Municipality.universe_id == uni))
            ).scalars()
        }
        members = {
            m.legal_name: m.id
            for m in (await s.execute(select(Member).where(Member.universe_id == uni))).scalars()
        }

        casanova = (
            (
                await s.execute(
                    select(Member).where(
                        Member.universe_id == uni, Member.legal_name == "Richard Casanova"
                    )
                )
            )
            .scalars()
            .first()
        )
        if casanova is None:
            print("Richard Casanova not seeded; run phase 2 first")
            return 1
        if casanova.biography.strip() == CASANOVA_BIO.strip():
            skipped.append("Richard Casanova biography")
        else:
            created.append("Richard Casanova biography (UBS heist, Tomi, Germani, godfather)")
            if not dry:
                await update_member(s, casanova.id, uni, MemberUpdate(biography=CASANOVA_BIO))

        for key, date, muni_name, location, narrative, participants in ROBBERIES:
            sortable = date.to_sortable_date()
            found = (
                (
                    await s.execute(
                        select(Incident).where(
                            Incident.universe_id == uni,
                            Incident.type == IncidentType.ROBBERY,
                            Incident.sortable_date == sortable,
                        )
                    )
                )
                .scalars()
                .first()
            )
            if found:
                skipped.append(f"incident {key}")
                continue
            created.append(f"incident {key}")
            if dry:
                continue
            await create_incident(
                s,
                IncidentCreate(
                    universe_id=uni,
                    type=IncidentType.ROBBERY,
                    date=date,
                    municipality_id=muni.get(muni_name) if muni_name else None,
                    location_text=location,
                    narrative=narrative,
                    participants=[
                        ParticipantCreate(member_id=members[n], role=r, outcome=o, notes=note)
                        for n, r, o, note in participants
                        if n in members
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
