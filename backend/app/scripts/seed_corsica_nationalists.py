"""The nationalist overlay: Armata Corsa, the FLNC, the MPA, and the 2001 killings.

The independence movement is not a sideshow to this story, it is entangled with
it. Vendetta puts it plainly: with the birth of Armata Corsa on 25 June 1999 a
fratricidal war broke out between the independence currents, and that war came
doubled with a confrontation with the milieu, because the nationalist leaders
had adopted the methods of gangsters and lived off the same trades. Slot
machines, racketeering, security contracts. Judicial investigations established
François Santoni's own involvement in extortion.

Three organisations are created as gangs, which is the only top-level container
the schema has. They are armed political movements, not crime clans, and each
description says so.

The Montigny case matters for a second reason: it produced this universe's
**first actual convictions**. Everywhere else in Corsica so far the participant
roles are attributions, or acquittals. Here Jacques Mariani took fifteen years
and his father seven, so the notes say convicted rather than attributed, and
neither carries the acquitted flag.

Also enriches Christophe Andreani, already seeded with the orphans, who turns
out to be the hinge between the two worlds: a nationalist militant since 17 who
ended up shooting for the heirs of the Brise.

Idempotent. Run from backend/:
  .venv/bin/python -m app.scripts.seed_corsica_nationalists          # dry run
  .venv/bin/python -m app.scripts.seed_corsica_nationalists --apply
"""

import argparse
import asyncio
import uuid

from sqlalchemy import select, text

from app.core.database import _session_factories
from app.core.enums import (
    DatePrecision,
    IncidentType,
    MemberStatus,
    ParticipantOutcome,
    ParticipantRole,
    SetRelationshipType,
    SetStatus,
)
from app.core.fuzzy_date import FuzzyDate
from app.crud.gang import create_gang
from app.crud.gang_set import create_gang_set
from app.crud.incident import create_incident
from app.crud.member import create_member, update_member
from app.crud.municipality import create_municipality
from app.models import Gang, GangSet, Incident, Member, Municipality, SetRelationship
from app.schemas.gang import GangCreate
from app.schemas.gang_set import SetCreate
from app.schemas.incident import IncidentCreate, ParticipantCreate
from app.schemas.member import MemberCreate, MemberSetAffiliationIn, MemberUpdate
from app.schemas.municipality import MunicipalityCreate

ARMATA, FLNC, MPA, BRISE = "Armata Corsa", "FLNC", "MPA", "Brise de Mer"


def ymd(y, m, d):
    return FuzzyDate(year=y, month=m, day=d, precision=DatePrecision.YMD)


def ym(y, m):
    return FuzzyDate(year=y, month=m, precision=DatePrecision.YM)


def yr(y, approx=False):
    return FuzzyDate(year=y, precision=DatePrecision.Y, approx=approx)


GANGS = [
    (
        ARMATA,
        None,
        "A clandestine nationalist movement founded on 25 June 1999 by François "
        "Santoni. Not a crime clan: an armed political organisation, recorded here "
        "because it cannot be separated from the rest. Its birth set off a fratricidal "
        "war between the independence currents, and that war came doubled with a "
        "confrontation with the milieu, since by then the nationalist leaders had "
        "adopted the methods of gangsters and lived off the same trades: slot machines, "
        "racketeering, security contracts. Its leader and three of its people were shot "
        "dead between August and September 2001.",
    ),
    (
        FLNC,
        ["Front de libération nationale corse", "FLNC unifié"],
        "The Front de libération nationale corse, the main armed independence "
        "organisation on the island. An armed political movement rather than a crime "
        "group, but the two worlds overlap constantly in this story: Richard Casanova "
        "was said to be one of its bomb-makers, Francis Mariani escaped prison in 1984 "
        "with a man who became one of its most feared leaders, and Christophe Andreani "
        "came to the Brise heirs out of its ranks.",
    ),
    (
        MPA,
        ["Mouvement pour l'autodétermination"],
        "The Mouvement pour l'autodétermination, launched by Alain Orsoni in 1990 after "
        "a split among the nationalist leadership. Its people held the Ajaccio chamber "
        "of commerce, the economic lung of the south, after Charles Pasqua handed them "
        "the purse strings in a political arrangement, which is how a political movement "
        "came to sit on airports, ports, tourism and public contracts.",
    ),
]

MUNICIPALITIES = ["Monacia-d'Aullène", "Moriani-Plage"]

