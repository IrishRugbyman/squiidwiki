"""Fold custody lookup sources into one per system per universe.

Before 2026-10-04 every reading of the BOP locator, MDOC's OTIS or the GDC
offender query was its own source row, told apart only by its title ("BOP
Inmate Locator - <name>, register <n>"), because those sites give a record no
address of its own. That made the source list mostly lookup pages and hid
which documents a member really rests on. Now each universe holds one source
per system, and the person-specific part moves onto the citation:

- locator: the member's number in that system from `member_custody_id`, or
  else the number read from the old URL or title;
- note and accessed_at: the old row's notes and reading date.

A member cited by two old rows of one system keeps one citation, the locators
and notes joined (crud.source.merge_into). Custody numbers, aliases and photos
pointing at an old row are re-pointed. A row filed under a lookup URL that is
not a lookup (a social post quoting an OTIS profile) is set apart first.

    $PY -m app.scripts.merge_lookup_sources --db test           # dry run
    $PY -m app.scripts.merge_lookup_sources --db test --go
    $PY -m app.scripts.merge_lookup_sources --go --log <file>   # prod

The mapping (old title -> locator, per citation) names people, so it is only
ever written to the --log path given, which belongs in the private research
tree, never to stdout or this repo.
"""

import argparse
import asyncio
import json
import uuid
from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.database import _session_factories
from app.core.sources import (
    LOOKUP_CANONICAL,
    LookupSystem,
    SourceKind,
    lookup_locator,
    normalise_url,
)
from app.crud.source import merge_into
from app.models.citation import Citation
from app.models.member import MemberCustodyId
from app.models.source import Source

# member_custody_id.system for each lookup system.
_CUSTODY_SYSTEM = {LookupSystem.BOP: "BOP", LookupSystem.MDOC_OTIS: "MDOC", LookupSystem.GDC: "GDC"}


def _not_a_lookup(s: Source) -> bool:
    """A source under a lookup URL that is really something else."""
    return "facebook" in (s.publication or "").casefold()


async def _member_numbers(session, system: LookupSystem) -> dict[uuid.UUID, list[str]]:
    rows = await session.execute(
        select(MemberCustodyId.member_id, MemberCustodyId.number).where(
            MemberCustodyId.system == _CUSTODY_SYSTEM[system]
        )
    )
    out: dict[uuid.UUID, list[str]] = defaultdict(list)
    for member_id, number in rows.all():
        out[member_id].append(number)
    return out


async def _stamp(session, source: Source, numbers, log: list[dict]) -> None:
    """Move the old row's person-specific part onto each of its citations."""
    fallback = lookup_locator(source.url, source.title)
    citations = (
        (await session.execute(select(Citation).where(Citation.source_id == source.id)))
        .scalars()
        .all()
    )
    for c in citations:
        mine = numbers.get(c.member_id, []) if c.member_id else []
        locator = mine[0] if len(mine) == 1 else fallback
        c.locator = c.locator or locator
        c.note = c.note or source.notes
        c.accessed_at = c.accessed_at or source.accessed_at
        c.updated_at = datetime.now(UTC)
        session.add(c)
        entity, entity_id = c.target()
        log.append(
            {
                "old_source": str(source.id),
                "old_title": source.title,
                "entity": entity,
                "entity_id": str(entity_id),
                "locator": c.locator,
            }
        )
    await session.flush()


async def run(db: str, go: bool, log_path: str | None) -> int:
    log: list[dict] = []
    summary = []
    async with _session_factories[db]() as session:
        rows = (
            (await session.execute(select(Source).where(Source.lookup_system.is_not(None))))
            .scalars()
            .all()
        )
        groups: dict[tuple[uuid.UUID, str], list[Source]] = defaultdict(list)
        for s in rows:
            if _not_a_lookup(s):
                s.lookup_system = None
                s.kind = SourceKind.SOCIAL.value
                session.add(s)
                summary.append(f"set apart (not a lookup): source {s.id}")
                continue
            groups[(s.universe_id, s.lookup_system)].append(s)

        for (universe_id, system_value), sources in sorted(groups.items(), key=str):
            system = LookupSystem(system_value)
            numbers = await _member_numbers(session, system)
            sources.sort(key=lambda s: (s.created_at, str(s.id)))
            canonical, others = sources[0], sources[1:]
            for s in sources:
                await _stamp(session, s, numbers, log)
            fields = LOOKUP_CANONICAL[system]
            canonical.title = fields["title"]
            canonical.url = fields["url"]
            canonical.url_norm = normalise_url(fields["url"])
            canonical.publication = fields["publication"]
            canonical.kind = SourceKind.CUSTODY.value
            canonical.notes = None
            canonical.accessed_at = None
            canonical.published_at = None
            canonical.archive_url = None
            canonical.updated_at = datetime.now(UTC)
            session.add(canonical)
            await session.flush()
            moved = combined = 0
            for s in others:
                out = await merge_into(session, s, canonical, commit=False)
                moved += out["moved"]
                combined += out["combined"]
            summary.append(
                f"universe {universe_id} {system.value}: {len(sources)} rows -> 1 "
                f"({moved} links moved, {combined} combined)"
            )
        print("\n".join(summary))
        if go:
            await session.commit()
            print("written")
        else:
            await session.rollback()
            print("dry run - pass --go to write")
    if log_path:
        with open(log_path, "w") as f:
            json.dump(log, f, indent=1, ensure_ascii=False)
        print(f"mapping of {len(log)} citations written to {log_path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Fold custody lookup sources into one per system.")
    ap.add_argument("--db", choices=sorted(_session_factories), default="prod")
    ap.add_argument("--go", action="store_true", help="write the changes")
    ap.add_argument("--log", help="where to write the per-citation mapping (private)")
    args = ap.parse_args()
    return asyncio.run(run(args.db, args.go, args.log))


if __name__ == "__main__":
    raise SystemExit(main())
