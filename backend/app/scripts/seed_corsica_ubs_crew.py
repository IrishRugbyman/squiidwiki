"""The rest of the UBS crew, and Alexandre Chevrière.

The robbery seeder put Richard Casanova on the Geneva job alone, because the
index of Vendetta names only him. The chapter names the whole team, and one of
them matters as much as Casanova does: Alexandre Chevrière, the Marseille friend
and hired hand of the Bastia men, who was assassinated three days after the
hearings at his own trial for the robbery.

It also produces the cleanest use of the acquitted flag in this universe. At the
Paris assizes in June 2004, more than ten years after the job, the Swiss inside
man refused to testify and **everyone was acquitted**. Casanova was on the run
and was never tried at all. So three participants carry acquitted=True and one
does not, and the difference is real: a court cleared the first three, and never
heard the fourth.

Rewrites the UBS narrative too, which was thin: the inside man, the method, and
how the case fell apart.

Idempotent. Run from backend/:
  .venv/bin/python -m app.scripts.seed_corsica_ubs_crew          # dry run
  .venv/bin/python -m app.scripts.seed_corsica_ubs_crew --apply
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
from app.crud.incident import create_incident, update_incident
from app.crud.member import create_member
from app.models import GangSet, Incident, Member
from app.schemas.incident import IncidentCreate, IncidentUpdate, ParticipantCreate
from app.schemas.member import MemberCreate, MemberSetAffiliationIn

BRISE = "Brise de Mer"


def ym(y, m):
    return FuzzyDate(year=y, month=m, precision=DatePrecision.YM)


def yr(y, approx=False):
    return FuzzyDate(year=y, precision=DatePrecision.Y, approx=approx)


MEMBERS = {
    "Alexandre Chevrière": dict(
        status=MemberStatus.DEAD,
        date_of_death=ym(2004, 6),
        in_brise=yr(1988, approx=True),
        biography=(
            "The Marseille friend and hired hand of the Bastia men, and one of the "
            "protagonists of the Union des Banques Suisses robbery in Geneva on 25 March "
            "1990. Not a founder of the Brise de Mer but one of its mainland supports, "
            "which is how the sources describe him.\n\n"
            "He was among those taken at Sartène on 5 July 2000, in the sweep that also "
            "caught Francis Mariani, Pierre-Marie Santucci and Maurice Costa, and from "
            "which Richard Casanova escaped over a low wall, abandoning a rucksack that "
            "held an automatic pistol, balaclavas, gloves, a walkie-talkie, keys to "
            "stolen cars and his DNA.\n\n"
            "Tried for the UBS robbery at the Paris assizes in June 2004 and acquitted "
            "with everyone else, after the Swiss inside man refused to appear. He was "
            "assassinated three days after the hearings ended. The sources give the "
            "sequence but not the date or the place, so his death is recorded here to "
            "the month."
        ),
    ),
    "Joël Patacchini": dict(
        status=MemberStatus.UNKNOWN,
        in_brise=yr(1985, approx=True),
        biography=(
            "Close to members of the Brise de Mer and one of the men suspected over the "
            "UBS robbery in Geneva, for which he was acquitted at Paris in June 2004.\n\n"
            "He had been picked up earlier, in 1988, over the robbery of a security van "
            "at Pietralba in Corsica, alongside Francis Santucci, Christian Leoni and "
            "Guy Voillemier. The haul was modest, a hundred and eighty thousand francs, "
            "but the arrests took in what the police regarded as the best of the Brise."
        ),
    ),
    "Jacques Patacchini": dict(
        status=MemberStatus.UNKNOWN,
        in_brise=yr(1985, approx=True),
        biography=(
            "Close to members of the Brise de Mer and, with his brother Joël, among the "
            "men suspected over the Union des Banques Suisses robbery in Geneva in March "
            "1990. Acquitted with the rest at the Paris assizes in June 2004."
        ),
    ),
    "Michel Ferrari": dict(
        status=MemberStatus.UNKNOWN,
        in_brise=None,
        biography=(
            "The Swiss accomplice on the inside of the UBS robbery, and the reason there "
            "was a case at all. Arrested afterwards and, on his own account, never paid "
            "what the Corsicans had promised him, he informed on them.\n\n"
            "His evidence was the whole of the prosecution and it did not hold. There "
            "was no physical evidence against the Bastia men beyond a few trips to "
            "Geneva in the weeks before the robbery, the team that met Ferrari was not "
            "necessarily the team that carried it out, and he recognised some of them "
            "but not all. At the trial in June 2004 he refused to come and testify at "
            "all, and everyone walked.\n\n"
            "Not a member of the Brise de Mer or of anything else: an inside man who was "
            "used and, he says, cheated."
        ),
    ),
}

UBS_NARRATIVE = (
    "The best-known job attributed to the Brise de Mer, and the one the press called "
    "the robbery of the century. On 25 March 1990 the Union des Banques Suisses in "
    "Geneva was emptied of a sum the sources give as 120 million francs in the "
    "narrative and 125 million, about 19 million euros, in the chronology. Not a "
    "centime of it was ever recovered. It went on funding businesses in Corsica and "
    "casinos in Africa, and, in the book's phrase, feeding the widows and orphans of "
    "the men later shot by brothers turned enemies.\n\n"
    "There was an inside man: the husband of the personal secretary of one of the "
    "bank's directors. The robbers jumped the gate, put a gun to the guards' temples, "
    "emptied the vaults with codes they already had, and drove away unhurried with more "
    "than two hundred kilos of banknotes.\n\n"
    "The men suspected were Richard Casanova, then 33 and considered the brain of the "
    "operation, the brothers Joël and Jacques Patacchini, and Alexandre Chevrière, the "
    "Marseille friend and hired hand of the Bastia men. The Swiss accomplice Michel "
    "Ferrari was arrested, said he had never been paid what he was promised, and "
    "informed on them. It was not enough: no physical evidence beyond a few trips to "
    "Geneva beforehand, the team that met Ferrari was not necessarily the team that did "
    "the job, and he recognised some faces but not all. The accused had solid alibis, as "
    "usual.\n\n"
    "The case reached the Paris assizes in June 2004, more than ten years late. Ferrari "
    "refused to testify. The prosecution's only working part seized, and everyone was "
    "acquitted. Casanova was on the run at the time and was never tried. Three days "
    "after the hearings ended, Alexandre Chevrière was assassinated."
)

CHEVRIERE_INCIDENT = (
    "chevriere-2004",
    IncidentType.MURDER,
    ym(2004, 6),
    "Alexandre Chevrière was assassinated three days after the hearings ended at the "
    "Paris assizes, where he and the rest of the UBS crew had just been acquitted of the "
    "1990 Geneva robbery. The sources give the sequence and nothing else: no date, no "
    "place, no suspect. The proximity is the whole of what is recorded, and the book "
    "leaves it there.",
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

        brise = await existing(GangSet, name=BRISE)
        gang_row = (
            await s.execute(
                text("SELECT id FROM gang WHERE universe_id=:u AND name=:n"),
                {"u": uni, "n": BRISE},
            )
        ).first()

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
            if d.get("in_brise") is not None:
                affs = [
                    MemberSetAffiliationIn(
                        set_id=brise.id, is_primary=True, from_date=d["in_brise"]
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
                    gang_id=gang_row[0] if d.get("in_brise") is not None else None,
                    affiliations=affs,
                ),
                actor,
            )
            mem[legal_name] = obj.id

        # --- the UBS incident gains its real cast and narrative ---------------
        ubs = (
            (
                await s.execute(
                    select(Incident).where(
                        Incident.universe_id == uni,
                        Incident.type == IncidentType.ROBBERY,
                        Incident.sortable_date
                        == FuzzyDate(
                            year=1990, month=3, day=25, precision=DatePrecision.YMD
                        ).to_sortable_date(),
                    )
                )
            )
            .scalars()
            .first()
        )
        if ubs is None:
            print("UBS incident not found; run seed_corsica_robberies first")
            return 1

        casanova = await existing(Member, legal_name="Richard Casanova")
        # Acquitted at Paris in June 2004; Casanova was on the run and never tried,
        # so he is the one man here the flag must NOT be set on.
        wanted = [
            (
                casanova.id,
                False,
                "Presumed mastermind, 'cerveau présumé' in the sources, and 33 at the "
                "time. On the run when the case came to trial in June 2004, so unlike "
                "his co-accused he was never tried for it at all.",
            ),
            (
                mem.get("Alexandre Chevrière"),
                True,
                "The Marseille hired hand of the Bastia men. Acquitted at the Paris "
                "assizes in June 2004, and assassinated three days after the hearings.",
            ),
            (
                mem.get("Joël Patacchini"),
                True,
                "Acquitted at the Paris assizes in June 2004.",
            ),
            (
                mem.get("Jacques Patacchini"),
                True,
                "Acquitted at the Paris assizes in June 2004.",
            ),
            (
                mem.get("Michel Ferrari"),
                False,
                "The inside man, not one of the robbers: the husband of a bank "
                "director's secretary supplied the access, Ferrari supplied the rest. "
                "Arrested, unpaid by his own account, he informed on the others and then "
                "refused to testify at their trial.",
            ),
        ]
        current = (
            await s.execute(
                text("SELECT count(*) FROM incident_participant WHERE incident_id=:i"),
                {"i": ubs.id},
            )
        ).scalar()
        if current >= len(wanted) and ubs.narrative == UBS_NARRATIVE:
            skipped.append("UBS incident cast + narrative")
        else:
            created.append("UBS incident: full cast (3 acquitted, 1 never tried) + narrative")
            if not dry:
                await update_incident(
                    s,
                    ubs.id,
                    uni,
                    IncidentUpdate(
                        narrative=UBS_NARRATIVE,
                        participants=[
                            ParticipantCreate(
                                member_id=mid,
                                role=(
                                    ParticipantRole.ASSISTED
                                    if note.startswith("The inside man")
                                    else ParticipantRole.SHOOTER
                                ),
                                outcome=ParticipantOutcome.UNHARMED,
                                acquitted=acq,
                                notes=note,
                            )
                            for mid, acq, note in wanted
                            if mid is not None
                        ],
                    ),
                )

        # --- Chevrière's killing ----------------------------------------------
        key, itype, date, narrative = CHEVRIERE_INCIDENT
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
                        narrative=narrative,
                        participants=(
                            [
                                ParticipantCreate(
                                    member_id=mem["Alexandre Chevrière"],
                                    role=ParticipantRole.VICTIM,
                                    outcome=ParticipantOutcome.KILLED,
                                )
                            ]
                            if "Alexandre Chevrière" in mem
                            else []
                        ),
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