MEMBERS = {
    "François Santoni": dict(
        status=MemberStatus.DEAD,
        dob=yr(1960, approx=True),
        date_of_death=ymd(2001, 8, 17),
        gang=ARMATA,
        set=ARMATA,
        from_date=ymd(1999, 6, 25),
        biography=(
            "Founder and leader of Armata Corsa, which he created on 25 June 1999, and "
            "by then in open conflict with the Brise de Mer. Judicial investigations "
            "established his involvement in extortion, which is the point the book keeps "
            "making about this period: the nationalist leaders had taken up the "
            "gangsters' methods and were living off the same trades.\n\n"
            "When Francis Mariani, Pierre-Marie Santucci and Maurice Costa were arrested "
            "at Sartène on 5 July 2000, investigators could never establish who they had "
            "gone there to kill. Santoni was among the names raised: his village lies "
            "thirty kilometres from Sartène. Mariani denied it and lost his temper, "
            "saying he had no wish to spend the rest of his life in a bulletproof vest."
            "\n\n"
            "Assassinated on 17 August 2001 at Monacia-d'Aullène, cut down by a burst of "
            "submachine-gun fire as he left a wedding in the far south of the island. "
            "Two of his lieutenants were dead four days later and a third within three "
            "weeks."
        ),
    ),
    "Dominique Marcelli": dict(
        status=MemberStatus.DEAD,
        date_of_death=ymd(2001, 8, 21),
        gang=ARMATA,
        set=ARMATA,
        from_date=yr(1999, approx=True),
        biography=(
            "One of François Santoni's lieutenants in Armata Corsa. He shares a surname "
            "with Jean-Christophe Marcelli, killed the same day, but the sources are "
            "explicit that they were not of the same family.\n\n"
            "On the day before their deaths, when Jean-Christophe collected him by car "
            "outside his home, several men got into the vehicle. Watching from the "
            "window, Dominique Marcelli's wife recognised Jacques Mariani. Neither man "
            "was seen alive again. His body was found near Moriani-Plage on 21 August "
            "2001, partially burned and riddled with bullets, beside a completely "
            "gutted car."
        ),
    ),
    "Jean-Christophe Marcelli": dict(
        status=MemberStatus.DEAD,
        date_of_death=ymd(2001, 8, 21),
        gang=ARMATA,
        set=ARMATA,
        from_date=yr(1999, approx=True),
        biography=(
            "One of François Santoni's lieutenants in Armata Corsa, and no relation to "
            "Dominique Marcelli despite the shared name. He was driving when several men "
            "got into the car outside Dominique's home, and both were killed. His "
            "charred body was found in the boot of the burnt-out vehicle near "
            "Moriani-Plage on 21 August 2001.\n\n"
            "Note a discrepancy in the source: the chronology names him "
            "Jean-Christophe, while the narrative calls the man in the boot "
            "Jean-Michel. Recorded under the chronology's name."
        ),
    ),
    "Nicolas Montigny": dict(
        status=MemberStatus.DEAD,
        dob=yr(1974, approx=True),
        date_of_death=ymd(2001, 9, 5),
        gang=ARMATA,
        set=ARMATA,
        from_date=yr(1999, approx=True),
        biography=(
            "An Armata Corsa militant, 27 years old, with a gentle face and round "
            "glasses. He was sitting on the mezzanine of the Cyber Corsica internet cafe "
            "in Bastia on 5 September 2001, downloading music, when gunmen shot him with "
            "three military weapons.\n\n"
            "Witnesses described two killers, one slim and one athletic with short hair, "
            "dressed in dark clothes with scarves pulled up over their noses, who fled "
            "towards a Renault Laguna parked nearby. Strangely, one of them came back "
            "into the cafe.\n\n"
            "His killing is the one that stuck. At the verdict on 13 March 2008 Jacques "
            "Mariani was sentenced to fifteen years and his father Francis to seven; "
            "Francis went on the run rather than serve it and was dead within ten months."
        ),
    ),
    "Dominique Savelli": dict(
        status=MemberStatus.DEAD,
        date_of_death=ym(1999, 8),
        gang=BRISE,
        set=None,
        biography=(
            "A butcher established in the Balagne, and the man the book calls Francis "
            "Mariani's butcher. Known to police for minor common-law matters and, above "
            "all, close to Mariani, who had given him work.\n\n"
            "In August 1999 Armata Corsa claimed his assassination as a preventive "
            "political killing, asserting he had been about to murder one of their "
            "leaders. He was nothing of the sort: not a militant for Corsican "
            "independence at all. His death is one of the clearest illustrations of what "
            "the period had become, a nationalist movement killing a gangster's butcher "
            "and calling it politics. The Brise was widely suspected of avenging him "
            "when the Marcellis were killed two years later."
        ),
    ),
    "Charles Pieri": dict(
        status=MemberStatus.UNKNOWN,
        gang=FLNC,
        set=None,
        biography=(
            "On 22 January 1984 a young Francis Mariani escaped the Sainte-Claire "
            "prison in Bastia, a sixteenth-century convent in the citadel long used as a "
            "penitentiary, using a file for the bars, a rope for the fifteen metres down "
            "to the street and a mirror to signal his accomplices. The unknown "
            "accomplice beside him became, in time, one of the most respected and most "
            "feared leaders of the Front de libération nationale corse: Charles Pieri."
            "\n\n"
            "He appears again years later in an extortion case that also drew in "
            "Jean-Guy Talamoni, later president of the Corsican assembly. A demonstration "
            "in support of Talamoni during that affair produced the first conviction of "
            "a seventeen-year-old Christophe Andreani."
        ),
    ),
    "Alain Orsoni": dict(
        status=MemberStatus.UNKNOWN,
        gang=MPA,
        set=None,
        biography=(
            "Former nationalist leader and founder of the Mouvement pour "
            "l'autodétermination, launched in 1990 after a split among the independence "
            "leadership. His clan held the Ajaccio chamber of commerce, the economic "
            "lung of southern Corsica, from the point at which Charles Pasqua handed "
            "the purse strings to people close to him as part of a political "
            "arrangement.\n\n"
            "Jean-Luc Germani took an interest in the 2004 elections to that chamber and "
            "attended a meeting with Orsoni's associates, including Antoine Nivaggioni, "
            "in the premises of an influential Ajaccio merchant. The gendarmes noted the "
            "purpose was unknown but might relate to threats made in the race for its "
            "presidency.\n\n"
            "Tried at the Aix-en-Provence assizes in spring 2015 over two assassinations "
            "and an attempted one against members of the Petit Bar, and acquitted, as "
            "were all the accused."
        ),
    ),
    "Guy Orsoni": dict(
        status=MemberStatus.LOCKED,
        dob=yr(1986, approx=True),
        gang=MPA,
        set=None,
        biography=(
            "Son of the former nationalist leader Alain Orsoni. Tried with his father at "
            "Aix-en-Provence in spring 2015 over two assassinations and an attempted one "
            "against members of the Petit Bar, and acquitted along with every other "
            "accused, to general surprise. Later sentenced to eight years for criminal "
            "conspiracy to commit two assassinations.\n\n"
            "In prison he became the man Jean-Luc Germani talked to. Germani's cell was "
            "never empty and he seems to have enjoyed a favoured regime, his door left "
            "unlocked, receiving robbers, traffickers and counterfeiters as he pleased. "
            "It is his conversations with Orsoni, then 31, that most interest "
            "investigators, because the two of them talked about almost nothing but "
            "Corsica, and because they show Germani had anticipated the orphans' move "
            "two years before the airport killings."
        ),
    ),
}

