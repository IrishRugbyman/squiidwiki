"""The long tail: the fixers, the front men, the football, and two missed killings.

The names that appear three or four times each and are easy to skip, except
that two of them are not minor at all.

**Daniel Vittini** was the Brise de Mer's man for the Corte region and was shot
in the back of the neck on 6 July 2008, two days before Ange-Marie Michelosi. He
belongs squarely in the war that phase 2 covered and was simply missed.

**Jean-Claude Guazzelli** is the fourth Guazzelli brother, the one the book
describes as taking an entirely different path while his brothers were being
watched for every new robbery. He was made director of Crédit Agricole for the
island, elected for the RPR, and then took the head of the ADEC, the agency that
steers Corsican economic development. He is the answer to a question phase 2
left hanging.

Also here: Dominique Rutily, Richard Casanova's other half, killed in 1996;
Michel Ferracci, the actor Casanova installed to watch the till at the Cercle
Wagram; Jean Casta, the Air Inter regional director; Charles Fraticelli, whose
son's nightclub was blown up; Gilbert Voillemier of L'Apocalypse; and Bati
Gentili, a football coach who is in the book only because two members of the
Brise may or may not have come to see him about a young player.

Rolland Courbis is named in the source as the friend and adviser who was with
Rutily when he was shot. He is recorded in the incident narrative rather than as
a member: he is a witness to it, not a party to any of this.

Idempotent. Run from backend/:
  .venv/bin/python -m app.scripts.seed_corsica_long_tail          # dry run
  .venv/bin/python -m app.scripts.seed_corsica_long_tail --apply
"""

import argparse
import asyncio
import uuid

from sqlalchemy import select, text

from app.core.database import _session_factories
from app.core.enums import (
    BusinessRole,
    BusinessStatus,
    BusinessType,
    DatePrecision,
    IncidentType,
    MemberStatus,
    ParticipantOutcome,
    ParticipantRole,
)
from app.core.fuzzy_date import FuzzyDate
from app.crud.business import create_business
from app.crud.incident import create_incident
from app.crud.member import create_member, update_member
from app.crud.municipality import create_municipality
from app.models import Business, Gang, GangSet, Incident, Member, Municipality
from app.schemas.business import BusinessCreate, BusinessMemberIn
from app.schemas.incident import IncidentCreate, ParticipantCreate
from app.schemas.member import MemberCreate, MemberSetAffiliationIn, MemberUpdate
from app.schemas.municipality import MunicipalityCreate

BRISE = "Brise de Mer"


def ymd(y, m, d):
    return FuzzyDate(year=y, month=m, day=d, precision=DatePrecision.YMD)


def ym(y, m):
    return FuzzyDate(year=y, month=m, precision=DatePrecision.YM)


def yr(y, approx=False):
    return FuzzyDate(year=y, precision=DatePrecision.Y, approx=approx)


MUNICIPALITIES = ["Poggio-di-Venaco", "Ghisonaccia", "Aléria", "L'Île-Rousse", "Calvi"]

