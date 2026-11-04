"""Delete the duplicate prison spells that repeated OTIS imports left behind.

Before 2026-11-04 the member form decided which OTIS sentences were already on
file from a cached list of the member's spells that the import itself never
refreshed, so importing the same profile again within the cache's five minutes
posted every sentence a second time (see `import_member_incarcerations` in
`app/crud/member.py`, which now decides on the server). This removes what that
left: rows of one member with the same court file, first notes line ("Offense:
..."), start and end date (`incarceration_match_key`).

**Which rows are extras.** The database alone cannot tell a repeated import from
two genuinely identical counts: OTIS lists a row per count, and three felony-
firearm counts on one file are three sentences that read the same. What does
tell them apart is *when* they were written. One import posts all its sentences
within seconds, so a member's spells are split into import batches (a new batch
starts after a gap longer than `--batch-gap` seconds), and the number of copies a
sentence legitimately has is the most any single batch holds. Copies beyond that
are extras. The oldest copies are kept, so the row that hand edits and case links
were made against survives.

That rule can be wrong in two directions, and both are reported, never guessed:

- two imports inside one batch gap (a double click on Save) look like one import
  with doubled counts and are kept: the "kept more than one" list names them, and
  `--keep-one` collapses every group to a single row once someone has checked
  OTIS;
- a group whose copies differ in anything besides the match key (facility,
  release dates, later notes lines, life flag, a case link that disagrees) is
  left alone and listed, because deleting a copy would delete what only it holds.
  A copy that carries a case link the kept row lacks is not a difference: the
  link moves to the kept row.

**What references a spell.** No foreign key points at `member_incarceration`
(checked at run time; the run aborts if one appears). Court-case defendant rows
reference the member and the case, not the spell, and `merge_charge` already
folded the duplicate counts into one charge, so they need nothing. The table is
not in the audit listeners' set, so each deletion is written to `audit_log` by
hand, as a DELETE with the whole row, attributed to claude-admin; `--go` also
writes the deleted rows to a JSON backup file.

Run from backend/:
  $PY -m app.scripts.dedupe_incarcerations                 # dry run against prod
  $PY -m app.scripts.dedupe_incarcerations --db test       # dry run against test
  $PY -m app.scripts.dedupe_incarcerations --db test --go  # write
Options: --batch-gap SECONDS (default 120), --keep-one, --backup PATH.
"""

import argparse
import asyncio
import datetime
import json
import sys
from collections import Counter, defaultdict

from sqlalchemy import text
from sqlmodel import select

from app.core.audit import _json_safe, current_user_id
from app.core.database import _session_factories
from app.core.enums import AuditAction
from app.crud.member import incarceration_match_key
from app.models.auth import AuditLog, User
from app.models.member import MemberIncarceration

ACTOR = "claude-admin@squiidwiki.dev"

# Fields outside the match key that must agree before a copy may go.
_MUST_AGREE = (
    "notes",
    "facility",
    "earliest_release_date",
    "max_discharge_date",
    "life_sentence",
)


def _key(s: MemberIncarceration) -> tuple:
    return incarceration_match_key(s.case_id, s.notes, s.from_date, s.to_date)


def _snapshot(s: MemberIncarceration) -> dict:
    return {c.key: _json_safe(getattr(s, c.key)) for c in MemberIncarceration.__mapper__.columns}


def _batches(spells: list[MemberIncarceration], gap: float) -> list[int]:
    """The import batch of each spell (same order as `spells`, sorted by created_at)."""
    out: list[int] = []
    batch = 0
    prev = None
    for s in spells:
        if prev is not None and (s.created_at - prev).total_seconds() > gap:
            batch += 1
        out.append(batch)
        prev = s.created_at
    return out


def plan(
    spells: list[MemberIncarceration], gap: float, keep_one: bool
) -> tuple[list[tuple[MemberIncarceration, MemberIncarceration]], list[dict], list[dict]]:
    """Decide what to delete.

    Returns (deletions as (extra, kept) pairs, groups kept with more than one
    row, groups skipped because their copies differ).
    """
    by_member: dict = defaultdict(list)
    for s in spells:
        by_member[s.member_id].append(s)

    deletions: list[tuple[MemberIncarceration, MemberIncarceration]] = []
    multi: list[dict] = []
    differing: list[dict] = []
    for member_id, rows in by_member.items():
        rows.sort(key=lambda s: (s.created_at, str(s.id)))
        batch_of = dict(zip((s.id for s in rows), _batches(rows, gap), strict=True))
        groups: dict = defaultdict(list)
        for s in rows:
            groups[_key(s)].append(s)
        for key, group in groups.items():
            if len(group) < 2:
                continue
            per_batch = Counter(batch_of[s.id] for s in group)
            legit = 1 if keep_one else max(per_batch.values())
            info = {
                "member_id": str(member_id),
                "case_id": key[0],
                "offense": key[1],
                "rows": len(group),
                "batches": len(per_batch),
                "keep": legit,
            }
            if legit >= len(group):
                multi.append(info)
                continue
            kept, extras = group[:legit], group[legit:]
            ref = kept[0]
            links = {s.court_case_id for s in group if s.court_case_id is not None}
            fields = [f for f in _MUST_AGREE if len({repr(getattr(s, f)) for s in group}) > 1]
            if fields or len(links) > 1:
                differing.append(
                    {**info, "differs_in": fields + (["court_case_id"] if len(links) > 1 else [])}
                )
                continue
            if legit > 1:
                multi.append(info)
            deletions.extend((e, ref) for e in extras)
    return deletions, multi, differing


