"""Create the clan structure the Brise de Mer split into, and place its members.

Phase 2 deliberately left this out for want of sourcing. The book does settle
it, in terms it uses repeatedly: "la guerre entre les deux clans".

Two camps, and they are not symmetrical:

- **Clan Mariani.** The heirs who stayed. Vendetta calls Francis Guazzelli and
  Pierre-Marie Santucci "les derniers fidèles de Francis Mariani", and has
  Jacques Mariani fearing that Sandra Germani would "pousser son frère Jean-Luc
  à venger la mort de Richard Casanova, et donc à entrer en guerre avec la
  famille Mariani". A set under the Brise de Mer gang: this is the Brise
  continuing under another name.

- **Clan Germani.** Its own gang, NOT a Brise set, on the book's explicit
  statement that Jean-Luc Germani "est un electron libre dans le paysage du
  grand banditisme corse, il n'appartient ni a la Brise ni a aucun clan". He
  became Richard Casanova's brother-in-law when Casanova took up with his
  sister Sandra, and Christophe Guazzelli was later asked in interview about
  "votre vengeance contre le 'clan' Germani".

Richard Casanova is the hinge and is modelled as such: a Brise founder whose
Brise affiliation stays primary, plus a second, secondary spell in Clan Germani
from around 2006. The sources have him drifting into that camp rather than
formally resigning from the Brise, and the affiliation model is built to say
exactly that.

Deferred, still unsourced enough to matter: Codaccioni, Quilichini, Luciani and
Federici on the Germani side, and "le clan des orphelins" (the sons: Christophe
and Richard Guazzelli, Jacques Mariani, Ange-Marie Michelosi junior), which is
a third generation and belongs with the Corse-du-Sud phase.

Idempotent. Run from backend/:
  .venv/bin/python -m app.scripts.seed_corsica_clans          # dry run
  .venv/bin/python -m app.scripts.seed_corsica_clans --apply
"""

import argparse
import asyncio
import sys
import uuid

from sqlalchemy import select, text

from app.core.database import _session_factories
from app.core.enums import DatePrecision, MemberStatus, SetRelationshipType, SetStatus
from app.core.fuzzy_date import FuzzyDate
from app.crud.gang import create_gang
from app.crud.gang_set import create_gang_set
from app.crud.member import create_member, update_member
from app.models import Gang, GangSet, Member, MemberSet, SetRelationship
from app.schemas.gang import GangCreate
from app.schemas.gang_set import SetCreate
from app.schemas.member import MemberCreate, MemberSetAffiliationIn, MemberUpdate

UNIVERSE_SLUG = "corsica"
BRISE = "Brise de Mer"
MARIANI = "Clan Mariani"
GERMANI = "Clan Germani"


def yr(y, approx=False):
    return FuzzyDate(year=y, precision=DatePrecision.Y, approx=approx)