MEMBERS = {
    "Daniel Vittini": dict(
        status=MemberStatus.DEAD,
        date_of_death=ymd(2008, 7, 6),
        gang=BRISE,
        set=BRISE,
        from_date=yr(1990, approx=True),
        biography=(
            "The Brise de Mer's man for the Corte region, in the centre of the island, "
            "with a drinks distribution company as his standing.\n\n"
            "On 6 July 2008 he was found face down in a clearing two hundred metres from "
            "the route nationale near Poggio-di-Venaco, beside one of his company's cars. "
            "He had been executed with his back to the gunman, several bullets in the "
            "nape of the neck. Investigators called it Jean-Luc Germani's signature.\n\n"
            "He died two days before Ange-Marie Michelosi and eleven weeks after Richard "
            "Casanova, in the middle of the summer that took the founding generation "
            "apart. 'Si sente u sangue', Francis Mariani kept saying that year: it smells "
            "of blood."
        ),
    ),
    "Jean-Claude Guazzelli": dict(
        status=MemberStatus.UNKNOWN,
        gang=None,
        set=None,
        biography=(
            "The fourth of the Guazzelli brothers and, by the book's account, the eldest: "
            "the one who took an entirely different path. While Francis, Jean-Angelo and "
            "Paul-Louis were watched by the authorities, suspected at every new robbery, "
            "building palaces in their village and changing Porsches like three-piece "
            "suits, Jean-Claude Guazzelli was appointed director of Crédit Agricole for "
            "the island. Elected for the RPR, he later took the head of the ADEC, the "
            "agency that steers Corsican economic development.\n\n"
            "The bank he ran held the accounts investigators later went through when the "
            "Bastia branch of the judicial police tried to show the gap between the "
            "Guazzellis' declared income and how they lived. The sister of Jean-Jacques "
            "and Guy Voillemier was running the Bastia branch at the time.\n\n"
            "No gang and no set. He is the fourth brother, not a member, and the point of "
            "him is precisely the distance."
        ),
    ),
    "Dominique Rutily": dict(
        status=MemberStatus.DEAD,
        date_of_death=ym(1996, 3),
        gang=BRISE,
        set=BRISE,
        from_date=yr(1985, approx=True),
        biography=(
            "Richard Casanova's other half, in the book's word his binôme. President of "
            "the Football Club de Calvi and, like Casanova, thinking bigger: Casanova "
            "circled Marseille, Rutily had his eye on Nice.\n\n"
            "He also managed the Challenger discothèque at L'Île-Rousse. When the "
            "authorities opened their second front in December after the 1986 sweep, the "
            "Challenger's accounts were gone through and the contractor who built the "
            "club admitted keeping a double set of books at Rutily's request: he had "
            "invoiced far below the real cost and handed over the difference, six hundred "
            "thousand euros, in cash with nothing written down.\n\n"
            "Assassinated in March 1996 leaving a match, on the car park of the stadium "
            "at Hyères in the Var. He was in the company of Rolland Courbis, then his "
            "friend and adviser."
        ),
    ),
    "Michel Ferracci": dict(
        status=MemberStatus.UNKNOWN,
        gang=None,
        set=None,
        biography=(
            "An actor, married to the Belgian actress Émilie Dequenne, with a few "
            "appearances in the series Mafiosa. Above all a close associate of Richard "
            "Casanova, who placed him as director of gaming at the Cercle Wagram in "
            "Paris, a strategic post from which to watch the club's finances.\n\n"
            "It was Ferracci who made the call, in the summer of 2001, that gave "
            "Christophe Guazzelli his first push into football, just before the training "
            "camp at Clairefontaine. He was, as the book puts it, acting under orders."
        ),
    ),
    "Jean Casta": dict(
        status=MemberStatus.UNKNOWN,
        gang=None,
        set=None,
        biography=(
            "Regional director of Air Inter and later a mayor. A small, likeable, "
            "intelligent, easy-going man who had been at school with the Guazzelli "
            "brothers, was a friend of Jean-Claude Guazzelli at Crédit Agricole, and was "
            "very close to Angelo, who produced a well-regarded oil on his property. He "
            "knew other members of the Brise and made no secret of it. In Corsica, he "
            "would say, everyone knows everyone.\n\n"
            "Police circled him for a long time over the 1991 robbery of a Sécuripost "
            "consignment on the Bastia-Paris flight, which arrived in the capital empty, "
            "the bags weighted with pieces of cardboard. Passengers have no access to the "
            "hold in flight, so the thief had been inside a trunk checked in at Bastia, "
            "unusually heavy and bulky.\n\n"
            "In 2013 he was convicted at a Cercle Wagram trial and sentenced to two "
            "years, one suspended, for moving between five and ten million euros out of "
            "the gaming club's coffers to the Guazzelli family. He declined to answer the "
            "authors' questions."
        ),
    ),
    "Charles Fraticelli": dict(
        status=MemberStatus.UNKNOWN,
        gang=None,
        set=None,
        biography=(
            "Owner of a tabac, newsagent and souvenir shop at Aléria, on the eastern "
            "plain, and one of the few friends Francis Mariani still had at the end. As "
            "Mariani rose at five each morning to be out before the six o'clock searches, "
            "changed address constantly and cut his acquaintance to the minimum, "
            "Fraticelli regularly had him to dinner.\n\n"
            "It was over one of those dinners, one evening in April 2008 with Claude "
            "Chossat present, that Mariani went round and round the same subject: he was "
            "now certain Jean-Luc Germani was behind the attempt on his life, and he "
            "intended to find him.\n\n"
            "After Daniel Vittini's assassination police put Fraticelli's home under "
            "surveillance. His son ran a nightclub, Le G, on the route de la Mer at "
            "Ghisonaccia, which was destroyed by a bomb on 11 November 2008."
        ),
    ),
    "Gilbert Voillemier": dict(
        status=MemberStatus.UNKNOWN,
        gang=None,
        set=None,
        biography=(
            "Manager of L'Apocalypse, the star nightclub of the island, south of Bastia, "
            "which Alain Delon had come to open. He was taken into custody in the October "
            "1986 crackdown, when a fifty-officer task force went after the Brise's "
            "revenue and searched the clubs one after another.\n\n"
            "One of the Voillemier family that recurs around the Brise: Jean-Jacques "
            "Voillemier flew to Siberia with Angelo Guazzelli and Francis Mariani in 1997 "
            "to discuss a casino, Guy Voillemier was picked up over the 1988 Pietralba "
            "van robbery, and their sister ran the Bastia branch of Crédit Agricole while "
            "Jean-Claude Guazzelli was its island director."
        ),
    ),
    "Bati Gentili": dict(
        status=MemberStatus.UNKNOWN,
        gang=None,
        set=None,
        biography=(
            "Born in Ajaccio, played for the GFCA and later coached them, then became "
            "head coach of Nantes. He is in this story for one disputed meeting.\n\n"
            "Christophe Guazzelli told Jacques Mariani that his oil-producing uncle "
            "Angelo Guazzelli, accompanied by the Brise de Mer's accountant Christian "
            "Leoni, had come to Nantes to speak to Gentili while Christophe was being "
            "dropped from training with the professionals to the reserves. Whether they "
            "were leaning on him, in the name of solidarity between Corsicans and of what "
            "those surnames can suggest, to get the boy the place he deserved, is exactly "
            "the question. By Christophe's account the meeting produced nothing. By Bati "
            "Gentili's account it never took place at all.\n\n"
            "No gang and no set: a football coach, recorded because the disagreement is "
            "part of the record."
        ),
    ),
}

