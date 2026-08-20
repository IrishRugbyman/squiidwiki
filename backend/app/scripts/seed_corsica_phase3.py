"""Seed phase 3: Corse-du-Sud, and the sons who came back for their fathers.

Phase 1 made the Brise de Mer, phase 2 destroyed its founding generation. This
is the third act, and it has two halves.

**Corse-du-Sud.** The southern power the Brise never controlled: Jean-Je
Colonna, "dernier parrain du sud de la Corse", his symbolic heir Jean-Claude
Colonna, and Ange-Marie Michelosi senior, who inherited Colonna's position and
ran the Ajaccio cafe that gave the Petit Bar its name. Both heirs were shot
within a month of each other in the summer of 2008.

**Le clan des orphelins.** The book's own term, and the title of its foreword.
The sons of the men killed in phase 2 spent years preparing revenge on the camp
they held responsible, and took it on 5 December 2017 at Bastia-Poretta
airport. Ange-Marie Michelosi junior is the hinge of the whole thing: he left
his natural clan, the Petit Bar, to join the Brise heirs and avenge his father,
which the affiliation model records as a closed spell rather than a deletion.

Almost everything here comes from the index of persons at the back of Lazard &
Galland, Vendetta, which is the most compact reliable statement of who was who,
plus the chronology for the dates.

Deliberately left out: Robert Feliciaggi, killed at Ajaccio in March 2006, who
appears in the chronology but nowhere I can source a description of; and Icham
Saffour, killed at Furiani in 2019, for the same reason. A name and a date is
not a member record.

Idempotent. Run from backend/:
  .venv/bin/python -m app.scripts.seed_corsica_phase3          # dry run
  .venv/bin/python -m app.scripts.seed_corsica_phase3 --apply
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
from app.crud.member import create_member, end_member_affiliation, update_member
from app.crud.municipality import create_municipality
from app.models import Gang, GangSet, Incident, Member, MemberSet, Municipality, SetRelationship
from app.schemas.gang import GangCreate
from app.schemas.gang_set import SetCreate
from app.schemas.incident import IncidentCreate, ParticipantCreate
from app.schemas.member import MemberCreate, MemberSetAffiliationIn, MemberUpdate
from app.schemas.municipality import MunicipalityCreate

UNIVERSE_SLUG = "corsica"
BRISE, PETIT_BAR, GERMANI, ORPHELINS = (
    "Brise de Mer",
    "Petit Bar",
    "Clan Germani",
    "Clan des orphelins",
)


def ymd(y, m, d):
    return FuzzyDate(year=y, month=m, day=d, precision=DatePrecision.YMD)


def yr(y, approx=False):
    return FuzzyDate(year=y, precision=DatePrecision.Y, approx=approx)


MUNICIPALITIES = ["Pietrosella", "Grosseto-Prugna", "Porto-Pollo"]

# legal_name -> dict. `set` is the primary current affiliation.
MEMBERS = {
    "Jean-Baptiste Jérôme Colonna": dict(
        status=MemberStatus.DEAD,
        dob=yr(1939, approx=True),
        date_of_death=ymd(2006, 11, 1),
        aliases=["Jean-Jé"],
        gang=PETIT_BAR,
        set=PETIT_BAR,
        from_date=yr(1980, approx=True),
        biography=(
            "Known as Jean-Jé. The last godfather of southern Corsica, and the man whose "
            "authority held a fragile status quo in place across the island. He died on "
            "1 November 2006 in a road accident at Porto-Pollo, aged 67.\n\n"
            "His death is the quiet hinge of everything that follows. At his funeral the "
            "Brise de Mer and Richard Casanova's new friends stood together and made a "
            "show of good relations: the godfather is dead but nothing changes, was the "
            "message. Neither camp wanted open war. Less than three weeks later Casanova "
            "was released on bail and the arrangement began to come apart."
        ),
    ),
    "Jean-Claude Colonna": dict(
        status=MemberStatus.DEAD,
        dob=yr(1961, approx=True),
        date_of_death=ymd(2008, 6, 16),
        gang=PETIT_BAR,
        set=PETIT_BAR,
        from_date=yr(1990, approx=True),
        biography=(
            "Cousin of Jean-Jé Colonna, and more importantly his symbolic heir in "
            "southern Corsica. Assassinated at Pietrosella on 16 June 2008, aged 47, "
            "eight weeks after Richard Casanova and three weeks before Ange-Marie "
            "Michelosi. Michel Tomi was heard as a witness in the investigation into his "
            "death in May 2010, and Jean-Luc Germani was among those convicted of "
            "criminal conspiracy in the case in February 2016."
        ),
    ),
    "Ange-Marie Michelosi senior": dict(
        status=MemberStatus.DEAD,
        dob=yr(1954, approx=True),
        date_of_death=ymd(2008, 7, 8),
        gang=PETIT_BAR,
        set=PETIT_BAR,
        from_date=yr(1990, approx=True),
        biography=(
            "Heir to Jean-Jé Colonna, the godfather of southern Corsica, and manager of "
            "the Ajaccio cafe called le Petit Bar that gave the gang its name. "
            "Assassinated at Grosseto-Prugna on 8 July 2008, aged 54, three weeks after "
            "Jean-Claude Colonna. The two killings removed the southern succession "
            "inside a month.\n\n"
            "His son left the Petit Bar to avenge him."
        ),
    ),
    "Ange-Marie Michelosi junior": dict(
        status=MemberStatus.LOCKED,
        gang=BRISE,
        set=ORPHELINS,
        from_date=yr(2009, approx=True),
        left_petit_bar=yr(2009, approx=True),
        biography=(
            "Son of Ange-Marie Michelosi. He left his natural clan, the Petit Bar, to "
            "move closer to the heirs of the Brise de Mer and avenge his father, which "
            "makes him the hinge between the two halves of this story: the son of a "
            "southern boss fighting alongside the sons of Bastia.\n\n"
            "Christophe Guazzelli addressed him as 'frère' and told him the two deaths "
            "at Poretta were only the beginning. Arrested at Tollare, in the far north "
            "of Cap Corse, on 12 December 2017 with Christophe Andreani, and charged in "
            "the Bastia-Poretta double assassination."
        ),
    ),
    "Jean-Luc Codaccioni": dict(
        status=MemberStatus.DEAD,
        dob=yr(1963, approx=True),
        date_of_death=ymd(2017, 12, 5),
        gang=GERMANI,
        set=GERMANI,
        from_date=yr(2008, approx=True),
        biography=(
            "Spiritual son of Michel Tomi and close to Jean-Luc Germani. Former head of "
            "security for the PMU in Gabon, part of the African gaming network through "
            "which so much of this money moved.\n\n"
            "Convicted with Germani in February 2016 of criminal conspiracy in the "
            "Jean-Claude Colonna case. Assassinated at Bastia-Poretta airport on 5 "
            "December 2017, aged 54, alongside Antoine Quilichini. He was identified for "
            "his killer by a prison officer who embraced him in the terminal, a gesture "
            "the investigation came to call the kiss of death."
        ),
    ),
    "Antoine Quilichini": dict(
        status=MemberStatus.DEAD,
        dob=yr(1968, approx=True),
        date_of_death=ymd(2017, 12, 5),
        aliases=["Tony le Boucher"],
        gang=GERMANI,
        set=GERMANI,
        from_date=yr(2008, approx=True),
        biography=(
            "Known as Tony le Boucher. Close to Jean-Luc Germani and to Jean-Luc "
            "Codaccioni, and convicted with them in February 2016 of criminal conspiracy "
            "in the Jean-Claude Colonna case. Assassinated with Codaccioni at "
            "Bastia-Poretta airport on 5 December 2017, aged 49."
        ),
    ),
    "Stéphane Luciani": dict(
        status=MemberStatus.LOCKED,
        gang=GERMANI,
        set=GERMANI,
        from_date=yr(2008, approx=True),
        biography=(
            "Convicted on 12 February 2016, with Jean-Luc Germani, Jean-Luc Codaccioni, "
            "Antoine Quilichini and Frédéric Federici, of criminal conspiracy in the "
            "assassination of Jean-Claude Colonna.\n\n"
            "Held at Borgo, he was a target of the plan the orphans laid after Poretta: "
            "with the rest of the camp behind bars, the intention was to reach them "
            "there, and a prison officer was to put poison in his coffee."
        ),
    ),
    "Christophe Guazzelli": dict(
        status=MemberStatus.LOCKED,
        dob=ymd(1991, 7, 3),
        gang=BRISE,
        set=ORPHELINS,
        from_date=yr(2009, approx=True),
        biography=(
            "Younger son of Francis Guazzelli and Sylvie Cappuri, born 3 July 1991. He "
            "was eighteen when his father was shot on the road to La Porta, and spent "
            "close to eight years preparing his answer, physically and mentally.\n\n"
            "Charged over the Bastia-Poretta double assassination of 5 December 2017 and "
            "suspected of being the gunman. He wore a latex mask, which was sent to the "
            "mainland to be destroyed once he learned it had been caught on video. "
            "Afterwards he told Ange-Marie Michelosi that the two deaths were only the "
            "beginning, that he intended to wipe out everyone suspected of killing their "
            "fathers, and that those already in prison would be reached there.\n\n"
            "Arrested at Marignane in August 2011 for drug trafficking, and again at "
            "Porto-Vecchio on 12 December 2017 with his brother Richard."
        ),
    ),
    "Richard Guazzelli": dict(
        status=MemberStatus.LOCKED,
        dob=ymd(1989, 12, 2),
        gang=BRISE,
        set=ORPHELINS,
        from_date=yr(2009, approx=True),
        biography=(
            "Elder son of Francis Guazzelli and Sylvie Cappuri, born 2 December 1989. He "
            "carries the first name of his godfather, Richard Casanova, which is a fair "
            "summary of how tangled these families are: his godfather was assassinated "
            "in April 2008 and his father nineteen months later.\n\n"
            "Arrested a few months after his brother in the 2011 Marignane drugs case, "
            "and again with him at Porto-Vecchio on 12 December 2017. Charged over the "
            "Bastia-Poretta double assassination."
        ),
    ),
    "Christophe Andreani": dict(
        status=MemberStatus.LOCKED,
        gang=BRISE,
        set=ORPHELINS,
        from_date=yr(2009, approx=True),
        biography=(
            "Childhood friend of Christophe Guazzelli and close to Ange-Marie Michelosi "
            "junior. Arrested with Michelosi at Tollare on 12 December 2017 and charged "
            "in the Bastia-Poretta double assassination."
        ),
    ),
    "Michel Tomi": dict(
        status=MemberStatus.UNKNOWN,
        dob=yr(1946, approx=True),
        gang=None,
        set=None,
        biography=(
            "The godfather of gaming in Africa, a billionaire whose network appeared to "
            "have no limits, and the spiritual father of both Richard Casanova and "
            "Jean-Luc Codaccioni. Not a member of any clan: a patron of them, and the "
            "one man Jacques Mariani thought could act as juge de paix and stop the war "
            "between the Mariani family and the Germani camp.\n\n"
            "He served three months in 1989 and was definitively convicted in 1996, to "
            "three years, on suspicion of fraud and misappropriation. He was heard as a "
            "witness in the investigation into Jean-Claude Colonna's death on 20 May "
            "2010. After the Poretta killings the orphans expected him to put a price on "
            "their heads."
        ),
    ),
}

INCIDENTS = [
    (
        "jc-colonna-2008",
        IncidentType.MURDER,
        ymd(2008, 6, 16),
        "Pietrosella",
        "Pietrosella, Corse-du-Sud",
        "Jean-Claude Colonna, symbolic heir to Jean-Jé Colonna in southern Corsica, was "
        "assassinated at Pietrosella on 16 June 2008, aged 47. Michel Tomi was heard as "
        "a witness in the investigation in May 2010, and in February 2016 Jean-Luc "
        "Germani, Jean-Luc Codaccioni, Antoine Quilichini, Stéphane Luciani and Frédéric "
        "Federici were convicted of criminal conspiracy in the case.",
        [("Jean-Claude Colonna", ParticipantRole.VICTIM, ParticipantOutcome.KILLED, None)],
    ),
    (
        "michelosi-2008",
        IncidentType.MURDER,
        ymd(2008, 7, 8),
        "Grosseto-Prugna",
        "Grosseto-Prugna, Corse-du-Sud",
        "Ange-Marie Michelosi, heir to Jean-Jé Colonna and manager of the Ajaccio cafe "
        "that gave the Petit Bar its name, was assassinated at Grosseto-Prugna on 8 July "
        "2008, aged 54. With Jean-Claude Colonna three weeks earlier and Richard "
        "Casanova in April, the southern succession had been removed inside three "
        "months. His son left the Petit Bar to avenge him.",
        [("Ange-Marie Michelosi senior", ParticipantRole.VICTIM, ParticipantOutcome.KILLED, None)],
    ),
    (
        "poretta-2017",
        IncidentType.MURDER,
        ymd(2017, 12, 5),
        "Lucciana",
        "Bastia-Poretta airport, Lucciana",
        "Jean-Luc Codaccioni and Antoine Quilichini were shot dead in the terminal at "
        "Bastia-Poretta airport on 5 December 2017. The gunman wore a latex mask and had "
        "waited beside Codaccioni for fifteen minutes; Codaccioni looked at him a hundred "
        "times, he said afterwards, and did not recognise him. A prison officer had "
        "embraced Codaccioni in the terminal so that the gunman could be certain of his "
        "target, a gesture the case came to call the kiss of death. The mask was sent to "
        "the mainland to be destroyed once he learned it had been filmed.\n\n"
        "This is the revenge of the sons. Christophe Guazzelli's father had been killed "
        "in November 2009, Ange-Marie Michelosi junior's in July 2008, and the men shot "
        "here belonged to the camp they held responsible. Guazzelli told Michelosi it was "
        "only the beginning, that the rest of the camp was already in prison and would be "
        "reached there, and that poison was prepared for Stéphane Luciani at Borgo.\n\n"
        "Christophe Guazzelli, Richard Guazzelli, Ange-Marie Michelosi junior and "
        "Christophe Andreani were all arrested in December 2017 and charged. None of the "
        "roles recorded here has been tested at trial.",
        [
            ("Jean-Luc Codaccioni", ParticipantRole.VICTIM, ParticipantOutcome.KILLED, None),
            ("Antoine Quilichini", ParticipantRole.VICTIM, ParticipantOutcome.KILLED, None),
            (
                "Christophe Guazzelli",
                ParticipantRole.SHOOTER,
                ParticipantOutcome.UNHARMED,
                "Charged and suspected of being the gunman. Not tried at the time of the "
                "source; attributed by investigators, not established by a court.",
            ),
            (
                "Richard Guazzelli",
                ParticipantRole.ASSISTED,
                ParticipantOutcome.UNHARMED,
                "Charged in the case. Not tried at the time of the source.",
            ),
            (
                "Ange-Marie Michelosi junior",
                ParticipantRole.ASSISTED,
                ParticipantOutcome.UNHARMED,
                "Charged in the case. Not tried at the time of the source.",
            ),
            (
                "Christophe Andreani",
                ParticipantRole.ASSISTED,
                ParticipantOutcome.UNHARMED,
                "Charged in the case. Not tried at the time of the source.",
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
        uni = (
            await s.execute(
                text("SELECT id FROM universe WHERE slug = :slug"), {"slug": UNIVERSE_SLUG}
            )
        ).first()[0]
        actor_row = (
            await s.execute(
                text(
                    "SELECT id, email FROM users WHERE global_role = 'ADMIN' "
                    "ORDER BY created_at LIMIT 1"
                )
            )
        ).first()
        actor = actor_row[0]
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

        # --- gangs ----------------------------------------------------------
        gangs = {
            g.name: g.id
            for g in (await s.execute(select(Gang).where(Gang.universe_id == uni))).scalars()
        }
        if PETIT_BAR not in gangs:
            created.append(f"gang {PETIT_BAR}")
            gangs[PETIT_BAR] = uuid.uuid4()
            if not dry:
                gangs[PETIT_BAR] = (
                    await create_gang(
                        s,
                        GangCreate(
                            universe_id=uni,
                            name=PETIT_BAR,
                            description=(
                                "The Ajaccio formation, named after the cafe Ange-Marie "
                                "Michelosi ran, which inherited the position of Jean-Jé "
                                "Colonna, the last godfather of southern Corsica. The power "
                                "the Brise de Mer never held. Its two heirs, Jean-Claude "
                                "Colonna and Michelosi, were assassinated three weeks apart "
                                "in the summer of 2008."
                            ),
                        ),
                        actor,
                    )
                ).id
        else:
            skipped.append(f"gang {PETIT_BAR}")

        # --- sets -----------------------------------------------------------
        sets = {
            x.name: x.id
            for x in (await s.execute(select(GangSet).where(GangSet.universe_id == uni))).scalars()
        }
        for name, gang_name, muni_name, bio in [
            (
                PETIT_BAR,
                PETIT_BAR,
                "Ajaccio",
                "Named after the Ajaccio cafe Ange-Marie Michelosi managed. The southern "
                "clan that inherited Jean-Jé Colonna's authority, and lost both its heirs "
                "in the summer of 2008.",
            ),
            (
                ORPHELINS,
                BRISE,
                "Bastia",
                "The book's own term, and the title of its foreword: the sons of the men "
                "killed in 2008 and 2009, who spent years preparing revenge on the camp "
                "they held responsible and took it at Bastia-Poretta airport in December "
                "2017. Ange-Marie Michelosi junior joined them from the Petit Bar, his "
                "father's clan, to avenge him.",
            ),
        ]:
            if name in sets:
                skipped.append(f"set {name}")
                continue
            created.append(f"set {name}")
            if dry:
                sets[name] = uuid.uuid4()
                continue
            sets[name] = (
                await create_gang_set(
                    s,
                    SetCreate(
                        universe_id=uni,
                        name=name,
                        bio=bio,
                        status=SetStatus.ACTIVE,
                        gang_id=gangs[gang_name],
                        municipality_id=muni.get(muni_name),
                    ),
                    actor,
                )
            ).id

        # --- members ---------------------------------------------------------
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
            affiliations = []
            # Michelosi junior starts in his father's clan and leaves it; the
            # Petit Bar spell is opened here and closed below, so the record says
            # he left rather than that he was never there.
            if d.get("left_petit_bar"):
                affiliations.append(
                    MemberSetAffiliationIn(
                        set_id=sets[PETIT_BAR], is_primary=True, from_date=yr(2000, True)
                    )
                )
            elif d.get("set"):
                affiliations.append(
                    MemberSetAffiliationIn(
                        set_id=sets[d["set"]], is_primary=True, from_date=d.get("from_date")
                    )
                )
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
                    gang_id=gangs[d["gang"]] if d.get("gang") else None,
                    affiliations=affiliations,
                ),
                actor,
            )
            mem[legal_name] = obj.id

            if d.get("left_petit_bar"):
                spell = (
                    (
                        await s.execute(
                            select(MemberSet).where(
                                MemberSet.member_id == obj.id,
                                MemberSet.set_id == sets[PETIT_BAR],
                                MemberSet.until_date.is_(None),
                            )
                        )
                    )
                    .scalars()
                    .first()
                )
                if spell:
                    await end_member_affiliation(
                        s, obj.id, spell.id, d["left_petit_bar"].model_dump(mode="json")
                    )
                await update_member(
                    s,
                    obj.id,
                    uni,
                    MemberUpdate(
                        affiliations=[
                            MemberSetAffiliationIn(
                                set_id=sets[ORPHELINS],
                                is_primary=True,
                                from_date=d.get("from_date"),
                            )
                        ]
                    ),
                )
                created.append("  (Michelosi junior: Petit Bar spell closed 2009)")

        # --- Jacques Mariani joins the orphans as a secondary affiliation -----
        jm = await existing(Member, legal_name="Jacques Mariani")
        if jm is not None:
            open_spells = (
                (
                    await s.execute(
                        select(MemberSet).where(
                            MemberSet.member_id == jm.id, MemberSet.until_date.is_(None)
                        )
                    )
                )
                .scalars()
                .all()
            )
            if any(sp.set_id == sets.get(ORPHELINS) for sp in open_spells):
                skipped.append("Jacques Mariani -> Clan des orphelins")
            else:
                created.append("Jacques Mariani -> Clan des orphelins")
                if not dry:
                    affs = [
                        MemberSetAffiliationIn(
                            set_id=sp.set_id,
                            rank=sp.rank,
                            is_primary=sp.is_primary,
                            from_date=sp.from_date,
                        )
                        for sp in open_spells
                    ]
                    affs.append(
                        MemberSetAffiliationIn(
                            set_id=sets[ORPHELINS], is_primary=False, from_date=yr(2016, True)
                        )
                    )
                    await update_member(s, jm.id, uni, MemberUpdate(affiliations=affs))

        # --- incidents --------------------------------------------------------
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
                        ParticipantCreate(member_id=mem[n], role=r, outcome=o, notes=note)
                        for n, r, o, note in participants
                        if n in mem
                    ],
                ),
                actor,
            )

        # --- the orphans against the Germani camp ------------------------------
        if ORPHELINS in sets and GERMANI in sets:
            a, b = sorted([sets[ORPHELINS], sets[GERMANI]])
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
                skipped.append(f"relationship {ORPHELINS} <-> {GERMANI}")
            else:
                created.append(f"relationship {ORPHELINS} <-> {GERMANI} (ENEMY, from 2009)")
                if not dry:
                    s.add(
                        SetRelationship(
                            set_a_id=a,
                            set_b_id=b,
                            relationship_type=SetRelationshipType.ENEMY,
                            from_date=yr(2009).model_dump(mode="json"),
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
