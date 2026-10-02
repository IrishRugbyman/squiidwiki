"""Bring every set's name_variants into line with its name, without renaming anything.

Since `sets.name` is derived from the primary name variant (app/core/set_names.py),
a set whose stored name is not what its primary variant displays would be renamed
on its next save. Before the change, 35 sets were in that state ("CFP 2400"
displayed as "CFP", "TNO" as "Trust No One") and 29 had no variants at all.

The stored name is what pills, captions and slugs have always shown, so it is
the name kept. For each set, in order:

1. No variants: one primary variant is made from the name, in the slot the name
   is: digits go to `number`, an all-caps tag ("LCF", "GMS") to `initials`,
   anything else to `name`.
2. The primary already displays the name: nothing to do.
3. Some ordering of the primary's filled slots displays the name ("CFP" +
   "2400"): that becomes its `lead`. The shortest such lead wins.
4. Another variant displays the name: it becomes the primary.
5. Otherwise the name is added as a new primary `name` variant, and the old
   primary is kept as an alternative.

Names, and so slugs, never change. Reserved sets are skipped. Idempotent: a
second run finds nothing to do.

Run from backend/:
  $PY -m app.scripts.derive_set_names              # dry run against prod
  $PY -m app.scripts.derive_set_names --db test    # dry run against test
  $PY -m app.scripts.derive_set_names --go         # write
"""

import argparse
import asyncio
import copy
import itertools
import re
import sys

import sqlalchemy as sa
from sqlmodel import select

from app.core.database import _session_factories
from app.core.set_names import SLOTS, display_name, variant_display
from app.models.gang_set import GangSet
from app.models.universe import Universe

_INITIALS = re.compile(r"[A-Z0-9$&.]*[A-Z][A-Z0-9$&.]*")


def _slot_for(name: str) -> str:
    """Which slot a bare name belongs in."""
    if name.isdigit():
        return "number"
    if len(name) <= 6 and _INITIALS.fullmatch(name):
        return "initials"
    return "name"


def _fit_lead(variant: dict, name: str) -> str | list[str] | None:
    """The shortest ordering of the variant's filled slots that displays `name`."""
    filled = [s for s in SLOTS if (variant.get(s) or "").strip()]
    for size in range(1, len(filled) + 1):
        for order in itertools.permutations(filled, size):
            if " ".join(variant[s].strip() for s in order) == name:
                return order[0] if size == 1 else list(order)
    return None


def plan(name: str, variants: list[dict] | None) -> tuple[list[dict], str] | None:
    """The variants that make `name` the derived name, and why; None when they already do."""
    name = name.strip()
    if not variants:
        slot = _slot_for(name)
        return [
            {
                "name": None,
                "initials": None,
                "number": None,
                slot: name,
                "is_primary": True,
                "lead": None,
            }
        ], f"seeded as {slot}"
    if display_name(variants) == name:
        return None
    out = copy.deepcopy(variants)
    if not any(v.get("is_primary") for v in out):
        out[0]["is_primary"] = True
    primary = next(v for v in out if v.get("is_primary"))
    lead = _fit_lead(primary, name)
    if lead is not None:
        before = variant_display(primary)
        primary["lead"] = lead
        return out, f"lead {lead!r} (was showing {before!r})"
    for v in out:
        if v is not primary and variant_display(v) == name:
            primary["is_primary"] = False
            v["is_primary"] = True
            return out, "an existing variant made primary"
    for v in out:
        if v is not primary:
            fitted = _fit_lead(v, name)
            if fitted is not None:
                primary["is_primary"] = False
                v["is_primary"] = True
                v["lead"] = fitted
                return out, f"an existing variant made primary, lead {fitted!r}"
    primary["is_primary"] = False
    out.insert(
        0, {"name": name, "initials": None, "number": None, "is_primary": True, "lead": None}
    )
    return out, f"added as a new primary name; {variant_display(primary)!r} kept as a variant"


async def run(db: str, go: bool) -> int:
    async with _session_factories[db]() as s:
        rows = (
            await s.execute(
                select(GangSet, Universe.name)
                .join(Universe, Universe.id == GangSet.universe_id)
                .where(GangSet.is_reserved.is_(False))
                .order_by(Universe.name, GangSet.name)
            )
        ).all()
        changes = 0
        for obj, universe in rows:
            result = plan(obj.name, obj.name_variants)
            if result is None:
                continue
            variants, why = result
            assert display_name(variants) == obj.name.strip(), (obj.name, variants)
            changes += 1
            print(f"{universe:10} {obj.name!r:34} {why}")
            if go:
                obj.name_variants = variants
                sa.orm.attributes.flag_modified(obj, "name_variants")
                s.add(obj)
        if go:
            await s.commit()
        print(
            f"\n{len(rows)} sets checked in {db}, {changes} "
            f"{'updated' if go else 'to update (dry run, pass --go to write)'}"
        )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Align every set's name_variants with its name.")
    ap.add_argument("--db", choices=sorted(_session_factories), default="prod")
    ap.add_argument("--go", action="store_true", help="write the changes")
    args = ap.parse_args()
    return asyncio.run(run(args.db, args.go))


if __name__ == "__main__":
    sys.exit(main())
