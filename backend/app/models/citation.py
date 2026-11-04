"""A citation: one source backing one record, with what it supports.

Before 2026-10-04 citations lived in six link tables (member_source,
incident_source, set_source, municipality_source, court_case_source,
business_source) that said only "this record cites this source": no order, no
page, no quote, no note of what the source establishes. This table replaces
them (migration `4a89130f7a88`); the old tables are gone.

Shaped like `media`: one nullable foreign key per kind of record and a CHECK
that exactly one is set, so every link is a real foreign key that cascades
when its record is deleted. A source cannot be deleted while it is cited
(RESTRICT): `crud.source.delete_source` removes its citations explicitly, so
the audit log records each one.
"""

import uuid
from datetime import UTC, date, datetime

import sqlalchemy as sa
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

# The records a citation can belong to, as (entity type, column, table). The
# entity type is what the API speaks; the order is the order the source page
# lists them in.
CITATION_TARGETS: tuple[tuple[str, str, str], ...] = (
    ("member", "member_id", "member"),
    ("incident", "incident_id", "incident"),
    ("set", "set_id", "sets"),
    ("alliance", "alliance_id", "alliance"),
    ("rap_group", "rap_group_id", "rap_group"),
    ("court_case", "court_case_id", "court_case"),
    ("municipality", "municipality_id", "municipality"),
    ("business", "business_id", "business"),
)
TARGET_COLUMN = {entity: column for entity, column, _ in CITATION_TARGETS}


def _target(table: str) -> Column:
    return Column(sa.Uuid(), sa.ForeignKey(f"{table}.id", ondelete="CASCADE"), nullable=True)


class Citation(SQLModel, table=True):
    __tablename__ = "citation"
    __table_args__ = (
        sa.CheckConstraint(
            "num_nonnulls(member_id, incident_id, set_id, alliance_id, rap_group_id, "
            "court_case_id, municipality_id, business_id) = 1",
            name="ck_citation_exactly_one_target",
        ),
        # One citation per source per record: two pages of the same filing are
        # one locator ("pp. 3, 17"), not two rows.
        *(
            sa.Index(
                f"uq_citation_{column}_source",
                column,
                "source_id",
                unique=True,
                postgresql_where=sa.text(f"{column} IS NOT NULL"),
            )
            for _, column, _ in CITATION_TARGETS
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # Always the source's universe, which is always the record's: a citation
    # never crosses universes (checked in crud.citation).
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)
    source_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid(),
            sa.ForeignKey("source.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
    )

    member_id: uuid.UUID | None = Field(default=None, sa_column=_target("member"))
    incident_id: uuid.UUID | None = Field(default=None, sa_column=_target("incident"))
    set_id: uuid.UUID | None = Field(default=None, sa_column=_target("sets"))
    alliance_id: uuid.UUID | None = Field(default=None, sa_column=_target("alliance"))
    rap_group_id: uuid.UUID | None = Field(default=None, sa_column=_target("rap_group"))
    court_case_id: uuid.UUID | None = Field(default=None, sa_column=_target("court_case"))
    municipality_id: uuid.UUID | None = Field(default=None, sa_column=_target("municipality"))
    business_id: uuid.UUID | None = Field(default=None, sa_column=_target("business"))

    # Where in the source: a page, a paragraph, a timestamp, or for a custody
    # lookup the record number ("12345-678", "#654321").
    locator: str | None = None
    # The words in the source that carry the claim.
    quote: str | None = None
    # What this source establishes for this record, in the researcher's words.
    note: str | None = None
    # Display order within the record's citations, 0 first.
    position: int = Field(
        default=0, sa_column=Column(sa.Integer, nullable=False, server_default="0")
    )
    # When the source was read for this record; a lookup page is read once per
    # person, so the date belongs here rather than on the source.
    accessed_at: date | None = None

    created_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    created_by_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )

    def target(self) -> tuple[str, uuid.UUID]:
        """The (entity type, id) this citation belongs to."""
        for entity, column, _ in CITATION_TARGETS:
            value = getattr(self, column)
            if value is not None:
                return entity, value
        raise ValueError("citation has no target")
