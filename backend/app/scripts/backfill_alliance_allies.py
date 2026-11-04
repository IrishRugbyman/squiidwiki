"""Make allies of sets that share an alliance but have no link at all, pair by approved pair.

Joining an alliance befriends its sets (`_sync_alliance_auto_allies` in
`app/crud/gang_set.py`). Until 2026-11 that sync found the siblings through the
`sets.alliance_id` mirror, so a set holding the alliance second or later was
never befriended, and some pairs of sets in one alliance hold no
`set_relationships` row either way.

Some of those gaps are deliberate: two crews can sit in one alliance and still
feud. So this script never decides on its own. A dry run (the default) lists
every pair that shares an alliance (any position in `alliance_set`) and has no
relationship row at all, ally or enemy, current or ended, in either order. It
prints each with its pair key, `<set uuid>:<set uuid>` with the smaller UUID
first. Writing needs `--go` AND an explicit approval list; every pair not on the
list is skipped and reported, and a pair that has any row by the time of the
write is never touched.

An approved pair is written through `befriend_alliance_pair`, the helper the
auto-ally sync itself uses (pair normalised to set_a_id < set_b_id, FRIEND,
open-ended), and recorded on both sets' History as an "allies" link change.

Run from backend/:
  $PY -m app.scripts.backfill_alliance_allies --db test                    # dry run
  $PY -m app.scripts.backfill_alliance_allies --db test --universe detroit # one universe
  $PY -m app.scripts.backfill_alliance_allies --db test --go --approve pairs.txt
  $PY -m app.scripts.backfill_alliance_allies --db test --go --pair A:B --pair C:D

The approval file holds one pair key per line, as the dry run prints them;
blank lines and `#` comments are ignored. Either order of the two UUIDs is
accepted.
"""

import argparse
import asyncio
import sys
import uuid
from dataclasses import dataclass, field

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_link_change
from app.core.database import _session_factories
from app.crud.gang_set import befriend_alliance_pair


@dataclass
class Pair:
    a_id: uuid.UUID
    b_id: uuid.UUID
    a_name: str
    b_name: str
    universe: str
    alliances: list[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        return pair_key(self.a_id, self.b_id)


@dataclass
class Result:
    missing: list[Pair]
    written: list[Pair] = field(default_factory=list)
    skipped: list[Pair] = field(default_factory=list)
    # Approved keys that are not a missing pair (already linked, or not sharing
    # an alliance): never written.
    not_missing: list[str] = field(default_factory=list)


def pair_key(x: uuid.UUID, y: uuid.UUID) -> str:
    """The stable key of a pair: both UUIDs, the smaller first."""
    a, b = (x, y) if x < y else (y, x)
    return f"{a}:{b}"


def parse_key(raw: str) -> str:
    """A pair key from user input, in either order; ValueError when malformed."""
    parts = raw.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"not a pair key (want <uuid>:<uuid>): {raw!r}")
    x, y = (uuid.UUID(p.strip()) for p in parts)
    if x == y:
        raise ValueError(f"a pair needs two different sets: {raw!r}")
    return pair_key(x, y)


def read_approvals(path: str | None, pairs: list[str]) -> set[str]:
    keys: set[str] = set()
    if path:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.split("#", 1)[0].strip()
                if line:
                    keys.add(parse_key(line))
    keys.update(parse_key(p) for p in pairs)
    return keys


_MISSING = sa.text(
    """
    SELECT s1.id, s1.name, s2.id, s2.name, u.name, al.name
    FROM alliance_set x
    JOIN alliance_set y ON y.alliance_id = x.alliance_id AND x.set_id < y.set_id
    JOIN alliance al ON al.id = x.alliance_id
    JOIN universe u ON u.id = al.universe_id
    JOIN sets s1 ON s1.id = x.set_id
    JOIN sets s2 ON s2.id = y.set_id
    WHERE (CAST(:universe_id AS uuid) IS NULL OR al.universe_id = CAST(:universe_id AS uuid))
      AND NOT EXISTS (
        SELECT 1 FROM set_relationships r
        WHERE (r.set_a_id = x.set_id AND r.set_b_id = y.set_id)
           OR (r.set_a_id = y.set_id AND r.set_b_id = x.set_id)
      )
    ORDER BY u.name, s1.name, s2.name, al.name
    """
)


