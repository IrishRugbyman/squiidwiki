"""Link every existing prison spell to the court case its court file names.

The one-off backfill for court cases, phase 3. New spells are linked when they
are written (app.services.court_case_links); this walks the ones written
before that, oldest first, with the same rule: a federal docket always makes a
case, a state court file only when it is notable (a homicide or assault count,
or a second defendant). A spell whose case text names no court and docket is
reported and left alone, as is one already linked.

The writes are audited as claude-admin, so the audit log tells them from a
person's.

Run from backend/:
  $PY -m app.scripts.link_spells_to_cases              # dry run against prod
  $PY -m app.scripts.link_spells_to_cases --db test    # dry run against test
  $PY -m app.scripts.link_spells_to_cases --go         # write
"""

import argparse
import asyncio
import sys
from collections import Counter

from sqlmodel import select

from app.core.audit import attach_audit_listeners, current_user_id
from app.core.database import _session_factories
from app.models.auth import User
from app.models.member import MemberIncarceration
from app.services.court_case_links import link_spell

ACTOR = "claude-admin@squiidwiki.dev"


async def run(db: str, go: bool) -> int:
    # The app attaches these at startup; a script has to, or its writes leave no
    # audit trail (the first prod run did not, and its rows were logged after).
    attach_audit_listeners()
    async with _session_factories[db]() as s:
        actor = (await s.execute(select(User.id).where(User.email == ACTOR))).scalar_one_or_none()
        current_user_id.set(actor)
        spells = (
            (
                await s.execute(
                    select(MemberIncarceration)
                    .where(
                        MemberIncarceration.case_id.is_not(None),
                        MemberIncarceration.case_id != "",
                        MemberIncarceration.court_case_id.is_(None),
                    )
                    .order_by(MemberIncarceration.created_at)
                )
            )
            .scalars()
            .all()
        )
        outcomes: Counter[str] = Counter()
        skipped: Counter[tuple[str, str]] = Counter()
        created: dict[str, str] = {}
        for spell in spells:
            result = await link_spell(s, spell)
            outcomes[result.outcome] += 1
            if result.outcome == "skipped":
                skipped[(result.reason, spell.case_id or "")] += 1
            elif result.outcome == "created" and result.case is not None:
                created[str(result.case.id)] = (
                    f"{result.case.court} {result.case.docket}  {result.case.name}"
                )

        print(f"{len(spells)} spells without a case link in {db}")
        print(
            f"  linked to a case already on file or made earlier in this run: {outcomes['linked']}"
        )
        print(f"  made a new case: {outcomes['created']}")
        print(f"  left alone: {outcomes['skipped']}")
        print(f"\n{len(created)} cases created:")
        for line in sorted(created.values()):
            print(f"  {line}")
        unplaced = {k: n for k, n in skipped.items() if k[0] != "state court file, not notable"}
        print(f"\nleft alone, case text not placeable ({sum(unplaced.values())} spells):")
        for (reason, text), n in sorted(unplaced.items()):
            print(f"  {n:3}  {text!r}  ({reason})")
        print(
            f"\nleft alone as ordinary state files: "
            f"{sum(n for k, n in skipped.items() if k[0] == 'state court file, not notable')} spells"
        )
        if go:
            await s.commit()
            print("\nwritten")
        else:
            await s.rollback()
            print("\ndry run, nothing written; pass --go to write")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Link existing spells to their court cases.")
    ap.add_argument("--db", choices=sorted(_session_factories), default="prod")
    ap.add_argument("--go", action="store_true", help="write the changes")
    args = ap.parse_args()
    return asyncio.run(run(args.db, args.go))


if __name__ == "__main__":
    sys.exit(main())
