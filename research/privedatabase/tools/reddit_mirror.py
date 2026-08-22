"""Mirror a subreddit into local SQLite so research stops depending on the archive being up.

Arctic Shift is the only Reddit source this box can reach - reddit.com, old.reddit.com,
oauth.reddit.com, PullPush and every redlib mirror tried all return 403 to this IP - and it
rate-limits hard enough to block a working session. The fix is not another API, it is to
stop making the same request twice.

The archive's own download tool does exactly this: it pages `posts/search` and
`comments/search` with `limit=auto`, which returns 100-1000 rows per call instead of the 25
you get by default, and writes them to disk. This does the same into SQLite, resumably, one
request at a time with backoff, and then every later question is answered locally with no
network at all.

    reddit_mirror.py pull Chiraqology --kind posts
    reddit_mirror.py pull Chiraqology --kind comments --after 2020-01-01
    reddit_mirror.py status
    reddit_mirror.py search "NLMB" --subreddit Chiraqology       # titles + selftext
    reddit_mirror.py search "Cortez Bailey" --comments           # comment bodies
    reddit_mirror.py thread pzbx9c                               # straight from the mirror

`pull` is resumable: it records how far it got per subreddit and kind, so re-running
continues rather than restarting, and interrupting it loses nothing but the current page.
Comment body search - the thing the live API cannot do at all for a busy subreddit, because
it times out however far you narrow it - is a plain SQL LIKE here and returns instantly.

The database lives outside the repo, at ~/.cache/squiidwiki/reddit-mirror.db, because it is
a cache: it is rebuildable from the archive and has no business in git.
"""

import argparse
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime

