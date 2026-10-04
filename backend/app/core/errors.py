"""An error the client can act on: an HTTP status, a stable `code`, and extras.

FastAPI's HTTPException carries only `detail`, so the frontend could tell a
duplicate URL from any other 409 only by parsing English. Raise `ApiError`
instead and the response is `{"detail": ..., "code": ..., **extra}`, e.g.

    {"detail": "A source with this URL is already on file.",
     "code": "duplicate_url", "existing_id": "…"}
"""

import uuid
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, detail: str, **extra: Any):
        super().__init__(detail)
        self.status_code = status_code
        self.code = code
        self.detail = detail
        self.extra = {k: str(v) if isinstance(v, uuid.UUID) else v for k, v in extra.items()}


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code, **exc.extra},
    )
