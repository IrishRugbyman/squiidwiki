"""Read Reddit threads for the privedatabase corpus, through the Arctic Shift archive.

Reddit itself refuses this box: `www.reddit.com`, `old.reddit.com` and `oauth.reddit.com`
all return 403 to the server's IP (checked 2026-08-22), which is why the 1 Eye thread had
to be pasted in by hand. Arctic Shift is the Pushshift successor - an independent archive
of ~2.5B posts and comments - and it answers this IP with no key and no account.

    reddit_fetch.py thread https://www.reddit.com/r/Chiraqology/comments/pzbx9c/...
    reddit_fetch.py thread pzbx9c --json
    reddit_fetch.py posts Chiraqology --query "NLMB" --after 2015-01-01 --limit 50
    reddit_fetch.py comments --link-id pzbx9c --body "smith"
    reddit_fetch.py user dream-tha-menace9

Output is markdown on stdout, ready to read or to paste into a seed script's source notes;
`--json` gives the raw archive objects instead.

Two things to know before citing what comes back:

- It is an archive, not Reddit. Posts are captured when made, so `score` and `num_comments`
  are only correct after ~36h, deleted comments survive here as `[deleted]`, and anything
  newer than the archive's last sync is missing. This does not change the reliability rating:
  a forum thread is UNVERIFIED whether it is read here or on Reddit.
- Free service, shared, no uptime guarantee, and the search paths are not equally fast.
  Post search (`posts --query`) and anything scoped to one post (`thread`, `comments
  --link-id`) return in a second. Subreddit-wide *comment body* search does not work here
  at all - it times out on r/Chiraqology however hard you narrow the window - so the
  working shape is `posts --query` to find threads, then `thread` to read one whole.
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime

BASE = "https://arctic-shift.photon-reddit.com/api"
UA = "squiidwiki-research/1.0 (privedatabase corpus)"


SLOW_HINT = (
    "Comment body search is served by a slow full-text path and times out against an "
    "active subreddit no matter how far you narrow the window (checked on r/Chiraqology "
    "with a 2-month range and --limit 2). It only works scoped to one post:\n"
    "  reddit_fetch.py posts <sub> --query '<term>'    # find the threads (fast)\n"
    "  reddit_fetch.py thread <id>                     # then read one whole\n"
    "  reddit_fetch.py comments --link-id <id> --body '<term>'\n"
    "--author alone works too; --author with --body does not."
)


def _fail(path, err):
    """Exit on an archive-level error, adding the hint that actually helps for timeouts."""
    if "imeout" in err or "imed out" in err:
        sys.exit(f"{path}: {err}\n{SLOW_HINT}")
    sys.exit(f"{path}: {err}")


def _get(path, **params):
    """GET an Arctic Shift endpoint and return its `data`, exiting on an API-level error.

    Archive errors arrive both ways: a 200 carrying `{"error": ...}` and a 4xx whose body
    carries the same field (a query timeout comes back as 422), so both are unwrapped here.
    """
    params = {k: v for k, v in params.items() if v is not None}
    url = f"{BASE}/{path}?{urllib.parse.urlencode(params)}"
    for attempt in (1, 2):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                body = json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt == 1:
                wait = int(e.headers.get("X-RateLimit-Reset") or 10)
                print(f"rate limited, waiting {wait}s", file=sys.stderr)
                time.sleep(min(wait, 60))
                continue
            raw = e.read()[:400].decode(errors="replace")
            try:
                _fail(path, json.loads(raw).get("error") or raw)
            except json.JSONDecodeError:
                sys.exit(f"HTTP {e.code} from {path}: {raw}")
        except urllib.error.URLError as e:
            sys.exit(f"cannot reach Arctic Shift: {e.reason}")
        if body.get("error"):
            _fail(path, body["error"])
        return body.get("data") or []
    return []


def thing_id(s, kind="t3"):
    """Turn a Reddit URL, a prefixed id or a bare base36 id into a bare base36 id."""
    s = s.strip()
    if "reddit.com" in s or s.startswith("/r/"):
        m = re.search(r"/comments/([a-z0-9]+)", s)
        if not m:
            sys.exit(f"no post id in URL: {s}")
        return m.group(1)
    return s.removeprefix(f"{kind}_")


def when(obj):
    """Format a thing's `created_utc` as a UTC date."""
    ts = obj.get("created_utc")
    return datetime.fromtimestamp(ts, UTC).strftime("%Y-%m-%d") if ts else "?"


def score(obj):
    """Format a thing's score with an explicit sign, or '?' if it was never updated."""
    s = obj.get("score")
    return f"{s:+d}" if isinstance(s, int) else "?"


def _children(node):
    """Return the child nodes of a comment-tree node (the Reddit Listing shape).

    `replies` hangs off the node's `data`, not the node, and is absent rather than
    empty when a comment has no replies.
    """
    replies = node.get("data", {}).get("replies")
    if isinstance(replies, dict):
        return replies.get("data", {}).get("children") or []
    return []


