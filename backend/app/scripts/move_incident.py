"""Move incidents to another universe.

An incident belongs to the universe it happened in. When a state gets its own
universe after the fact (Texas, 2026-10-04), the incidents filed elsewhere for
want of one move to it. The API has no way to do that: its writes are scoped
to the incident's universe, and three things hang off the incident by universe.

- Citations must cite a source of the incident's own universe, so each one is
  pointed at the target universe's source with the same normalised URL, or at
  a copy of the old source made there.
- Its photos carry the universe too; the R2 object is left where it is.
- Its municipality must be in the target universe, so it is given one there
  (`--municipality`) or cleared.

Participants are untouched: a member of any universe may take part in an
incident. Set participants must be of the incident's universe, so an incident
with any is refused. Court cases keep their link, as a case may cover an
incident of another universe.

Writes go through the ORM and are audited as claude-admin.

Run from backend/:
  $PY -m app.scripts.move_incident <incident id>... --to texas [--municipality Houston]
  ... --go        # write
"""

import argparse
import asyncio
import sys
import uuid

from sqlmodel import select

from app.core.audit import attach_audit_listeners, current_user_id
from app.core.database import _session_factories
from app.models.auth import User
from app.models.citation import Citation
from app.models.incident import Incident, IncidentSetParticipant
from app.models.media import Media
from app.models.municipality import Municipality
from app.models.source import Source
from app.models.universe import Universe

ACTOR = "claude-admin@squiidwiki.dev"

# Copied as they are; universe, id and timestamps are the new row's own.
_SOURCE_FIELDS = (
    "url",
    "url_norm",
    "title",
    "publication",
    "published_at",
    "accessed_at",
    "reliability",
    "kind",
    "lookup_system",
    "notes",
    "archive_url",
)


async def _target_source(s, source: Source, universe_id: uuid.UUID, made: dict) -> Source:
    """The target universe's source for `source`: same normalised URL, or a copy."""
    if source.id in made:
        return made[source.id]
    found = None
    if source.url_norm:
        found = (
            (
                await s.execute(
                    select(Source)
                    .where(Source.universe_id == universe_id, Source.url_norm == source.url_norm)
                    .order_by(Source.created_at)
                )
            )
            .scalars()
            .first()
        )
    if found is None:
        found = Source(universe_id=universe_id, **{f: getattr(source, f) for f in _SOURCE_FIELDS})
        s.add(found)
        await s.flush()
        print(f"    copies source {source.title!r}")
    else:
        print(f"    cites the target's own {found.title!r}")
    made[source.id] = found
    return found


async def run(db: str, ids: list[str], to: str, municipality: str | None, go: bool) -> int:
    attach_audit_listeners()
    async with _session_factories[db]() as s:
        actor = (await s.execute(select(User.id).where(User.email == ACTOR))).scalar_one_or_none()
        current_user_id.set(actor)

        target = (await s.execute(select(Universe).where(Universe.slug == to))).scalar_one_or_none()
        if target is None:
            sys.exit(f"no universe {to!r} in {db}")
        muni_id = None
        if municipality:
            muni = (
                await s.execute(
                    select(Municipality).where(
                        Municipality.universe_id == target.id, Municipality.name == municipality
                    )
                )
            ).scalar_one_or_none()
            if muni is None:
                sys.exit(f"no municipality {municipality!r} in {to}")
            muni_id = muni.id

        made: dict[uuid.UUID, Source] = {}
        for raw in ids:
            incident = await s.get(Incident, uuid.UUID(raw))
            if incident is None:
                sys.exit(f"no incident {raw} in {db}")
            if incident.universe_id == target.id:
                print(f"{raw} is already in {to}")
                continue
            sets = (
                (
                    await s.execute(
                        select(IncidentSetParticipant).where(
                            IncidentSetParticipant.incident_id == incident.id
                        )
                    )
                )
                .scalars()
                .all()
            )
            if sets:
                sys.exit(f"{raw} has set participants, which must stay in its universe; refusing")

            print(f"{raw}  {incident.location_text}  -> {to}")
            citations = (
                (
                    await s.execute(
                        select(Citation)
                        .where(Citation.incident_id == incident.id)
                        .order_by(Citation.position)
                    )
                )
                .scalars()
                .all()
            )
            kept: dict[uuid.UUID, Citation] = {}
            for c in citations:
                source = await s.get(Source, c.source_id)
                new = await _target_source(s, source, target.id, made)
                if new.id in kept:
                    # Two old sources with one URL become one source here, and a
                    # record cites a source once: fold this citation's detail
                    # into the first and drop it.
                    first = kept[new.id]
                    for field in ("locator", "quote", "note"):
                        extra = getattr(c, field)
                        have = getattr(first, field)
                        if extra and extra != have:
                            setattr(first, field, f"{have}; {extra}" if have else extra)
                    s.add(first)
                    await s.delete(c)
                    print(f"    folds a second citation of {new.title!r} into the first")
                    continue
                c.source_id = new.id
                c.universe_id = target.id
                kept[new.id] = c
                s.add(c)
            await s.flush()
            for m in (
                await s.execute(select(Media).where(Media.incident_id == incident.id))
            ).scalars():
                m.universe_id = target.id
                s.add(m)
                print(f"    moves photo {m.original_filename or m.id}")
            incident.universe_id = target.id
            incident.municipality_id = muni_id
            s.add(incident)
            await s.flush()

        if go:
            await s.commit()
            print("written")
        else:
            await s.rollback()
            print("dry run, nothing written; pass --go to write")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Move incidents to another universe.")
    ap.add_argument("incidents", nargs="+", help="incident ids")
    ap.add_argument("--to", required=True, help="target universe slug")
    ap.add_argument("--municipality", help="the target universe's municipality, by name")
    ap.add_argument("--db", choices=sorted(_session_factories), default="prod")
    ap.add_argument("--go", action="store_true", help="write the changes")
    args = ap.parse_args()
    return asyncio.run(run(args.db, args.incidents, args.to, args.municipality, args.go))


if __name__ == "__main__":
    sys.exit(main())
