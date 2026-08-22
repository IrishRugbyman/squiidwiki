"""Shared helpers for the privedatabase seed scripts: admin API client + psql query.

Every seed/repair script talks to the local SquiidWiki backend on :8001 with the
dev admin account and reads reference data straight from squiidwiki_prod.
"""

import json
import subprocess
import sys
import urllib.error
import urllib.request

API = "http://localhost:8001/api/v1"
CHICAGO = "59d23911-6fee-4156-8839-ac3c248a3b46"


def q(sql, db="squiidwiki_prod"):
    """Run a query and return its rows as a list of dicts."""
    r = subprocess.run(
        ["psql", "-d", db, "-t", "-A", "-c", f"SELECT coalesce(json_agg(t),'[]') FROM ({sql}) t;"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        sys.exit(f"psql failed: {r.stderr.strip()}")
    return json.loads(r.stdout)


class Api:
    """API client that logs in and transparently re-logs-in on 401 (15-min tokens)."""

    def __init__(self):
        """Log in immediately so the first call carries a token."""
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
        """Call the API; return the JSON body, or {"_error": code, "_body": text} on HTTP error."""
        r = urllib.request.Request(
            f"{API}/{path}",
            method=method,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            },
        )
        try:
            with urllib.request.urlopen(r, timeout=60) as x:
                raw = x.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            if e.code == 401 and not _retried:
                self.login()
                return self.call(method, path, payload, _retried=True)
            return {"_error": e.code, "_body": e.read()[:300].decode(errors="replace")}
