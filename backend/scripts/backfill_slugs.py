"""
One-shot script: populate sets.slug for existing rows.
Run once after applying migration 10d0ba868d7f_add_slug_to_gang_set.

Usage:
  cd backend
  python scripts/backfill_slugs.py
"""
import re
import sys
import psycopg2

from app.core.config import settings


def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-") or "set"


def main() -> None:
    # settings.database_url is asyncpg; convert to psycopg2 format
    url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    conn = psycopg2.connect(url)
    cur = conn.cursor()

    cur.execute("SELECT id, name, universe_id FROM sets WHERE slug IS NULL")
    rows = cur.fetchall()

    if not rows:
        print("No rows to backfill.")
        conn.close()
        return

    slug_seen: dict[tuple, int] = {}
    updates: list[tuple[str, str]] = []

    for row_id, name, universe_id in rows:
        base = slugify(name)
        key = (str(universe_id), base)
        n = slug_seen.get(key, 0) + 1
        slug_seen[key] = n
        slug = base if n == 1 else f"{base}-{n}"
        updates.append((slug, str(row_id)))

    cur.executemany("UPDATE sets SET slug = %s WHERE id = %s::uuid", updates)
    conn.commit()
    print(f"Backfilled {len(updates)} rows.")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
