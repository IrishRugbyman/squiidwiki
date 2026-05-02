import base64
import json
import uuid
from datetime import datetime
from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, BeforeValidator

from app.core.fuzzy_date import FuzzyDate

T = TypeVar("T")


def _coerce_fuzzy_date(v):
    if isinstance(v, dict):
        return FuzzyDate(**v)
    return v


FuzzyDateField = Annotated[FuzzyDate | None, BeforeValidator(_coerce_fuzzy_date)]


class CursorPage(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None
    total: int | None


class OffsetPage(BaseModel, Generic[T]):
    items: list[T]
    total: int


def make_cursor(created_at: datetime, id: uuid.UUID) -> str:
    payload = {"at": created_at.isoformat(), "id": str(id)}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def parse_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    payload = json.loads(base64.urlsafe_b64decode(cursor.encode()))
    return datetime.fromisoformat(payload["at"]), uuid.UUID(payload["id"])