FAMILY = [
    ("Jean-Claude Guazzelli", "brother", "François Guazzelli"),
    ("Jean-Claude Guazzelli", "brother", "Angelo Guazzelli"),
    ("Jean-Claude Guazzelli", "brother", "Paul-Louis Guazzelli"),
]

BUSINESSES = [
    (
        "Le Challenger",
        BusinessType.NIGHTLIFE,
        "L'Île-Rousse",
        BusinessStatus.ACTIVE,
        "Discothèque at L'Île-Rousse managed by Dominique Rutily and operated through a "
        "company called Le Forum. Targeted in the second wave of the 1986 financial "
        "crackdown, when the contractor who built it admitted invoicing far below the "
        "real cost at Rutily's request and handing back the six-hundred-thousand-euro "
        "difference in cash.",
        [("Dominique Rutily", BusinessRole.OWNER)],
    ),
    (
        "Cercle Wagram",
        BusinessType.GAMING,
        None,
        BusinessStatus.CLOSED,
        "A Paris gaming club, and one of the routes by which the money moved. Richard "
        "Casanova placed Michel Ferracci as its director of gaming, a strategic post from "
        "which to watch the till. Jean Casta was convicted in 2013 of moving between five "
        "and ten million euros out of its coffers to the Guazzelli family.",
        [("Michel Ferracci", BusinessRole.FRONT), ("Jean Casta", BusinessRole.BENEFICIARY)],
    ),
    (
        "Le G",
        BusinessType.NIGHTLIFE,
        "Ghisonaccia",
        BusinessStatus.CLOSED,
        "Nightclub on the route de la Mer at Ghisonaccia, run by Charles Fraticelli's son. "
        "The only discothèque in its micro-region and popular with summer tourists, it was "
        "destroyed by a bomb and the ensuing fire on the evening of 11 November 2008.",
        [],
    ),
]

