import uuid
from datetime import UTC, date, datetime

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.core.enums import SourceReliability


class Source(SQLModel, table=True):
    __tablename__ = "source"
    __table_args__ = (
        sa.Index("ix_source_universe_url_norm", "universe_id", "url_norm"),
        # One source per custody lookup system per universe: the BOP locator,
        # OTIS and the GDC query are each a single source, and the person's
        # number sits on the citation (see app/scripts/merge_lookup_sources.py).
        sa.Index(
            "uq_source_universe_lookup_system",
            "universe_id",
            "lookup_system",
            unique=True,
            postgresql_where=sa.text("lookup_system IS NOT NULL"),
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)
    url: str
    # `app.core.sources.normalise_url(url)`, kept by crud on every write: what
    # the duplicate check and the paste-a-URL lookup compare.
    url_norm: str = Field(sa_column=Column(String, nullable=False, server_default=""))
    title: str
    publication: str | None = None
    # none_as_null: without it a None is stored as the JSON value 'null', which
    # `IS NULL` does not see (384 rows were, until migration 4a89130f7a88).
    published_at: dict | None = Field(default=None, sa_column=Column(JSONB(none_as_null=True)))
    accessed_at: date | None = None
    reliability: SourceReliability = SourceReliability.UNVERIFIED
    # VARCHAR, not a Postgres enum (the media.kind asyncpg pitfall). Values are
    # `app.core.sources.SourceKind`; derived from the URL unless set by hand.
    kind: str = Field(
        default="OTHER", sa_column=Column(String, nullable=False, server_default="OTHER")
    )
    # `app.core.sources.LookupSystem` for a custody lookup source, else None.
    lookup_system: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    notes: str | None = None
    archive_url: str | None = None
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    created_by_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
