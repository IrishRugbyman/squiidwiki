import re
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


_HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


def _validate_color(v: Optional[str]) -> Optional[str]:
    if v is None or v == "":
        return None
    if not _HEX_COLOR_RE.match(v):
        raise ValueError("color must be a hex string like #RRGGBB or #RRGGBBAA")
    return v.lower()


class GangCreate(BaseModel):
    universe_id: uuid.UUID
    name: str
    aliases: Optional[list[str]] = None
    description: Optional[str] = None
    color: Optional[str] = None
    color_secondary: Optional[str] = None

    @field_validator("color", "color_secondary")
    @classmethod
    def _color(cls, v):
        return _validate_color(v)


class GangUpdate(BaseModel):
    name: Optional[str] = None
    aliases: Optional[list[str]] = None
    description: Optional[str] = None
    color: Optional[str] = None
    color_secondary: Optional[str] = None

    @field_validator("color", "color_secondary")
    @classmethod
    def _color(cls, v):
        return _validate_color(v)


class GangRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    name: str
    slug: Optional[str] = None
    aliases: Optional[list[str]] = None
    description: Optional[str] = None
    color: Optional[str] = None
    color_secondary: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class GangListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    name: str
    slug: Optional[str] = None
    aliases: Optional[list[str]] = None
    description: Optional[str] = None
    color: Optional[str] = None
    color_secondary: Optional[str] = None
