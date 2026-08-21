#!/usr/bin/env python3
"""Reconcile the privedatabase extraction against the SquiidWiki database.

Read-only. Writes db-sync.md next to the extraction files. Re-run it after any
seeding pass; never hand-maintain the status table, it will drift.

    python3 research/privedatabase/tools/db_sync.py [--db squiidwiki_prod]
"""

import argparse
import datetime
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
UNIVERSE = {
    "chicago": ("Metro Chicago", "59d23911-6fee-4156-8839-ac3c248a3b46"),
    "detroit": ("Metro Detroit", "4f57cae1-ebfe-408c-b435-052e2bd0ca45"),
}


def norm(x: str) -> str:
    """Reduce a name to a comparison key: lowercase, alphanumerics only."""
    return re.sub(r"[^a-z0-9]", "", (x or "").lower())


def candidates(title: str):
    """Keys a site title might match a DB set under.

    Site titles carry forms the DB name does not: "OAK BOYZ NATION (OBN)" is
    stored as "OBN", and "DIPSET/FRONT$TREET" covers two sets. Without these
    the reconciliation reports false orphans in both directions.
    """
    out = {norm(title)}
    inner = re.findall(r"\(([^)]+)\)", title)  # (OBN)
    out |= {norm(i) for i in inner}
    out.add(norm(re.sub(r"\([^)]*\)", "", title)))  # title minus parenthetical
    for part in re.split(r"[/]", re.sub(r"\([^)]*\)", "", title)):
        out.add(norm(part))
    return {k for k in out if k}


def psql_json(db, sql):
    """Return query results as JSON. Bios contain newlines, so row-splitting on
    text output is unsafe - let Postgres do the encoding."""
    r = subprocess.run(
        ["psql", "-d", db, "-t", "-A", "-c", f"SELECT coalesce(json_agg(t),'[]') FROM ({sql}) t;"],
        capture_output=True,
        text=True,
    )
    if r.returncode:
        sys.exit(f"psql failed: {r.stderr.strip()}")
    return json.loads(r.stdout.strip() or "[]")


def db_sets(db, uid):
    """Return the universe's non-reserved sets, keyed by id, with match keys."""
    rows = psql_json(
        db,
        f"""
        SELECT s.id, s.name, s.slug, coalesce(s.bio,'') AS bio,
               coalesce(g.name,'') AS gang,
               coalesce(s.name_variants,'[]'::jsonb) AS nv,
               (SELECT count(*) FROM member_set ms WHERE ms.set_id=s.id) AS members,
               (SELECT count(*) FROM set_relationships r
                  WHERE r.set_a_id=s.id OR r.set_b_id=s.id) AS relations
        FROM sets s LEFT JOIN gang g ON g.id=s.gang_id
        WHERE s.universe_id='{uid}' AND s.is_reserved=false""",
    )
    out = {}
    for r in rows:
        keys = {norm(r["name"])} | {norm(v.get("name", "")) for v in (r["nv"] or [])}
        out[r["id"]] = {
            "id": r["id"],
            "name": r["name"],
            "slug": r["slug"],
            "bio": r["bio"],
            "gang": r["gang"],
            "members": r["members"],
            "relations": r["relations"],
            "keys": {k for k in keys if k},
        }
    return out


def extraction(city):
    """Sets parsed out of the site, keyed by page id."""
    return json.loads((ROOT / "tools" / f"extract-{city}.json").read_text())


def main():
    """Reconcile extraction against the database and write db-sync.md."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="squiidwiki_prod")
    a = ap.parse_args()

    L = [
        "# Extraction ↔ database sync",
        "",
        "**Generated** - do not hand-edit. Regenerate with:",
        "",
        "```bash",
        f"python3 research/privedatabase/tools/db_sync.py --db {a.db}",
        "```",
        "",
        f"Database: `{a.db}`. Last run: {datetime.date.today().isoformat()}.",
        "",
    ]

    for city in ("chicago",):
        uname, uid = UNIVERSE[city]
        ex = extraction(city)
        db = db_sets(a.db, uid)
        by_key = {}
        for s in db.values():
            for k in s["keys"]:
                by_key.setdefault(k, s)

        seeded, missing = [], []
        for pid, e in sorted(ex.items(), key=lambda kv: kv[1]["title"].upper()):
            hit = next((by_key[k] for k in candidates(e["title"]) if k in by_key), None)
            (seeded if hit else missing).append((pid, e, hit))

        matched_ids = {h["id"] for _, _, h in seeded if h}
        orphans = [s for sid, s in db.items() if sid not in matched_ids]

        L += [
            f"## {uname}",
            "",
            f"- **{len(ex)}** sets extracted from the site",
            f"- **{len(seeded)}** of them are in the database",
            f"- **{len(missing)}** not yet seeded",
            f"- **{len(orphans)}** database sets with no matching extraction",
            "",
        ]

        if seeded:
            L += [
                "### In the database",
                "",
                "`Rel` counts set_relationships rows; `Mem` counts member_set rows.",
                "",
                "| Set | Page | DB slug | Bio | Gang | Mem | Rel |",
                "|---|---|---|---|---|---|---|",
            ]
            for pid, e, h in seeded:
                L.append(
                    f"| {e['title']} | {pid} | `{h['slug']}` | {'Y' if h['bio'] else '-'} | "
                    f"{h['gang'] or '-'} | {h['members'] or '-'} | {h['relations'] or '-'} |"
                )
            L.append("")

        if missing:
            L += [
                "### Not yet seeded",
                "",
                "| Set | Page | Nations | Allies | Enemies |",
                "|---|---|---|---|---|",
            ]
            for pid, e, _ in missing:
                L.append(
                    f"| {e['title']} | {pid} | {', '.join(e.get('nations', [])) or '-'} | "
                    f"{len(e.get('allies', []))} | {len(e.get('enemies', []))} |"
                )
            L.append("")

        if orphans:
            L += [
                "### In the database, not in the extraction",
                "",
                "Entered by hand, or named differently on the site. Worth checking for duplicates.",
                "",
                "| Set | DB slug | Gang | Mem | Rel |",
                "|---|---|---|---|---|",
            ]
            for s in sorted(orphans, key=lambda s: s["name"].upper()):
                L.append(
                    f"| {s['name']} | `{s['slug']}` | {s['gang'] or '-'} | "
                    f"{s['members'] or '-'} | {s['relations'] or '-'} |"
                )
            L.append("")

    (ROOT / "db-sync.md").write_text("\n".join(L) + "\n")
    print(f"wrote {ROOT / 'db-sync.md'}")


if __name__ == "__main__":
    main()
