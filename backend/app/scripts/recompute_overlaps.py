"""Recompute municipality_overlap for every city that has sub-areas.

The API keeps the table current on every write; this is for the backfill after
migration 2d5a7ab2c470 and for after any bulk change to outlines made in SQL.

Run from backend/:
  $PY -m app.scripts.recompute_overlaps
"""

import asyncio
import sys

from sqlalchemy import func
from sqlmodel import select

from app.core.database import _session_factories
from app.crud.municipality import sync_overlaps
from app.models.municipality import Municipality, MunicipalityOverlap


async def main() -> int:
    async with _session_factories["prod"]() as s:
        parents = (
            (
                await s.execute(
                    select(Municipality.parent_id)
                    .distinct()
                    .where(Municipality.parent_id.is_not(None))
                )
            )
            .scalars()
            .all()
        )
        for pid in parents:
            await sync_overlaps(s, pid)
        await s.commit()
        n = (await s.execute(select(func.count()).select_from(MunicipalityOverlap))).scalar_one()
        print(f"{len(parents)} cities recomputed, {n} overlaps stored")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