async def _check_no_references(s) -> None:
    rows = (
        await s.execute(
            text(
                "select conrelid::regclass::text, conname from pg_constraint "
                "where confrelid = 'member_incarceration'::regclass"
            )
        )
    ).all()
    if rows:
        raise SystemExit(
            "foreign keys now reference member_incarceration; teach this script about them first: "
            + ", ".join(f"{t}.{c}" for t, c in rows)
        )


async def run(db: str, go: bool, gap: float, keep_one: bool, backup: str | None) -> int:
    async with _session_factories[db]() as s:
        await _check_no_references(s)
        actor = (await s.execute(select(User.id).where(User.email == ACTOR))).scalar_one_or_none()
        current_user_id.set(actor)
        spells = list((await s.execute(select(MemberIncarceration))).scalars().all())
        deletions, multi, differing = plan(spells, gap, keep_one)

        groups = {(str(e.member_id), _key(e)) for e, _ in deletions}
        print(f"{len(spells)} spells in {db}")
        print(f"  {len(deletions)} extra rows to delete, in {len(groups)} duplicate groups")
        relinked = 0
        for extra, kept in deletions:
            print(
                f"  delete {extra.id} (written {extra.created_at:%Y-%m-%d %H:%M:%S}), "
                f"keep {kept.id}: member {extra.member_id} {extra.case_id!r} "
                f"{(extra.notes or '').splitlines()[0] if extra.notes else ''!r}"
            )
            if extra.court_case_id is not None and kept.court_case_id is None:
                kept.court_case_id = extra.court_case_id
                s.add(kept)
                relinked += 1
        if relinked:
            print(f"  {relinked} case links moved onto the kept row")

        print(f"\n{len(multi)} groups keep more than one identical row (check against OTIS;")
        print("  --keep-one collapses them to one):")
        for g in multi:
            print(
                f"  member {g['member_id']} {g['case_id']!r} {g['offense']!r}: "
                f"{g['rows']} rows in {g['batches']} batch(es), keeping {g['keep']}"
            )
        print(f"\n{len(differing)} groups left alone because their copies differ:")
        for g in differing:
            print(
                f"  member {g['member_id']} {g['case_id']!r} {g['offense']!r}: "
                f"{g['rows']} rows, differ in {', '.join(g['differs_in'])}"
            )

        if not go:
            await s.rollback()
            print("\ndry run, nothing written; pass --go to write")
            return 0

        now = datetime.datetime.now(datetime.UTC)
        snapshots = [_snapshot(e) for e, _ in deletions]
        path = backup or f"dedupe_incarcerations-{db}-{now:%Y%m%dT%H%M%SZ}.json"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(snapshots, fh, indent=1)
        for (extra, _), snap in zip(deletions, snapshots, strict=True):
            s.add(
                AuditLog(
                    user_id=actor,
                    entity_type="member_incarceration",
                    entity_id=extra.id,
                    action=AuditAction.DELETE,
                    diff_json={k: v for k, v in snap.items() if k != "created_at"},
                    created_at=now,
                )
            )
            await s.delete(extra)
        await s.commit()
        print(f"\nwritten; {len(snapshots)} deleted rows backed up to {path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Delete duplicate incarceration spells.")
    ap.add_argument("--db", choices=sorted(_session_factories), default="prod")
    ap.add_argument("--go", action="store_true", help="write the changes")
    ap.add_argument(
        "--batch-gap",
        type=float,
        default=120.0,
        help="seconds between two writes that start a new import batch (default 120)",
    )
    ap.add_argument(
        "--keep-one",
        action="store_true",
        help="keep one row per group even where one batch wrote several (checked against OTIS)",
    )
    ap.add_argument("--backup", help="where --go writes the deleted rows as JSON")
    args = ap.parse_args()
    return asyncio.run(run(args.db, args.go, args.batch_gap, args.keep_one, args.backup))


if __name__ == "__main__":
    sys.exit(main())
