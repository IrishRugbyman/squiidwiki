import base64
import json
import uuid
from datetime import datetime
from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, BeforeValidator, field_validator

from app.core.fuzzy_date import FuzzyDate

T = TypeVar("T")


def _coerce_fuzzy_date(v):
    if isinstance(v, dict):
        return FuzzyDate(**v)
    return v


FuzzyDateField = Annotated[FuzzyDate | None, BeforeValidator(_coerce_fuzzy_date)]


def refuse_null(*fields: str):
    """A PATCH validator refusing an explicit null for fields that cannot be empty.

    An Update schema types every field Optional so that it can be left out,
    and the CRUD applies what was sent with exclude_unset. A field sent as
    null therefore reached a NOT NULL column and failed on flush: a 500. Null
    is not a value these columns hold, so it is bad input, a 422; leaving the
    field out keeps the current value. Use as a class attribute:

        _required = refuse_null("type", "verified")
    """

    def _check(cls, v):
        if v is None:
            raise ValueError("cannot be null; leave the field out to keep its value")
        return v

    return field_validator(*fields)(classmethod(_check))


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