def render_tree(nodes, depth=0, out=None):
    """Render a comment tree as an indented markdown list, keeping deleted bodies visible."""
    out = [] if out is None else out
    for node in nodes:
        if node.get("kind") == "more":
            n = len(node.get("data", {}).get("children") or [])
            out.append(f"{'  ' * depth}- _[{n} more comments collapsed]_")
            continue
        c = node.get("data", {})
        body = (c.get("body") or "").strip() or "[empty]"
        body = body.replace("\n", f"\n{'  ' * depth}  ")
        out.append(f"{'  ' * depth}- **u/{c.get('author')}** ({when(c)}, {score(c)}): {body}")
        render_tree(_children(node), depth + 1, out)
    return out


def cmd_thread(args):
    """Print a post and its full comment tree."""
    pid = thing_id(args.target)
    posts = _get("posts/ids", ids=pid, md2html="false")
    if not posts:
        sys.exit(f"post {pid} is not in the archive")
    p = posts[0]
    tree = _get("comments/tree", link_id=f"t3_{pid}", limit=args.limit)
    if args.json:
        print(json.dumps({"post": p, "comments": tree}, indent=2))
        return
    print(f"# {p.get('title')}\n")
    print(
        f"r/{p.get('subreddit')} | u/{p.get('author')} | {when(p)} | "
        f"score {score(p)} | {p.get('num_comments')} comments"
    )
    print(f"https://www.reddit.com/comments/{pid}\n")
    selftext = (p.get("selftext") or "").strip()
    if selftext:
        print(f"{selftext}\n")
    elif p.get("url"):
        print(f"Link post: {p['url']}\n")
    lines = render_tree(tree)
    print(f"## Comments ({len(lines)} rendered)\n")
    print("\n".join(lines) if lines else "_none in the archive_")
    print(f"\n_Retrieved from Arctic Shift on {datetime.now(UTC):%Y-%m-%d}._")


def cmd_posts(args):
    """Search posts in a subreddit or by author."""
    data = _get(
        "posts/search",
        subreddit=args.subreddit,
        author=args.author,
        query=args.query,
        title=args.title,
        after=args.after,
        before=args.before,
        limit=args.limit,
        sort=args.sort,
    )
    if args.json:
        print(json.dumps(data, indent=2))
        return
    for p in data:
        print(
            f"- {when(p)} r/{p.get('subreddit')} u/{p.get('author')} "
            f"({score(p)}, {p.get('num_comments')}c) {p.get('title')}\n"
            f"  https://www.reddit.com/comments/{p.get('id')}"
        )
    sys.stdout.flush()
    print(f"\n{len(data)} posts", file=sys.stderr)


def cmd_comments(args):
    """Search comments by subreddit, author, body text or parent post."""
    data = _get(
        "comments/search",
        subreddit=args.subreddit,
        author=args.author,
        body=args.body,
        link_id=thing_id(args.link_id) if args.link_id else None,
        after=args.after,
        before=args.before,
        limit=args.limit,
        sort=args.sort,
    )
    if args.json:
        print(json.dumps(data, indent=2))
        return
    for c in data:
        body = " ".join((c.get("body") or "").split())
        print(
            f"- {when(c)} r/{c.get('subreddit')} u/{c.get('author')} ({score(c)}): {body}\n"
            f"  https://www.reddit.com/comments/"
            f"{(c.get('link_id') or '').removeprefix('t3_')}/_/{c.get('id')}"
        )
    sys.stdout.flush()
    print(f"\n{len(data)} comments", file=sys.stderr)


def cmd_user(args):
    """Show where a user is active and what they most recently posted."""
    subs = _get("users/interactions/subreddits", author=args.author, limit=args.limit)
    if args.json:
        print(json.dumps(subs, indent=2))
        return
    print(f"# u/{args.author}\n\n## Active in\n")
    for s in subs:
        print(f"- r/{s.get('subreddit')}: {s.get('count')}")
    print("\n## Recent posts\n")
    for p in _get("posts/search", author=args.author, limit=10, sort="desc"):
        print(f"- {when(p)} r/{p.get('subreddit')}: {p.get('title')}")


def main():
    """Parse arguments and dispatch to a subcommand."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("thread", help="a post and its whole comment tree")
    t.add_argument("target", help="reddit URL, t3_id or bare post id")
    t.add_argument("--limit", type=int, default=9999, help="max comments (default: all)")
    t.set_defaults(fn=cmd_thread)

    p = sub.add_parser("posts", help="search posts")
    p.add_argument("subreddit", nargs="?", help="subreddit name, without r/")
    p.add_argument("--author")
    p.add_argument("--query", help="keyword search over title and selftext")
    p.add_argument("--title", help="keyword search over the title only")
    p.set_defaults(fn=cmd_posts)

    c = sub.add_parser("comments", help="search comments")
    c.add_argument("--subreddit")
    c.add_argument("--author")
    c.add_argument("--body", help="keyword search; needs a subreddit, author or link")
    c.add_argument("--link-id", help="restrict to one post (URL or id)")
    c.set_defaults(fn=cmd_comments)

    u = sub.add_parser("user", help="where a user is active")
    u.add_argument("author")
    u.set_defaults(fn=cmd_user)

    for x in (p, c):
        x.add_argument("--after", help="date, or an offset like 2y / 6m / 30d")
        x.add_argument("--before")
        x.add_argument("--sort", choices=("asc", "desc"), default="desc")
    for x in (p, c, u):
        x.add_argument("--limit", type=int, default=25)
    for x in (t, p, c, u):
        x.add_argument("--json", action="store_true", help="raw archive objects")

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
