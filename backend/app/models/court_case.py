import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy import CheckConstraint, Column, DateTime, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlmodel import Field, SQLModel


class CourtCase(SQLModel, table=True):
    """One prosecution or suit, as a court filed it.

    A case belongs to one universe: where its court sits when a universe exists
    for that place, otherwise the universe most of its defendants come from.
    Its defendants and the incidents it covers can come from any universe, the
    same rule incident participants follow; its sets and sources are its own
    universe's.

    `court` plus `docket` identify the case and are unique together when the
    docket is known (a French trial is often known by name alone). Every other
    spelling of the docket that turns up, in OTIS, in a case file, with or
    without the court in brackets, goes in `docket_aliases`, so it resolves to
    this row instead of minting a second one. `jurisdiction`, `kind` and the
    defendant's `disposition` are enum values stored as VARCHAR, like
    `member_custody_id.system`, so a new value is a code change.
    """

    __tablename__ = "court_case"
    __table_args__ = (
        sa.Index("uq_court_case_universe_slug", "universe_id", "slug", unique=True),
        sa.Index(
            "uq_court_case_court_docket",
            "court",
            "docket",
            unique=True,
            postgresql_where=sa.text("docket IS NOT NULL"),
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)
    name: str = Field(index=True)
    slug: str | None = Field(default=None, index=True)
    jurisdiction: str = Field(sa_column=Column(String, nullable=False))
    kind: str = Field(sa_column=Column(String, nullable=False, server_default="CRIMINAL"))
    court: str = Field(sa_column=Column(String, nullable=False))
    docket: str | None = None
    docket_aliases: list[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String), nullable=False, server_default="{}"),
    )
    # The appeal of a trial, the indictment a complaint became, the copy of a
    # case another district opened on a Rule 5 arrest.
    parent_case_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            sa.Uuid(), sa.ForeignKey("court_case.id", ondelete="SET NULL"), nullable=True
        ),
    )
    filed_at: dict | None = Field(default=None, sa_column=Column(JSONB(none_as_null=True)))
    closed_at: dict | None = Field(default=None, sa_column=Column(JSONB(none_as_null=True)))
    judge: str | None = None
    # Under the biography rule: what no column holds (the enterprise the
    # indictment describes, how the case was built), never the defendants, the
    # dates or the court.
    summary: str | None = None
    # One case can span several CourtListener dockets (a magistrate number, the
    # criminal number, an appeal).
    courtlistener_ids: list[int] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(sa.Integer), nullable=False, server_default="{}"),
    )
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    created_by_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")


class CourtCaseDefendant(SQLModel, table=True):
    """One person charged in a case, and what became of the charges.

    `member_id` is empty for a defendant the wiki has no member for yet ("D-7"),
    who then carries a `label`; one of the two is always set. Deleting a member
    keeps the row and writes their name into `label`, because the court record
    outlives the wiki row (see `delete_member`).

    `charges` is a list of `{count, statute, offense, disposition}`, statutes as
    the court cites them (MCL 750.316, 18 U.S.C. 1962(d)). The sentence is held
    here because `member_incarceration` has no column for a term; a spell is
    the time served, linked back through `member_incarceration.court_case_id`.
    """

    __tablename__ = "court_case_defendant"
    __table_args__ = (
        CheckConstraint(
            "member_id IS NOT NULL OR label IS NOT NULL",
            name="ck_court_case_defendant_member_or_label",
        ),
        sa.Index(
            "uq_court_case_defendant_case_member",
            "court_case_id",
            "member_id",
            unique=True,
            postgresql_where=sa.text("member_id IS NOT NULL"),
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    court_case_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid(),
            sa.ForeignKey("court_case.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    member_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            sa.Uuid(), sa.ForeignKey("member.id", ondelete="SET NULL"), nullable=True, index=True
        ),
    )
    label: str | None = None
    defendant_number: str | None = None
    disposition: str = Field(sa_column=Column(String, nullable=False, server_default="PENDING"))
    charges: list = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default="[]"),
    )
    sentence_months: int | None = None
    life_sentence: bool = Field(
        default=False, sa_column=Column(sa.Boolean, nullable=False, server_default="false")
    )
    supervised_release_months: int | None = None
    sentenced_at: dict | None = Field(default=None, sa_column=Column(JSONB(none_as_null=True)))
    # Pleaded and testified for the government, or a repenti: the reason a
    # sentence is short, and often the reason the case exists at all.
    cooperated: bool = Field(
        default=False, sa_column=Column(sa.Boolean, nullable=False, server_default="false")
    )
    notes: str | None = None
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )


class CourtCaseIncident(SQLModel, table=True):
    """An incident a case covers. Many to many: a racketeering case covers a
    dozen incidents, and one killing can produce a state and a federal case."""

    __tablename__ = "court_case_incident"

    court_case_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid(), sa.ForeignKey("court_case.id", ondelete="CASCADE"), primary_key=True
        )
    )
    incident_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid(),
            sa.ForeignKey("incident.id", ondelete="CASCADE"),
            primary_key=True,
            index=True,
        )
    )


class CourtCaseSet(SQLModel, table=True):
    """A set the case is about: the enterprise an indictment names, or the sets
    whose members it charges as one crew."""

    __tablename__ = "court_case_set"

    court_case_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid(), sa.ForeignKey("court_case.id", ondelete="CASCADE"), primary_key=True
        )
    )
    set_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid(), sa.ForeignKey("sets.id", ondelete="CASCADE"), primary_key=True, index=True
        )
    )