# member -> (set name, from_date, why)
PLACEMENTS = [
    (
        "Francis Mariani",
        MARIANI,
        yr(2008, approx=True),
        "The clan is his; the war is fought over his succession.",
    ),
    (
        "Jacques Mariani",
        MARIANI,
        yr(2008, approx=True),
        "His son. The book speaks of a war against 'la famille Mariani'.",
    ),
    (
        "François Guazzelli",
        MARIANI,
        yr(2008, approx=True),
        "One of the two men Vendetta calls 'les derniers fidèles de Francis Mariani'.",
    ),
    (
        "Pierre-Marie Santucci",
        MARIANI,
        yr(2008, approx=True),
        "The other of the two 'derniers fidèles'; carried Mariani's coffin and was "
        "dead four weeks later.",
    ),
    (
        "Maurice Costa",
        MARIANI,
        yr(2008, approx=True),
        "Weaker than the other four: placed here on his long association with Mariani "
        "and Santucci, arrested with them at Sartène in 2000 and freed with them by the "
        "forged fax in 2001, rather than on any statement about the clan war itself.",
    ),
    (
        "Richard Casanova",
        GERMANI,
        yr(2006, approx=True),
        "Secondary to his Brise affiliation, which stays primary. The sources have him "
        "drifting into Germani's orbit after becoming his brother-in-law, not resigning "
        "from the Brise.",
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

        brise_gang = await existing(Gang, name=BRISE)
        muni = {
            r[1]: r[0]
            for r in (
                await s.execute(
                    text("SELECT id, name FROM municipality WHERE universe_id = :u"), {"u": uni}
                )
            ).all()
        }
        if brise_gang is None:
            print("Phase 1 must be seeded first", file=sys.stderr)
            return 1

        # --- Clan Germani is its own gang, not a Brise set ------------------
        germani_gang = await existing(Gang, name=GERMANI)
        if germani_gang:
            skipped.append(f"gang {GERMANI}")
            germani_gang_id = germani_gang.id
        else:
            created.append(f"gang {GERMANI}")
            germani_gang_id = uuid.uuid4()
            if not dry:
                obj = await create_gang(
                    s,
                    GangCreate(
                        universe_id=uni,
                        name=GERMANI,
                        description=(
                            "Not a branch of the Brise de Mer but a rival formation around "
                            "Jean-Luc Germani, who belonged to neither the Brise nor any "
                            "clan before Richard Casanova, drifting away from the Brise, "
                            "became his brother-in-law. Germani could also call on his "
                            "childhood friends the Federici brothers, the 'bergers-braqueurs' "
                            "of the eastern plain. The camp that fought the Mariani family "
                            "after Casanova's assassination in April 2008."
                        ),
                    ),
                    actor,
                )
                germani_gang_id = obj.id

        # --- the two clan sets ----------------------------------------------
        sets: dict[str, uuid.UUID] = {}
        for name, gang_id, muni_name, bio in [
            (
                MARIANI,
                brise_gang.id,
                "Bastia",
                "The Brise de Mer continuing under another name: the heirs who stayed with "
                "Francis Mariani when Richard Casanova drifted off. Vendetta calls Francis "
                "Guazzelli and Pierre-Marie Santucci 'les derniers fidèles de Francis "
                "Mariani', and the war of 2008-2012 is fought over the Mariani succession.",
            ),
            (
                GERMANI,
                germani_gang_id,
                "Vescovato",
                "Jean-Luc Germani's camp. He grew up around the bar his mother kept at "
                "Arena, in the plain of Vescovato, where the Federici brothers drank. "
                "Formed against the Mariani family in revenge for Richard Casanova.",
            ),
        ]:
            found = await existing(GangSet, name=name)
            if found:
                sets[name] = found.id
                skipped.append(f"set {name}")
                continue
            created.append(f"set {name}")
            if dry:
                sets[name] = uuid.uuid4()
                continue
            obj = await create_gang_set(
                s,
                SetCreate(
                    universe_id=uni,
                    name=name,
                    bio=bio,
                    status=SetStatus.ACTIVE,
                    gang_id=gang_id,
                    municipality_id=muni.get(muni_name),
                ),
                actor,
            )
            sets[name] = obj.id

        # --- Jean-Luc Germani himself ---------------------------------------
        germani = await existing(Member, legal_name="Jean-Luc Germani")
        if germani:
            skipped.append("member Jean-Luc Germani")
        else:
            created.append("member Jean-Luc Germani")
            if not dry:
                await create_member(
                    s,
                    MemberCreate(
                        universe_id=uni,
                        legal_name="Jean-Luc Germani",
                        status=MemberStatus.LOCKED,
                        gang_id=germani_gang_id,
                        affiliations=[
                            MemberSetAffiliationIn(
                                set_id=sets[GERMANI], is_primary=True, from_date=yr(2001, True)
                            )
                        ],
                        biography=(
                            "A free electron in the Corsican underworld, belonging to neither "
                            "the Brise de Mer nor any clan, and mistrusted accordingly: the "
                            "young man was said to fear nothing. He became Richard Casanova's "
                            "brother-in-law when Casanova took up with his sister Sandra.\n\n"
                            "He grew up around the bar his mother kept at Arena, a hamlet on "
                            "the Vescovato plain crossed by the route nationale, where the "
                            "Federici brothers, the 'bergers-braqueurs' who ran the eastern "
                            "plain, came for a coffee or a game of cards. They remained his "
                            "childhood friends and his backing. He had also taken part in "
                            "jobs with Brise de Mer men, including a security-van robbery at "
                            "Saint-Laurent-du-Var alongside Jacques Mariani.\n\n"
                            "He and Francis Mariani fell out over an African loan and over "
                            "investments in bars and clubs around Aix-en-Provence, in "
                            "particular Le Bliss. Mariani came to believe Germani was behind "
                            "the 2001 attempt on his life, and suspicion of Germani hardened "
                            "into an obsession. After Casanova's assassination in April 2008 "
                            "his camp and the Mariani family went to war.\n\n"
                            "Arrested in the Hauts-de-Seine on 27 November 2014 after more "
                            "than three and a half years on the run, and convicted on 12 "
                            "February 2016 of criminal conspiracy in the Jean-Claude Colonna "
                            "case."
                        ),
                    ),
                    actor,
                )

        # --- place the existing members --------------------------------------
        # _sync_member_sets replaces every *open* spell, so each member's current
        # affiliations have to be read and passed back or they are deleted.
        for legal_name, set_name, from_date, _why in PLACEMENTS:
            m = await existing(Member, legal_name=legal_name)
            if m is None:
                print(f"  ! no member {legal_name!r}", file=sys.stderr)
                continue
            open_spells = (
                (
                    await s.execute(
                        select(MemberSet).where(
                            MemberSet.member_id == m.id, MemberSet.until_date.is_(None)
                        )
                    )
                )
                .scalars()
                .all()
            )
            if any(sp.set_id == sets[set_name] for sp in open_spells):
                skipped.append(f"{legal_name} -> {set_name}")
                continue
            created.append(f"{legal_name} -> {set_name}")
            if dry:
                continue
            affiliations = [
                MemberSetAffiliationIn(
                    set_id=sp.set_id,
                    rank=sp.rank,
                    is_primary=sp.is_primary,
                    from_date=sp.from_date,
                )
                for sp in open_spells
            ]
            affiliations.append(
                MemberSetAffiliationIn(set_id=sets[set_name], is_primary=False, from_date=from_date)
            )
            await update_member(s, m.id, uni, MemberUpdate(affiliations=affiliations))

        # --- the war itself ---------------------------------------------------
        a, b = sorted([sets[MARIANI], sets[GERMANI]])
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
            skipped.append(f"relationship {MARIANI} <-> {GERMANI}")
        else:
            created.append(f"relationship {MARIANI} <-> {GERMANI} (ENEMY, from 2008)")
            if not dry:
                s.add(
                    SetRelationship(
                        set_a_id=a,
                        set_b_id=b,
                        relationship_type=SetRelationshipType.ENEMY,
                        from_date=yr(2008).model_dump(mode="json"),
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
