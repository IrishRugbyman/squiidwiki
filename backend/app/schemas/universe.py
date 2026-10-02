import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

# The frontend puts the universe slug first in every URL (/michigan/members/x),
# beside its own top-level pages. A universe slugged like one of those would be
# unreachable or would swallow the page, and old links (/members/x) are told
# apart from a universe by these names. Keep in step with frontend/src/routes
# and SCOPED_SECTIONS in frontend/src/lib/universeRoutes.ts.
RESERVED_UNIVERSE_SLUGS = frozenset(
    {
        "admin",
        "api",
        "assets",
        "audit",
        "login",
        "profile",
        "universes",
        "alliances",
        "calendar",
        "gangs",
        "incidents",
        "map",
        "members",
        "municipalities",
        "research",
        "sets",
        "sources",
        "timeline",
    }
)


def _check_slug(slug: Optional[str]) -> Optional[str]:
    if slug is not None and slug.strip().lower() in RESERVED_UNIVERSE_SLUGS:
        raise ValueError(f"{slug!r} is reserved: it names a page of the site")
    return slug


class UniverseCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None

    _slug = field_validator("slug")(_check_slug)


class UniverseUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None

    _slug = field_validator("slug")(_check_slug)


class UniverseRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str]
    created_at: datetime


class UniverseListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: str