ANDREANI_BIO = (
    "Childhood friend of Christophe Guazzelli and close to Ange-Marie Michelosi junior. "
    "Big, red-haired and bearded, a butcher by training, from La Porta like the "
    "Guazzellis. He was 27 at the time of the airport killings and already had a "
    "considerable record.\n\n"
    "He is the join between the two worlds this universe covers. A nationalist militant, "
    "his first conviction came at seventeen, for violence against police at a "
    "demonstration in support of the independence leader Jean-Guy Talamoni, then in "
    "custody in an extortion case that also involved Charles Pieri, the former FLNC "
    "leader. His file also carries an arrest in 2009 over a car bomb against a "
    "gendarmerie, an action claimed by the FLNC unifié.\n\n"
    "The heir to the Brise, whose name made half the island flinch, and the young "
    "hothead out of the ranks of militant nationalism: the alliance of the two "
    "Christophes was reason enough to worry the authorities. Arrested with Michelosi at "
    "Tollare on 12 December 2017 and charged in the Bastia-Poretta double assassination."
)

INCIDENTS = [
    (
        "savelli-1999",
        IncidentType.MURDER,
        ym(1999, 8),
        None,
        "Balagne",
        "Dominique Savelli, a butcher in the Balagne, was assassinated in August 1999. "
        "Armata Corsa claimed the killing as a preventive political assassination, "
        "saying he had been about to murder one of their leaders. Savelli was not an "
        "independence militant at all; he was known for minor common-law matters and was "
        "close to Francis Mariani, who had given him work. The Brise was widely suspected "
        "of avenging him when the Marcelli brothers were killed two years later.",
        [("Dominique Savelli", ParticipantRole.VICTIM, ParticipantOutcome.KILLED, None)],
    ),
    (
        "santoni-2001",
        IncidentType.MURDER,
        ymd(2001, 8, 17),
        "Monacia-d'Aullène",
        "Leaving a wedding, Monacia-d'Aullène",
        "François Santoni, founder and leader of Armata Corsa, was cut down by a burst "
        "of submachine-gun fire on 17 August 2001 as he left a wedding in the far south "
        "of the island. Two of his lieutenants were dead four days later and a third "
        "within three weeks: the movement he had created two years earlier was "
        "decapitated in under a month.",
        [("François Santoni", ParticipantRole.VICTIM, ParticipantOutcome.KILLED, None)],
    ),
    (
        "marcelli-2001",
        IncidentType.MURDER,
        ymd(2001, 8, 21),
        "Moriani-Plage",
        "Near Moriani-Plage",
        "Dominique and Jean-Christophe Marcelli, two of François Santoni's lieutenants "
        "and not of the same family despite the shared name, were found dead near "
        "Moriani-Plage on 21 August 2001, four days after their leader.\n\n"
        "Police were stunned by the violence of it. Dominique Marcelli's body lay "
        "partially burned and riddled with bullets beside a completely gutted car, with "
        "the charred body of his companion in the boot. The day before, when "
        "Jean-Christophe collected Dominique by car outside his home, several men got "
        "into the vehicle; watching from the window, Dominique's wife recognised Jacques "
        "Mariani. Neither man was seen alive again.\n\n"
        "The obvious motive was Dominique Savelli, Francis Mariani's butcher, killed by "
        "Armata Corsa two years earlier.",
        [
            ("Dominique Marcelli", ParticipantRole.VICTIM, ParticipantOutcome.KILLED, None),
            ("Jean-Christophe Marcelli", ParticipantRole.VICTIM, ParticipantOutcome.KILLED, None),
            (
                "Jacques Mariani",
                ParticipantRole.ASSISTED,
                ParticipantOutcome.UNHARMED,
                "Recognised by Dominique Marcelli's wife among the men who got into the "
                "car outside her home the day before the bodies were found. An "
                "eyewitness identification at the abduction, not at the killing, and he "
                "was never tried for this.",
            ),
        ],
    ),
    (
        "montigny-2001",
        IncidentType.MURDER,
        ymd(2001, 9, 5),
        "Bastia",
        "Cyber Corsica internet cafe, Bastia",
        "Nicolas Montigny, 27, an Armata Corsa militant, was sitting on the mezzanine of "
        "the Cyber Corsica internet cafe in Bastia on 5 September 2001, downloading "
        "music, when gunmen killed him with three military weapons. Witnesses saw two "
        "men, one slim and one athletic with short hair, in dark clothes with scarves "
        "over their noses, leave towards a Renault Laguna parked nearby; one of them "
        "then came back into the cafe.\n\n"
        "Alone among the killings in this universe, this one was tried and produced "
        "convictions. On 13 March 2008 Jacques Mariani was sentenced to fifteen years "
        "and his father Francis to seven. Francis went on the run rather than serve it "
        "and died in the explosion at Casevecchie ten months later.",
        [
            ("Nicolas Montigny", ParticipantRole.VICTIM, ParticipantOutcome.KILLED, None),
            (
                "Jacques Mariani",
                ParticipantRole.SHOOTER,
                ParticipantOutcome.UNHARMED,
                "CONVICTED. Sentenced to fifteen years at the verdict of 13 March 2008. "
                "Unlike almost every other role recorded in this universe, this one was "
                "established by a court.",
            ),
            (
                "Francis Mariani",
                ParticipantRole.ASSISTED,
                ParticipantOutcome.UNHARMED,
                "CONVICTED. Sentenced to seven years at the verdict of 13 March 2008, "
                "and went on the run rather than serve it.",
            ),
        ],
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
        uni = (await s.execute(text("SELECT id FROM universe WHERE slug='corsica'"))).first()[0]
        actor_row = (
            await s.execute(
                text(
                    "SELECT id, email FROM users WHERE global_role='ADMIN' "
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

        muni = {
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
            muni[name] = (
                await create_municipality(s, MunicipalityCreate(universe_id=uni, name=name), actor)
            ).id

        gangs = {
            g.name: g.id
            for g in (await s.execute(select(Gang).where(Gang.universe_id == uni))).scalars()
        }
        for name, aliases, desc in GANGS:
            if name in gangs:
                skipped.append(f"gang {name}")
                continue
            created.append(f"gang {name}")
            if dry:
                gangs[name] = uuid.uuid4()
                continue
            gangs[name] = (
                await create_gang(
                    s,
                    GangCreate(universe_id=uni, name=name, aliases=aliases, description=desc),
                    actor,
                )
            ).id

        sets = {
            x.name: x.id
            for x in (await s.execute(select(GangSet).where(GangSet.universe_id == uni))).scalars()
        }
        if ARMATA not in sets:
            created.append(f"set {ARMATA}")
            sets[ARMATA] = uuid.uuid4()
            if not dry:
                sets[ARMATA] = (
                    await create_gang_set(
                        s,
                        SetCreate(
                            universe_id=uni,
                            name=ARMATA,
                            bio=(
                                "The armed wing of the movement Santoni founded in June 1999. "
                                "Decapitated between 17 August and 5 September 2001, when its "
                                "leader, two lieutenants and a militant were shot dead inside "
                                "three weeks."
                            ),
                            status=SetStatus.EXTINCT,
                            gang_id=gangs[ARMATA],
                        ),
                        actor,
                    )
                ).id
        else:
            skipped.append(f"set {ARMATA}")

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
            affs = []
            if d.get("set"):
                affs = [
                    MemberSetAffiliationIn(
                        set_id=sets[d["set"]], is_primary=True, from_date=d.get("from_date")
                    )
                ]
            obj = await create_member(
                s,
                MemberCreate(
                    universe_id=uni,
                    legal_name=legal_name,
                    biography=d["biography"],
                    status=d["status"],
                    dob=d.get("dob"),
                    date_of_death=d.get("date_of_death"),
                    gang_id=gangs[d["gang"]] if d.get("gang") else None,
                    affiliations=affs,
                ),
                actor,
            )
            mem[legal_name] = obj.id

        andreani = await existing(Member, legal_name="Christophe Andreani")
        if andreani is None or andreani.biography.strip() == ANDREANI_BIO.strip():
            skipped.append("Christophe Andreani biography")
        else:
            created.append("Christophe Andreani biography (nationalist background)")
            if not dry:
                await update_member(s, andreani.id, uni, MemberUpdate(biography=ANDREANI_BIO))

        all_members = {
            m.legal_name: m.id
            for m in (await s.execute(select(Member).where(Member.universe_id == uni))).scalars()
        }
        all_members.update(mem)

        for key, itype, date, muni_name, location, narrative, participants in INCIDENTS:
            sortable = date.to_sortable_date()
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
                    municipality_id=muni.get(muni_name) if muni_name else None,
                    location_text=location,
                    narrative=narrative,
                    participants=[
                        ParticipantCreate(member_id=all_members[n], role=r, outcome=o, notes=note)
                        for n, r, o, note in participants
                        if n in all_members
                    ],
                ),
                actor,
            )

        if ARMATA in sets and BRISE in sets:
            a, b = sorted([sets[ARMATA], sets[BRISE]])
            rel = (
                (
                    await s.execute(
                        select(SetRelationship).where(
                            SetRelationship.set_a_id == a, SetRelationship.set_b_id == b
                        )
                    )
                )
                .scalars()
                .first()
            )
            if rel is not None:
                skipped.append(f"relationship {ARMATA} <-> {BRISE}")
            else:
                created.append(f"relationship {ARMATA} <-> {BRISE} (ENEMY, from 1999)")
                if not dry:
                    s.add(
                        SetRelationship(
                            set_a_id=a,
                            set_b_id=b,
                            relationship_type=SetRelationshipType.ENEMY,
                            from_date=yr(1999).model_dump(mode="json"),
                        )
                    )
                    await s.commit()

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
