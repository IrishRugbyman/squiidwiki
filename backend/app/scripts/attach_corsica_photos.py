"""Attach photographs to the Corsica members.

Only two of the nine have a photograph, and that is not for want of looking.
Searched via a real browser: French Wikipedia flags the absence for Robert
Moracchini with its "illustration sous licence libre serait bienvenue"
placeholder, Commons has nothing for the Brise de Mer, and an image search on
Seatelli, Ziglioli and Louis Memmi returns pure noise, since they belong to
1981-98 and never reached the indexed web. The French press also routinely
illustrates these stories with stock photos rather than the subject: both the
Police & Realites and 20 Minutes pieces on Moracchini's killing use one, the
latter captioned "Image d'illustration". Those were rejected.

Every entry here was opened in the browser and looked at, not taken on trust
from a filename or an alt attribute. A URL does not prove whose face is in the
image, and these pages carry murder accusations against named people with
living relatives. Anything that could not be confirmed was left out rather than
guessed at, and each caption says where the photograph came from and how far it
can be trusted.

Images are downloaded and pushed to R2 through the normal media CRUD, which
also builds the thumbnail and marks the first photo for an entity primary.
Hotlinking is avoided on purpose: press URLs rot, and a broken portrait on a
member page reads as a mistake.

Idempotent: a member that already has media is skipped.

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
    (
        "Pierre-Marie Santucci",
        "https://s.france24.com/media/display/bc0cd8f6-162f-11e9-b43f-005056a964fe"
        "/w:1024/p:16x9/0210-santucci_m.webp",
        "Archive photograph published by France 24 with its report of his killing, "
        "10 February 2009. Undated, and shows him under gendarme escort: the setting "
        "and the black curls match the custody photograph described in Lazard & "
        "Galland, Vendetta.",
    ),
    (
        "Robert Moracchini",
        "https://www.corsenetinfos.corsica/photo/art/grande/72955048-50760898.jpg",
        "On the summit of Everest with the Corsican bandera, May 2023, aged 63. "
        "Published by Corse Net Infos, credited Thamserku Expedition. His face is "
        "covered by mask and goggles, so this identifies the moment rather than the "
        "man: it is here because the climb is the defining fact of his last years, "
        "not as a likeness.",
    ),
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
