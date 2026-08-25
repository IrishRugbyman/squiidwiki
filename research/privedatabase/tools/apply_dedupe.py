"""Apply agent-adjudicated member merges, then report.

Input: a verdicts JSON produced by the dedupe-chicago-members workflow - one
verdict per duplicate-name group, each with zero or more merge clusters. Only
high- and medium-confidence merges are applied; low-confidence ones are
reported and left alone. A merged member keeps every set affiliation of the
records it absorbs (one man, several sets - the Chief Keef rule), the union of
aliases, and the strongest status.

Usage: python3 apply_dedupe.py <verdicts.json> [--go]
"""

import json
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

sys.path.insert(0, "/home/lbzgiu/squiidape/squiidwiki/research/privedatabase/tools")
from db_sync import norm  # noqa: E402

API = "http://localhost:8001/api/v1"
U = "59d23911-6fee-4156-8839-ac3c248a3b46"

STATUS_RANK = {"DEAD": 5, "LOCKED": 4, "ESCAPEE": 3, "ABSCONDER": 3, "FREE": 2, "UNKNOWN": 1}


def q(sql):
    """Run a query against squiidwiki_prod and return rows as JSON."""
    r = subprocess.run(
        [
            "psql",
            "-d",
            "squiidwiki_prod",
            "-t",
            "-A",
            "-c",
            f"SELECT coalesce(json_agg(t),'[]') FROM ({sql}) t;",
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode:
        sys.exit(f"psql failed: {r.stderr.strip()}")
    return json.loads(r.stdout)


class Api:
    """API client with login-on-401 (15-minute tokens)."""

    def __init__(self):
        """Log in immediately."""
        self.token = None
        self.login()

    def login(self):
        """Fetch a fresh admin access token."""
        body = json.dumps({"email": "admin@squiidwiki.dev", "password": "admin1234"}).encode()
        r = urllib.request.Request(
            f"{API}/auth/login",
            method="POST",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(r, timeout=30) as x:
            self.token = json.load(x)["access_token"]

    def call(self, method, path, payload=None, _retried=False):
        """Call the API; return the JSON body, or {"_error": code} on HTTP error."""
        r = urllib.request.Request(
            f"{API}/{path}",
            method=method,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"},
        )
        try:
            with urllib.request.urlopen(r, timeout=30) as x:
                raw = x.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            if e.code == 401 and not _retried:
                self.login()
                return self.call(method, path, payload, _retried=True)
            return {"_error": e.code, "_body": e.read()[:200].decode(errors="replace")}


def bad_alias(a, keep_nick):
    """An alias not worth carrying: empty, same as the nickname, or junk."""
    return not a or len(a) > 34 or norm(a) == norm(keep_nick) or " ou " in a or " fois" in a


def main():
    """Validate the verdicts, then apply high/medium-confidence merges."""
    verdicts = json.loads(pathlib.Path(sys.argv[1]).read_text())["verdicts"]
    go = "--go" in sys.argv

    members = {
        m["id"]: m
        for m in q(
            f"SELECT m.id, m.nickname, m.status, coalesce(m.aliases,'[]'::jsonb) aliases, "
            f"m.gang_id::text gid, m.alliance_id::text aid FROM member m "
            f"WHERE m.universe_id='{U}'"
        )
    }
    affil = {}
    for r in q(
        f"SELECT ms.member_id, ms.set_id, ms.is_primary, s.name FROM member_set ms "
        f"JOIN sets s ON s.id=ms.set_id JOIN member m ON m.id=ms.member_id "
        f"WHERE m.universe_id='{U}'"
    ):
        affil.setdefault(r["member_id"], []).append(r)

    planned, skipped, seen_absorbed = [], [], set()
    for v in verdicts:
        for mg in v["merges"]:
            keep, absorbs = mg["keep_id"], [a for a in mg["absorb_ids"] if a != mg["keep_id"]]
            if v["confidence"] == "low":
                skipped.append((v["key"], "low confidence"))
                continue
            if keep not in members or any(a not in members for a in absorbs) or not absorbs:
                skipped.append((v["key"], "unknown or empty ids"))
                continue
            if keep in seen_absorbed or any(a in seen_absorbed for a in absorbs):
                skipped.append((v["key"], "conflicts with an earlier merge"))
                continue
            seen_absorbed.update(absorbs)
            planned.append((v["key"], keep, absorbs, mg.get("primary_set")))

    print(
        f"verdicts: {len(verdicts)} groups; planned merges: {len(planned)}; skipped: {len(skipped)}"
    )
    for k, why in skipped:
        print(f"  skip {k}: {why}")
    if not go:
        for k, keep, absorbs, ps in planned[:15]:
            names = [members[x]["nickname"] for x in [keep, *absorbs]]
            print(f"  merge {k}: keep {names[0]}, absorb {names[1:]} (primary: {ps})")
        print("DRY RUN - re-run with --go")
        return

    api = Api()
    done = err = 0
    for _key, keep, absorbs, primary_set in planned:
        km = members[keep]
        rows = affil.get(keep, []) + [r for a in absorbs for r in affil.get(a, [])]
        by_set, primary_id = {}, None
        for r in rows:
            by_set.setdefault(r["set_id"], r)
            if primary_set and norm(r["name"]) == norm(primary_set):
                primary_id = r["set_id"]
        if primary_id is None:
            primary_id = next(
                (r["set_id"] for r in affil.get(keep, []) if r["is_primary"]),
                next(iter(by_set), None),
            )
        aliases, seen = [], {norm(km["nickname"] or "")}
        for src in [km, *(members[a] for a in absorbs)]:
            for a in [src["nickname"], *(src["aliases"] or [])]:
                if not bad_alias(a, km["nickname"]) and norm(a) not in seen:
                    aliases.append(a)
                    seen.add(norm(a))
        status = max(
            (m["status"] for m in [km, *(members[a] for a in absorbs)]),
            key=lambda s: STATUS_RANK.get(s, 0),
        )
        body = {"status": status, "aliases": aliases}
        if by_set:
            body["affiliations"] = [
                {"set_id": sid, "is_primary": sid == primary_id} for sid in by_set
            ]
        gid = km["gid"] or next((members[a]["gid"] for a in absorbs if members[a]["gid"]), None)
        aid = km["aid"] or next((members[a]["aid"] for a in absorbs if members[a]["aid"]), None)
        if gid:
            body["gang_id"] = gid
        if aid:
            body["alliance_id"] = aid
        x = api.call("PATCH", f"members/{keep}?universe_id={U}", body)
        if x.get("_error"):
            err += 1
            print(f"  PATCH fail {km['nickname']}: {x['_error']} {x.get('_body', '')[:100]}")
            continue
        ok = True
        for a in absorbs:
            d = api.call("DELETE", f"members/{a}?universe_id={U}")
            if d.get("_error"):
                ok = False
                print(f"  DELETE fail {members[a]['nickname']}: {d['_error']}")
        done += ok
    print(f"merged {done}/{len(planned)} clusters, {err} patch failures")


if __name__ == "__main__":
    main()
