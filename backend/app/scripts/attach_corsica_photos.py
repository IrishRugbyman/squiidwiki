"""Attach photographs to the Corsica members.

Deliberately table-driven and empty by default. No freely-licensed photograph
exists for any of these nine people: French Wikipedia explicitly flags the
absence for Robert Moracchini, the best-documented of them, and a Commons
search turns up nothing for the Brise de Mer at all. What exists is copyrighted
press photography, and a URL does not prove whose face is in it. These pages
carry murder accusations against named people with living relatives, so the
identification has to be made by a person who can actually recognise them, not
guessed at from a search result.

So: fill in PHOTOS with sources you have checked, then run it. Each entry needs
a caption naming the photograph's origin, because an unattributed portrait on a
page like this is worth very little.

Images are downloaded and pushed to R2 through the normal media CRUD, which
also builds the thumbnail and marks the first photo for an entity primary.
Hotlinking is avoided on purpose: press URLs rot, and a broken portrait on a
member page reads as a mistake.

Run from backend/:
  .venv/bin/python -m app.scripts.attach_corsica_photos          # dry run
  .venv/bin/python -m app.scripts.attach_corsica_photos --apply
"""

import argparse
import asyncio
import mimetypes
import sys
import uuid
from pathlib import Path

import httpx
from sqlalchemy import select, text

from app.core.database import _session_factories
from app.crud.media import create_media
from app.models import Media, Member

UNIVERSE_SLUG = "corsica"

# (member legal_name, url-or-local-path, caption)
# The caption must say where the photograph came from.
PHOTOS: list[tuple[str, str, str]] = [
    # ("Robert Moracchini", "https://…/moracchini.jpg", "Corse-Matin, 30 March 2025."),
]


async def _load(ref: str) -> tuple[bytes, str, str]:
    """Return (bytes, filename, content_type) for a URL or a local path."""
    if ref.startswith(("http://", "https://")):
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as c:
            r = await c.get(ref, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            ctype = r.headers.get("content-type", "").split(";")[0].strip()
            if not ctype.startswith("image/"):
                raise ValueError(f"not an image ({ctype or 'no content-type'}): {ref}")
            return r.content, ref.rsplit("/", 1)[-1] or "photo", ctype
    p = Path(ref)
    if not p.exists():
        raise FileNotFoundError(ref)
    ctype = mimetypes.guess_type(p.name)[0] or "image/jpeg"
    return p.read_bytes(), p.name, ctype


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write to the database and R2")
    args = ap.parse_args()
    dry = not args.apply

    if not PHOTOS:
        print(
            "PHOTOS is empty. Add entries you have verified, then re-run.\n"
            "See the module docstring for why this is not pre-filled.",
            file=sys.stderr,
        )
        return 1

    async with _session_factories["prod"]() as s:
        row = (
            await s.execute(
                text("SELECT id FROM universe WHERE slug = :slug"), {"slug": UNIVERSE_SLUG}
            )
        ).first()
        if row is None:
            print(f"Universe '{UNIVERSE_SLUG}' not found", file=sys.stderr)
            return 1
        uni: uuid.UUID = row[0]

        actor_row = (
            await s.execute(
                text(
                    "SELECT id, email FROM users WHERE global_role = 'ADMIN' "
                    "ORDER BY created_at LIMIT 1"
                )
            )
        ).first()
        if actor_row is None:
            print("No ADMIN user to attribute the upload to", file=sys.stderr)
            return 1
        actor: uuid.UUID = actor_row[0]

        failures = 0
        for legal_name, ref, caption in PHOTOS:
            member = (
                (
                    await s.execute(
                        select(Member).where(
                            Member.universe_id == uni, Member.legal_name == legal_name
                        )
                    )
                )
                .scalars()
                .first()
            )
            if member is None:
                print(f"  ! no member named {legal_name!r}", file=sys.stderr)
                failures += 1
                continue

            already = (
                (await s.execute(select(Media).where(Media.member_id == member.id)))
                .scalars()
                .first()
            )
            if already is not None:
                print(f"  = {legal_name} already has media, skipping")
                continue

            if dry:
                print(f"  + {legal_name} <- {ref}")
                continue

            try:
                data, filename, ctype = await _load(ref)
            except Exception as exc:  # noqa: BLE001 - report and carry on
                print(f"  ! {legal_name}: {exc}", file=sys.stderr)
                failures += 1
                continue

            await create_media(
                s,
                universe_id=uni,
                member_id=member.id,
                file_bytes=data,
                original_filename=filename,
                content_type=ctype,
                caption=caption,
                actor_id=actor,
            )
            print(f"  + {legal_name} <- {filename} ({len(data) // 1024} KB)")

    if dry:
        print("\nDRY RUN, nothing written. Re-run with --apply.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