INCIDENTS = [
    (
        "rutily-1996",
        IncidentType.MURDER,
        ym(1996, 3),
        None,
        "Car park of the stadium at Hyères, Var",
        "Dominique Rutily, Richard Casanova's binôme and president of the Football Club "
        "de Calvi, was assassinated in March 1996 as he left a match, on the car park of "
        "the stadium at Hyères in the Var. He was in the company of Rolland Courbis, then "
        "his friend and adviser, who is recorded here only as the man who was with him."
        "\n\n"
        "Outside Corsica, and no municipality, for the same reason as the Geneva job: the "
        "island's business was rarely confined to the island.",
        [("Dominique Rutily", ParticipantRole.VICTIM, ParticipantOutcome.KILLED)],
    ),
    (
        "vittini-2008",
        IncidentType.MURDER,
        ymd(2008, 7, 6),
        "Poggio-di-Venaco",
        "A clearing off the route nationale, near Poggio-di-Venaco",
        "Daniel Vittini, the Brise de Mer's man for the Corte region, was found face down "
        "on 6 July 2008 in a clearing two hundred metres from the route nationale, beside "
        "one of the cars belonging to his drinks distribution company. He had been "
        "executed with his back to the gunman, several bullets in the nape of the neck. "
        "Investigators called it Jean-Luc Germani's signature.\n\n"
        "Two days later Ange-Marie Michelosi was shot at Grosseto-Prugna. Eleven weeks "
        "earlier it had been Richard Casanova. In the south the Colonna succession was "
        "being wiped out over property, tourist infrastructure and public contracts; in "
        "the north the fratricidal war ran on.",
        [("Daniel Vittini", ParticipantRole.VICTIM, ParticipantOutcome.KILLED)],
    ),
    (
        "le-g-2008",
        IncidentType.BOMBING,
        ymd(2008, 11, 11),
        "Ghisonaccia",
        "Le G nightclub, route de la Mer, Ghisonaccia",
        "On the evening of 11 November 2008 the Le G nightclub at Ghisonaccia, run by the "
        "son of Francis Mariani's friend Charles Fraticelli, was completely destroyed by "
        "an explosion and the fire that followed. It was the only discothèque in its "
        "micro-region and busy with tourists in summer. Nobody is recorded as hurt.",
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
        sets = {
            x.name: x.id
            for x in (await s.execute(select(GangSet).where(GangSet.universe_id == uni))).scalars()
        }

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
                    date_of_death=d.get("date_of_death"),
                    gang_id=gangs[d["gang"]] if d.get("gang") else None,
                    affiliations=affs,
                ),
                actor,
            )
            mem[legal_name] = obj.id

        for who, rel, other in FAMILY:
            a = await existing(Member, legal_name=who)
            other_row = await existing(Member, legal_name=other)
            if a is None or other_row is None:
                continue
            fam = dict(a.family or {})
            ids = set(fam.get(rel) or [])
            if str(other_row.id) in ids:
                skipped.append(f"family {who} {rel} {other}")
                continue
            created.append(f"family {who} {rel} {other}")
            if dry:
                continue
            ids.add(str(other_row.id))
            fam[rel] = sorted(ids)
            await update_member(s, a.id, uni, MemberUpdate(family=fam))

        all_members = {
            m.legal_name: m.id
            for m in (await s.execute(select(Member).where(Member.universe_id == uni))).scalars()
        }
        all_members.update(mem)

        for name, btype, muni_name, status, desc, members in BUSINESSES:
            if await existing(Business, name=name):
                skipped.append(f"business {name}")
                continue
            created.append(f"business {name}")
            if dry:
                continue
            await create_business(
                s,
                BusinessCreate(
                    universe_id=uni,
                    name=name,
                    business_type=btype,
                    description=desc,
                    status=status,
                    municipality_id=muni.get(muni_name) if muni_name else None,
                    members=[
                        BusinessMemberIn(member_id=all_members[mn], role=r)
                        for mn, r in members
                        if mn in all_members
                    ],
                ),
                actor,
            )

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
                        ParticipantCreate(member_id=all_members[n], role=r, outcome=o)
                        for n, r, o in participants
                        if n in all_members
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