async def missing_pairs(session: AsyncSession, universe_id: uuid.UUID | None = None) -> list[Pair]:
    """Pairs of sets sharing an alliance with no relationship row at all."""
    rows = await session.execute(
        _MISSING, {"universe_id": str(universe_id) if universe_id else None}
    )
    by_key: dict[str, Pair] = {}
    for a_id, a_name, b_id, b_name, universe, alliance in rows.all():
        key = pair_key(a_id, b_id)
        if key not in by_key:
            by_key[key] = Pair(a_id, b_id, a_name, b_name, universe)
        by_key[key].alliances.append(alliance)
    return list(by_key.values())


async def _has_any_link(session: AsyncSession, x: uuid.UUID, y: uuid.UUID) -> bool:
    row = await session.execute(
        sa.text(
            "SELECT 1 FROM set_relationships WHERE (set_a_id = :x AND set_b_id = :y) "
            "OR (set_a_id = :y AND set_b_id = :x) LIMIT 1"
        ),
        {"x": x, "y": y},
    )
    return row.first() is not None


async def backfill(
    session: AsyncSession,
    *,
    approved: set[str],
    go: bool,
    universe_id: uuid.UUID | None = None,
) -> Result:
    """List the missing pairs; with `go`, befriend the approved ones and commit.

    Nothing is written without `go`, and nothing outside `approved`, whatever
    `go` says. Commits only when it wrote something.
    """
    result = Result(missing=await missing_pairs(session, universe_id))
    keys = {p.key for p in result.missing}
    result.not_missing = sorted(approved - keys)
    for pair in result.missing:
        if not (go and pair.key in approved):
            result.skipped.append(pair)
            continue
        # Checked again at write time: never over any row, ally or enemy.
        if await _has_any_link(session, pair.a_id, pair.b_id):
            result.skipped.append(pair)
            continue
        if await befriend_alliance_pair(session, pair.a_id, pair.b_id) is None:
            result.skipped.append(pair)
            continue
        for me, other in ((pair.a_id, pair.b_id), (pair.b_id, pair.a_id)):
            record_link_change(
                session,
                entity_type="sets",
                entity_id=me,
                link="allies",
                key="set_id",
                before=[],
                after=[{"set_id": other, "relationship_type": "FRIEND"}],
            )
        result.written.append(pair)
    if result.written:
        await session.commit()
    return result


def _line(p: Pair) -> str:
    return (
        f"{p.key}  {p.universe}: {p.a_name!r} + {p.b_name!r}  (alliance: {', '.join(p.alliances)})"
    )


async def run(db: str, universe: str | None, go: bool, approved: set[str]) -> int:
    async with _session_factories[db]() as s:
        universe_id = None
        if universe:
            universe_id = (
                await s.execute(sa.text("SELECT id FROM universe WHERE slug = :s"), {"s": universe})
            ).scalar_one_or_none()
            if universe_id is None:
                print(f"no universe {universe!r} in {db}", file=sys.stderr)
                return 2
        result = await backfill(s, approved=approved, go=go, universe_id=universe_id)
    print(f"{len(result.missing)} pairs share an alliance with no relationship row in {db}:")
    for p in result.missing:
        print("  " + _line(p))
    if go:
        print(f"\nwritten as allies ({len(result.written)}):")
        for p in result.written:
            print("  " + _line(p))
        print(f"skipped, not approved or linked meanwhile ({len(result.skipped)}):")
        for p in result.skipped:
            print("  " + _line(p))
    else:
        print("\ndry run: nothing written. Approve pairs with --approve FILE / --pair, and --go.")
    if result.not_missing:
        print(f"\napproved but not a missing pair, ignored ({len(result.not_missing)}):")
        for k in result.not_missing:
            print("  " + k)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Befriend approved pairs of sets that share an alliance and have no link."
    )
    ap.add_argument("--db", choices=sorted(_session_factories), required=True)
    ap.add_argument("--universe", help="limit to one universe, by slug")
    ap.add_argument("--go", action="store_true", help="write the approved pairs")
    ap.add_argument("--approve", metavar="FILE", help="file of approved pair keys, one per line")
    ap.add_argument(
        "--pair", action="append", default=[], metavar="A:B", help="an approved pair key"
    )
    args = ap.parse_args()
    try:
        approved = read_approvals(args.approve, args.pair)
    except ValueError as e:
        ap.error(str(e))
    if args.go and not approved:
        print("--go writes only approved pairs, and none were given: nothing to write.")
    return asyncio.run(run(args.db, args.universe, args.go, approved))


if __name__ == "__main__":
    sys.exit(main())
