"""Give every existing universe the Unknown reserved set.

`seed_reserved_sets` only runs when a universe is created, so the three
universes that predate Unknown never got one. This adds it where it is missing
and leaves alone any universe that already has it. Idempotent.

Dry-run by default; --go writes.
"""

import asyncio
import sys

from sqlmodel import select

from app.core.database import _session_factories
from app.models.gang_set import GangSet
from app.models.universe import Universe

GO = "--go" in sys.argv


async def main() -> None:
    """Insert the Unknown set into each universe that lacks one."""
    async with _session_factories["prod"]() as session:
        universes = (await session.execute(select(Universe))).scalars().all()
        for u in universes:
            existing = (
                await session.execute(
                    select(GangSet).where(GangSet.universe_id == u.id, GangSet.slug == "unknown")
                )
            ).scalar_one_or_none()
            if existing is not None:
                print(f"SKIP {u.name}: already has one ({existing.id})")
                continue
            if not GO:
                print(f"DRY  {u.name}: would add Unknown")
                continue
            session.add(GangSet(universe_id=u.id, name="Unknown", slug="unknown", is_reserved=True))
            print(f"OK   {u.name}: Unknown added")
        if GO:
            await session.commit()


asyncio.run(main())
