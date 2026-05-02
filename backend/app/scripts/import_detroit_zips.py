"""Import Detroit ZIP-code areas as child municipalities of Detroit.

Source: City of Detroit Zip Code Tabulation Areas (ZCTA) — 34 features.
Each feature -> a child municipality of "Detroit" in the metro-detroit universe,
named with the bare ZIP (e.g. "48201").

Idempotent: skips features whose name (zipcode) + parent_id already exist.

Run from backend/:
  $PY -m app.scripts.import_detroit_zips
"""
import asyncio
import json
import sys
import uuid
from pathlib import Path

from sqlalchemy import text

from app.core.database import _session_factories

GEOJSON_PATH = Path(__file__).resolve().parent / "data" / "detroit_zip_codes.geojson"
UNIVERSE_SLUG = "metro-detroit"
PARENT_NAME = "Detroit"


async def main() -> int:
    if not GEOJSON_PATH.exists():
        print(f"GeoJSON not found at {GEOJSON_PATH}", file=sys.stderr)
        return 1

    raw = json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))
    features = raw.get("features", [])
    print(f"Loaded {len(features)} features from {GEOJSON_PATH.name}")

    async with _session_factories["prod"]() as s:
        univ_row = (await s.execute(
            text("SELECT id FROM universe WHERE slug = :slug"),
            {"slug": UNIVERSE_SLUG},
        )).first()
        if univ_row is None:
            print(f"Universe '{UNIVERSE_SLUG}' not found.", file=sys.stderr)
            return 1
        universe_id: uuid.UUID = univ_row[0]

        parent_row = (await s.execute(
            text(
                "SELECT id FROM municipality "
                "WHERE universe_id = :uid AND name = :name AND parent_id IS NULL"
            ),
            {"uid": str(universe_id), "name": PARENT_NAME},
        )).first()
        if parent_row is None:
            print(
                f"Parent municipality '{PARENT_NAME}' not found in universe '{UNIVERSE_SLUG}'.",
                file=sys.stderr,
            )
            return 1
        parent_id: uuid.UUID = parent_row[0]

        existing_names = {
            r[0]
            for r in (await s.execute(
                text(
                    "SELECT name FROM municipality "
                    "WHERE universe_id = :uid AND parent_id = :pid"
                ),
                {"uid": str(universe_id), "pid": str(parent_id)},
            )).all()
        }

        inserted = 0
        skipped = 0
        for feat in features:
            props = feat.get("properties") or {}
            zipcode = str(props.get("zipcode") or "").strip()
            geom = feat.get("geometry")
            if not zipcode or geom is None:
                skipped += 1
                continue
            if zipcode in existing_names:
                skipped += 1
                continue
            await s.execute(
                text(
                    "INSERT INTO municipality (id, universe_id, name, parent_id, geometry) "
                    "VALUES (:id, :uid, :name, :pid, CAST(:geom AS jsonb))"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "uid": str(universe_id),
                    "name": zipcode,
                    "pid": str(parent_id),
                    "geom": json.dumps(geom),
                },
            )
            inserted += 1

        await s.commit()

    print(f"Inserted {inserted} ZIP municipalities, skipped {skipped}.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
