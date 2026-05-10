"""Tiny ETag/304 helper. Compute a stable hash from any stringifiable inputs;
compare against the request's If-None-Match and short-circuit with 304.
"""
import hashlib
from datetime import datetime
from typing import Iterable

from fastapi import HTTPException, Request, Response


def make_etag(*parts: object) -> str:
    """SHA1 of the joined string representations. Quoted per RFC 7232."""
    h = hashlib.sha1()
    for p in parts:
        if p is None:
            h.update(b"\x00")
        elif isinstance(p, datetime):
            h.update(p.isoformat().encode())
        else:
            h.update(str(p).encode())
        h.update(b"|")
    return f'W/"{h.hexdigest()}"'


def check_etag(request: Request, response: Response, etag: str) -> None:
    """Set the response ETag and raise 304 if the client already has it.

    Compares against If-None-Match. The header may contain multiple comma-separated
    entries; we strip whitespace and exact-match.
    """
    response.headers["ETag"] = etag
    inm = request.headers.get("if-none-match")
    if not inm:
        return
    candidates: Iterable[str] = (c.strip() for c in inm.split(","))
    if etag in candidates:
        # 304 must echo ETag so caches stay coherent.
        raise HTTPException(status_code=304, headers={"ETag": etag})
