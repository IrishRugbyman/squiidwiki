#!/usr/bin/env python
"""Dump every post of a professional Instagram account via Business Discovery.

Reads the Page token out of ``~/squiidape-ig/.env`` and walks the whole media
edge, writing ``<handle>.json`` (id, caption, timestamp, permalink, media_type,
like_count, comments_count) to the chosen output directory.

Two things make this less trivial than it looks:

* the ``business_discovery`` media edge returns ``paging.cursors.after`` but
  **no** ``paging.next`` link, so a loop that stops when ``next`` is missing
  silently keeps only the first page;
* the default page size is 100, which makes an account look far shallower than
  it is. Ask for ``media.limit(500)``.

Personal accounts are unreachable and come back as "Invalid user id" - that is
the account type, not a bug. See the repo CLAUDE.md, "Research sources for
Detroit", for what the resulting archives are and are not good for.

    python research/privedatabase/tools/fetch_ig_account.py thedetroitscanner -o /tmp
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ENV_PATH = Path.home() / "squiidape-ig" / ".env"
GRAPH = "https://graph.facebook.com/v21.0/"
FIELDS = "id,caption,timestamp,permalink,media_type,like_count,comments_count"


def load_env(path: Path) -> dict[str, str]:
    """Parse the KEY=VALUE lines of an .env file, ignoring comments."""
    env: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            env[key] = value.strip().strip('"')
    return env


def fetch_page(ig_id: str, token: str, handle: str, after: str | None) -> dict:
    """One business_discovery call, optionally continuing from a cursor."""
    media = f"media.limit(500).after({after})" if after else "media.limit(500)"
    fields = f"business_discovery.username({handle}){{username,media_count,{media}{{{FIELDS}}}}}"
    url = GRAPH + ig_id + "?" + urllib.parse.urlencode({"fields": fields, "access_token": token})
    with urllib.request.urlopen(url) as response:
        return json.load(response)


def fetch_all(ig_id: str, token: str, handle: str) -> tuple[list[dict], int | None]:
    """Walk the full media edge. Returns the posts and the account's media_count."""
    posts: list[dict] = []
    after: str | None = None
    media_count: int | None = None
    while True:
        discovery = fetch_page(ig_id, token, handle, after)["business_discovery"]
        media_count = discovery.get("media_count", media_count)
        media = discovery["media"]
        posts.extend(media["data"])
        after = media.get("paging", {}).get("cursors", {}).get("after")
        # No paging.next here - the cursor plus an empty page is the only end signal.
        if not after or not media["data"]:
            return posts, media_count
        print(f"  {len(posts)} posts...", file=sys.stderr)


def main() -> None:
    """Fetch one account and write it to disk."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("handle", help="professional account to read, without the @")
    parser.add_argument("-o", "--out-dir", default=".", help="where to write <handle>.json")
    args = parser.parse_args()

    env = load_env(ENV_PATH)
    posts, media_count = fetch_all(env["IG_BUSINESS_ACCOUNT_ID"], env["FB_PAGE_TOKEN"], args.handle)
    posts.sort(key=lambda post: post["timestamp"])
    print(f"{len(posts)} posts fetched (media_count {media_count})", file=sys.stderr)

    out = Path(args.out_dir) / f"{args.handle}.json"
    out.write_text(json.dumps(posts, indent=1))
    print(out)


if __name__ == "__main__":
    main()
