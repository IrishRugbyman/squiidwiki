"""The people around the principals: drivers, bankers, brothers, wives, fixers.

Every phase so far seeded the men who shot each other. The book is full of the
ones who drove them, banked for them, married them and hid them, and they are
often the reason anything is known at all. Claude Chossat is named 26 times in
Vendetta, more than Pierre-Marie Santucci, and had no record here.

Ten people, found by extracting every capitalised name in the book, counting
them, and diffing against what was already seeded.

The nationalist overlay (Francois Santoni, Nicolas Montigny, the Marcelli
brothers, Charles Pieri, Alain and Guy Orsoni, Armata Corsa) is a coherent block
of its own and is deliberately not in this batch. Politicians, police and
magistrates who appear as context (Pasqua, Giacobbi, Marion, Squarcini, Legras)
are left out entirely: they are not members of anything, and the schema has no
way to say what they are.

**A schema limit worth knowing.** `INVERSE_REL` in app/crud/member.py runs
father/son/uncle/nephew/brother/cousin/spouse. There is no mother, daughter,
sister or in-law. So Sylvie Cappuri can be linked to Francis Guazzelli as his
spouse, but not to Richard and Christophe as their mother, because the only
parent relation is `father` and the inverse would assert she is one. Sandra
Germani cannot be linked to her brother for the same reason: `brother` inverts
to `brother`, which would make her Jean-Luc's brother. Both facts are in the
biographies instead.

Idempotent. Run from backend/:
  .venv/bin/python -m app.scripts.seed_corsica_inner_circle          # dry run
  .venv/bin/python -m app.scripts.seed_corsica_inner_circle --apply
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
)
from app.core.fuzzy_date import FuzzyDate
from app.crud.incident import create_incident
from app.crud.member import create_member, update_member
from app.crud.municipality import create_municipality
from app.models import Gang, GangSet, Incident, Member, Municipality
from app.schemas.incident import IncidentCreate, ParticipantCreate
from app.schemas.member import MemberCreate, MemberSetAffiliationIn, MemberUpdate
from app.schemas.municipality import MunicipalityCreate

BRISE, GERMANI = "Brise de Mer", "Clan Germani"


def ymd(y, m, d):
    return FuzzyDate(year=y, month=m, day=d, precision=DatePrecision.YMD)


def yr(y, approx=False):
    return FuzzyDate(year=y, precision=DatePrecision.Y, approx=approx)


MEMBERS = {
    "Claude Chossat": dict(
        status=MemberStatus.UNKNOWN,
        dob=yr(1978, approx=True),
        gang=BRISE,
        set=BRISE,
        from_date=yr(2000, approx=True),
        biography=(
            "Francis Mariani's driver and hired hand, and afterwards the first repenti "
            "the Brise de Mer ever produced. He is named more often in Vendetta than "
            "most of the men he worked for, because he is one of the few who talked.\n\n"
            "They met inside. Mariani was doing a short stretch at Borgo, where the "
            "saying that it is the inmates who watch the warders was never truer; "
            "Chossat was 22, a small-time crook convicted of robbing two elderly people "
            "in their own home, who liked rally driving and had papered his cell with "
            "posters of fast cars. Mariani fascinated him as much as he frightened him, "
            "and the association protected him inside, where it always pays to sit under "
            "the boss's authority.\n\n"
            "As Mariani's bodyguard he sat through a great many conversations, and much "
            "of what is known about the quarrel with Germani and Casanova comes from what "
            "he later recounted. He maintained that Bernard Squarcini had recruited "
            "Casanova as an informant."
        ),
    ),
    "Tony Patacchini": dict(
        status=MemberStatus.UNKNOWN,
        gang=BRISE,
        set=BRISE,
        from_date=yr(1995, approx=True),
        biography=(
            "The team's banker, and a defrocked notary, which is a useful combination in "
            "a group with that much cash and no way to explain it. Francis Mariani "
            "complained to him about the unrepaid African loan in the words that sum the "
            "whole quarrel up: 'Celui-là nous doit des sous' - Michel Tomi owes us "
            "money.\n\n"
            "After the 2001 attempt on Mariani's life he put him up in his own flat in "
            "the little rue Campi in central Ajaccio, which runs alongside the "
            "prefecture and the police station. He noticed his boss had changed "
            "physically, swollen, 'perhaps ill', and said so to police years afterwards "
            "in custody.\n\n"
            "Distinct from Joël and Jacques Patacchini, who were tried over the UBS "
            "robbery; the sources do not state how, or whether, they are related."
        ),
    ),
    "Angelo Guazzelli": dict(
        status=MemberStatus.UNKNOWN,
        aliases=["Jean-Angelo", "Olive"],
        gang=BRISE,
        set=BRISE,
        from_date=yr(1978, approx=True),
        biography=(
            "Known as Olive. Brother of Francis and Paul-Louis Guazzelli and one of the "
            "three of them at the bar on the old port.\n\n"
            "On 16 January 1997 he flew from Geneva to Kemerovo in Siberia, via Moscow, "
            "with Francis Mariani, Jean-Jacques Voillemier and three others, on the "
            "invitation of three Russians, to discuss opening a casino. An Interpol "
            "message that year alerted France to the presence of Brise members in "
            "Russia.\n\n"
            "He gave the answer the gang always gave. Asked by police whether he was a "
            "member, he lost his temper: the Brise de Mer was 'a journalistic invention "
            "by Parisian hacks to sell newsprint', and there was a political motive "
            "behind it, to run the island down. He went on the run after his brother was "
            "killed in 2009."
        ),
    ),
    "Paul-Louis Guazzelli": dict(
        status=MemberStatus.UNKNOWN,
        gang=BRISE,
        set=BRISE,
        from_date=yr(1978, approx=True),
        biography=(
            "The third of the Guazzelli brothers at the bar on the old port, with Francis "
            "and Jean-Angelo. Their father gave his occupation as farmer and their mother "
            "was a schoolteacher; a fourth brother took an entirely different path."
        ),
    ),
    "Sylvie Cappuri": dict(
        status=MemberStatus.UNKNOWN,
        gang=None,
        set=None,
        biography=(
            "Francis Guazzelli's partner and the mother of Richard, Christophe and a "
            "third son, Francis junior, born some years after them. A child of Bastia "
            "herself, she had known Francis and a good part of the Brise de Mer from "
            "school. Those who met her remember a discreet and unforgettable beauty, and "
            "a mother who was present and attentive.\n\n"
            "The family's life ran between a villa with an indoor pool at La Porta, the "
            "Guazzelli stronghold, and a bourgeois flat in Bastia. Her eldest was named "
            "Richard for Richard Casanova, who stood as his godfather; both men were "
            "shot dead within nineteen months of each other.\n\n"
            "Not a member of anything. She is here because the sons who carried the war "
            "into the next generation are hers, and because the schema's family relations "
            "have no way to record a mother."
        ),
    ),
    "Sandra Germani": dict(
        status=MemberStatus.UNKNOWN,
        gang=GERMANI,
        set=None,
        biography=(
            "Jean-Luc Germani's sister, described as a dark-haired woman with a "
            "mysterious face, and Richard Casanova's partner. That relationship is the "
            "join between the two camps: it made Germani Casanova's brother-in-law and "
            "pulled him into a story he had no other claim on.\n\n"
            "Investigators looking into Casanova's affairs found companies registered in "
            "her name, alongside others in the name of his father François Casanova. She "
            "was said to be financed by Michel Tomi.\n\n"
            "After Casanova was assassinated in April 2008, Jacques Mariani's fear was "
            "precisely that she would push her brother to avenge him, and so bring the "
            "Germani camp to war with the Mariani family. She is recorded against the "
            "Germani gang but no set: aligned with that camp rather than a made member "
            "of it. The sibling link cannot be stored, because the schema's only sibling "
            "relation is 'brother' and it inverts to itself."
        ),
    ),
    "Frédéric Federici": dict(
        status=MemberStatus.UNKNOWN,
        gang=GERMANI,
        set=GERMANI,
        from_date=yr(2000, approx=True),
        biography=(
            "One of the Federici brothers, the 'bergers-braqueurs' as the press called "
            "them, shepherd-robbers who ran the eastern plain. They were Jean-Luc "
            "Germani's childhood friends, met in the bar his mother kept at Arena on the "
            "Vescovato plain, where they came for a coffee, a beer or a game of cards, "
            "and they remained his backing.\n\n"
            "Francis Mariani counted the Federici clan among those he suspected after the "
            "attempt on his life. Convicted on 12 February 2016, with Germani, Jean-Luc "
            "Codaccioni, Antoine Quilichini and Stéphane Luciani, of criminal conspiracy "
            "in the assassination of Jean-Claude Colonna."
        ),
    ),
    "Robert Feliciaggi": dict(
        status=MemberStatus.DEAD,
        dob=yr(1943, approx=True),
        date_of_death=ymd(2006, 3, 10),
        aliases=["Bob l'Africain"],
        gang=None,
        set=None,
        biography=(
            "Known as Bob l'Africain. A cheerful, sociable man already doing business in "
            "Africa, in prawns among other things, and close to the Congolese president "
            "Denis Sassou-Nguesso. It was Feliciaggi who opened the continent to Michel "
            "Tomi, who brought the gaming expertise; both were close to another Corsican, "
            "Charles Pasqua, French interior minister in 1986 and again in 1993, and "
            "between them they built the African casino network through which so much of "
            "this money later moved.\n\n"
            "Assassinated at Ajaccio on 10 March 2006. Not a member of the Brise de Mer "
            "or of any clan: the money side of the story rather than the shooting side, "
            "which is why he has a gang of none."
        ),
    ),
    "Antoine Nivaggioni": dict(
        status=MemberStatus.UNKNOWN,
        gang=None,
        set=None,
        biography=(
            "A figure of the Ajaccio business world, close to the circle of the former "
            "nationalist leader Alain Orsoni, whose people had held the southern chamber "
            "of commerce since Charles Pasqua handed them the purse strings in a "
            "political arrangement. Jean-Luc Germani attended a meeting with Orsoni's "
            "associates including Nivaggioni, held on the premises of an influential "
            "Ajaccio merchant; the gendarmes noted the purpose was unknown but might "
            "relate to threats made in the race for the chamber's presidency.\n\n"
            "Francis Mariani named him among those he suspected after the attempt on his "
            "life."
        ),
    ),
    "Rachid Si Larbi": dict(
        status=MemberStatus.UNKNOWN,
        gang=None,
        set=None,
        biography=(
            "Fifteen years older than Christophe Guazzelli, whom he met on football "
            "pitches in Paris, where he presented himself as an agent. He was never "
            "registered as one, but let the doubt stand while shaking hands warmly with "
            "promising young players.\n\n"
            "One of those figures found equally in the VIP boxes of football grounds, the "
            "smart brasseries of the 8th arrondissement and celebrity parties: "
            "facilitator, intermediary, public-relations man, luxury concierge, a little "
            "of all of it or none. Officially, in the early 2010s, he ran a small car "
            "business.\n\n"
            "He had done favours for Francis Guazzelli in Paris, stayed in contact with "
            "Angelo Guazzelli including during his time on the run after 2009, and after "
            "the father's death made himself indispensable to Christophe and close to "
            "his mother Sylvie Cappuri. Nobody at the Nantes club quite understood why: "
            "Christophe was not a professional player and had no money to bring him."
        ),
    ),
}

# Only relations the schema can express correctly. See the module docstring.
FAMILY = [
    ("François Guazzelli", "brother", "Angelo Guazzelli"),
    ("François Guazzelli", "brother", "Paul-Louis Guazzelli"),
    ("Angelo Guazzelli", "brother", "Paul-Louis Guazzelli"),
    ("François Guazzelli", "spouse", "Sylvie Cappuri"),
]

FELICIAGGI_INCIDENT = (
    "feliciaggi-2006",
    IncidentType.MURDER,
    ymd(2006, 3, 10),
    "Ajaccio",
    "Ajaccio",
    "Robert Feliciaggi, known as Bob l'Africain, was assassinated at Ajaccio on 10 "
    "March 2006. He was the man who had opened Africa to Michel Tomi and, with him and "
    "Charles Pasqua, built the casino network that carried the island's money. His "
    "killing came eight months before Jean-Jé Colonna died at the wheel and two years "
    "before Richard Casanova was shot, at the front of the sequence in which the old "
    "arrangements came apart.",
    [("Robert Feliciaggi", ParticipantRole.VICTIM, ParticipantOutcome.KILLED)],
)


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

        gangs = {
            g.name: g.id
            for g in (await s.execute(select(Gang).where(Gang.universe_id == uni))).scalars()
        }
        sets = {
            x.name: x.id
            for x in (await s.execute(select(GangSet).where(GangSet.universe_id == uni))).scalars()
        }
        muni = {
            m.name: m.id
            for m in (
                await s.execute(select(Municipality).where(Municipality.universe_id == uni))
            ).scalars()
        }
        if "Ajaccio" not in muni:
            muni["Ajaccio"] = (
                await create_municipality(
                    s, MunicipalityCreate(universe_id=uni, name="Ajaccio"), actor
                )
            ).id

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
                    aliases=d.get("aliases"),
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

        for who, rel, other in FAMILY:
            a = await existing(Member, legal_name=who)
            b_id = mem.get(other) or getattr(await existing(Member, legal_name=other), "id", None)
            if a is None or b_id is None:
                continue
            fam = dict(a.family or {})
            ids = set(fam.get(rel) or [])
            if str(b_id) in ids:
                skipped.append(f"family {who} {rel} {other}")
                continue
            created.append(f"family {who} {rel} {other}")
            if dry:
                continue
            ids.add(str(b_id))
            fam[rel] = sorted(ids)
            await update_member(s, a.id, uni, MemberUpdate(family=fam))

        key, itype, date, muni_name, location, narrative, participants = FELICIAGGI_INCIDENT
        sortable = date.to_sortable_date()
        if await existing(Incident, type=itype, sortable_date=sortable):
            skipped.append(f"incident {key}")
        else:
            created.append(f"incident {key}")
            if not dry:
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