BASE = "https://arctic-shift.photon-reddit.com/api"
UA = "squiidwiki-research/1.0 (privedatabase corpus)"
DB = os.path.expanduser("~/.cache/squiidwiki/reddit-mirror.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS post (
  id TEXT PRIMARY KEY, subreddit TEXT, created_utc INTEGER, author TEXT,
  title TEXT, selftext TEXT, score INTEGER, num_comments INTEGER, url TEXT
);
CREATE TABLE IF NOT EXISTS comment (
  id TEXT PRIMARY KEY, subreddit TEXT, created_utc INTEGER, author TEXT,
  body TEXT, score INTEGER, link_id TEXT, parent_id TEXT
);
CREATE TABLE IF NOT EXISTS progress (
  subreddit TEXT, kind TEXT, cursor INTEGER, updated_at TEXT,
  PRIMARY KEY (subreddit, kind)
);
CREATE INDEX IF NOT EXISTS post_sub_time ON post(subreddit, created_utc);
CREATE INDEX IF NOT EXISTS comment_sub_time ON comment(subreddit, created_utc);
CREATE INDEX IF NOT EXISTS comment_link ON comment(link_id);
"""

POST_FIELDS = "id,subreddit,created_utc,author,title,selftext,score,num_comments,url"
COMMENT_FIELDS = "id,subreddit,created_utc,author,body,score,link_id,parent_id"


def db():
    """Open the mirror, creating it and its schema on first use."""
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)
    return con


def get(path, **params):
    """One archive call, retrying politely on a rate limit or a timeout."""
    url = f"{BASE}/{path}?{urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})}"
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as r:
                body = json.load(r)
            if body.get("error"):
                raise RuntimeError(body["error"])
            return body.get("data") or []
        except urllib.error.HTTPError as e:
            raw = e.read()[:200].decode(errors="replace")
            wait = int(e.headers.get("X-RateLimit-Reset") or 0) or min(8 * 2**attempt, 120)
            print(f"    HTTP {e.code} ({raw[:60]}), waiting {wait}s", file=sys.stderr)
            time.sleep(wait)
        except Exception as e:
            wait = min(8 * 2**attempt, 120)
            print(f"    {e}, waiting {wait}s", file=sys.stderr)
            time.sleep(wait)
    return None


def pull(args):
    """Page a subreddit into the mirror, continuing from wherever the last run stopped."""
    con = db()
    kinds = ["posts", "comments"] if args.kind == "both" else [args.kind]
    for kind in kinds:
        row = con.execute(
            "SELECT cursor FROM progress WHERE subreddit=? AND kind=?", (args.subreddit, kind)
        ).fetchone()
        after = (
            row[0]
            if row and not args.restart
            else int(datetime.fromisoformat(args.after).replace(tzinfo=UTC).timestamp())
        )
        before = int(datetime.fromisoformat(args.before).replace(tzinfo=UTC).timestamp())
        path = f"{kind}/search"
        fields = POST_FIELDS if kind == "posts" else COMMENT_FIELDS
        total = 0
        print(
            f"pulling r/{args.subreddit} {kind} from {datetime.fromtimestamp(after, UTC):%Y-%m-%d}"
        )
        while after < before:
            rows = get(
                path,
                subreddit=args.subreddit,
                after=after,
                before=before,
                limit="auto",
                sort="asc",
                fields=fields,
            )
            if rows is None:
                print("  giving up after repeated failures; progress is saved", file=sys.stderr)
                break
            if not rows:
                con.execute(
                    "INSERT OR REPLACE INTO progress VALUES (?,?,?,?)",
                    (args.subreddit, kind, before, datetime.now(UTC).isoformat()),
                )
                con.commit()
                print(f"  done, {total} new {kind}")
                break
            if kind == "posts":
                con.executemany(
                    "INSERT OR REPLACE INTO post VALUES (:id,:subreddit,:created_utc,:author,"
                    ":title,:selftext,:score,:num_comments,:url)",
                    [{k: r.get(k) for k in POST_FIELDS.split(",")} for r in rows],
                )
            else:
                con.executemany(
                    "INSERT OR REPLACE INTO comment VALUES (:id,:subreddit,:created_utc,:author,"
                    ":body,:score,:link_id,:parent_id)",
                    [{k: r.get(k) for k in COMMENT_FIELDS.split(",")} for r in rows],
                )
            total += len(rows)
            newest = max(r["created_utc"] for r in rows)
            # +1 so the newest row is not fetched again; a whole second of ties is the
            # worst case and INSERT OR REPLACE makes a repeat harmless.
            after = newest + 1
            con.execute(
                "INSERT OR REPLACE INTO progress VALUES (?,?,?,?)",
                (args.subreddit, kind, after, datetime.now(UTC).isoformat()),
            )
            con.commit()
            print(
                f"  +{len(rows):<5} total {total:<7} at {datetime.fromtimestamp(after, UTC):%Y-%m-%d}"
            )
            time.sleep(args.delay)


def status(args):
    """Show what the mirror holds."""
    con = db()
    print(f"{DB}  ({os.path.getsize(DB) / 1e6:.1f} MB)\n" if os.path.exists(DB) else "empty\n")
    for table in ("post", "comment"):
        rows = con.execute(
            f"SELECT subreddit, count(*), min(created_utc), max(created_utc) "
            f"FROM {table} GROUP BY subreddit ORDER BY 2 DESC"
        ).fetchall()
        for sub, n, lo, hi in rows:
            print(
                f"  {table:8s} r/{sub:<16} {n:>8,}  "
                f"{datetime.fromtimestamp(lo, UTC):%Y-%m-%d} .. {datetime.fromtimestamp(hi, UTC):%Y-%m-%d}"
            )
    for sub, kind, cur, at in con.execute("SELECT * FROM progress"):
        print(
            f"  cursor   r/{sub:<16} {kind:<9} {datetime.fromtimestamp(cur, UTC):%Y-%m-%d}  (run {at[:10]})"
        )


def search(args):
    """Search the mirror. This is the part the live API cannot do."""
    con = db()
    like = f"%{args.query}%"
    if args.comments:
        sql = (
            "SELECT created_utc, subreddit, author, body, link_id, id FROM comment "
            "WHERE body LIKE ?"
        )
        params = [like]
        if args.subreddit:
            sql += " AND subreddit=?"
            params.append(args.subreddit)
        sql += " ORDER BY created_utc DESC LIMIT ?"
        params.append(args.limit)
        for ts, sub, author, body, link, cid in con.execute(sql, params):
            print(
                f"- {datetime.fromtimestamp(ts, UTC):%Y-%m-%d} r/{sub} u/{author}: "
                f"{' '.join((body or '').split())[:220]}"
            )
            print(f"  https://www.reddit.com/comments/{(link or '').removeprefix('t3_')}/_/{cid}")
    else:
        sql = (
            "SELECT created_utc, subreddit, author, title, selftext, score, num_comments, id "
            "FROM post WHERE (title LIKE ? OR selftext LIKE ?)"
        )
        params = [like, like]
        if args.subreddit:
            sql += " AND subreddit=?"
            params.append(args.subreddit)
        sql += " ORDER BY created_utc DESC LIMIT ?"
        params.append(args.limit)
        for ts, sub, author, title, _body, score, ncom, pid in con.execute(sql, params):
            print(
                f"- {datetime.fromtimestamp(ts, UTC):%Y-%m-%d} r/{sub} u/{author} "
                f"({score:+d}, {ncom}c) {title}"
            )
            print(f"  https://www.reddit.com/comments/{pid}")


def thread(args):
    """Print a post and its comments straight out of the mirror."""
    con = db()
    p = con.execute(
        "SELECT title, author, created_utc, score, num_comments, selftext, url "
        "FROM post WHERE id=?",
        (args.id,),
    ).fetchone()
    if not p:
        sys.exit(f"post {args.id} is not in the mirror - pull its subreddit first")
    title, author, ts, score, ncom, selftext, url = p
    print(f"# {title}\n")
    print(f"u/{author} | {datetime.fromtimestamp(ts, UTC):%Y-%m-%d} | {score:+d} | {ncom} comments")
    if (selftext or "").strip():
        print(f"\n{selftext.strip()}")
    elif url:
        print(f"\nLink: {url}")
    rows = con.execute(
        "SELECT author, created_utc, score, body FROM comment WHERE link_id IN (?,?) "
        "ORDER BY created_utc",
        (args.id, f"t3_{args.id}"),
    ).fetchall()
    print(f"\n## Comments ({len(rows)} in mirror)\n")
    for a, cts, cs, body in rows:
        print(
            f"- **u/{a}** ({datetime.fromtimestamp(cts, UTC):%Y-%m-%d}, {cs:+d}): "
            f"{' '.join((body or '').split())[:400]}"
        )


def main():
    """Parse arguments and dispatch."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("pull", help="mirror a subreddit into SQLite (resumable)")
    p.add_argument("subreddit")
    p.add_argument("--kind", choices=("posts", "comments", "both"), default="posts")
    p.add_argument("--after", default="2005-01-01")
    p.add_argument("--before", default=datetime.now(UTC).strftime("%Y-%m-%d"))
    p.add_argument("--delay", type=float, default=1.5, help="seconds between calls")
    p.add_argument("--restart", action="store_true", help="ignore the saved cursor")
    p.set_defaults(fn=pull)

    s = sub.add_parser("status", help="what the mirror holds")
    s.set_defaults(fn=status)

    q = sub.add_parser("search", help="search the mirror offline")
    q.add_argument("query")
    q.add_argument("--subreddit")
    q.add_argument("--comments", action="store_true", help="search comment bodies")
    q.add_argument("--limit", type=int, default=25)
    q.set_defaults(fn=search)

    t = sub.add_parser("thread", help="a post and its comments from the mirror")
    t.add_argument("id")
    t.set_defaults(fn=thread)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
