import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


class HistoryFieldChange(BaseModel):
    field: str
    old: Any = None
    new: Any = None
    # scalar: show old -> new. text: long prose, diffed word by word.
    # opaque: a blob (a polygon) shown only as "changed".
    kind: Literal["scalar", "text", "opaque"] = "scalar"


class HistoryActor(BaseModel):
    id: uuid.UUID
    email: str | None = None


class HistoryEntryRead(BaseModel):
    id: uuid.UUID
    created_at: datetime
    action: Literal["CREATE", "UPDATE", "DELETE"]
    actor: HistoryActor | None
    # The entity the audit row was written on. Equal to the requested entity
    # unless is_self is False: then this is the far side of a link (the
    # incident a member was added to, the member added to a set).
    entity_type: str
    entity_id: uuid.UUID
    is_self: bool
    # Set on link-change rows: which list changed ("sets", "participants", ...)
    # and the field in each row naming the far side ("set_id", "member_id").
    link: str | None = None
    link_key: str | None = None
    added: list[dict] = []
    removed: list[dict] = []
    changed: list[dict] = []
    # Set on snapshot rows: the column-level changes.
    changes: list[HistoryFieldChange] = []
    # True on the first UPDATE of an entity that predates the audit log: there
    # was no earlier snapshot to compare it with.
    baseline: bool = False


class HistoryLabel(BaseModel):
    type: str
    label: str
    slug: str | None = None


class HistoryPage(BaseModel):
    items: list[HistoryEntryRead]
    total: int
    # Names for every UUID the page mentions, keyed by UUID string.
    labels: dict[str, HistoryLabel]
