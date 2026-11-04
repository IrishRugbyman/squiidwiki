"""court cases: prosecutions, their defendants, and what they cover

Five new tables and one column.

- `court_case`: one prosecution or suit. Unique on (court, docket) when the
  docket is known, and on (universe_id, slug). `jurisdiction` and `kind` are
  VARCHAR holding enum values, like `member_custody_id.system`, so a new value
  is a code change and not a migration. `docket_aliases` holds every other
  spelling of the docket, so the same case written three ways resolves to one
  row. `parent_case_id` links an appeal to its trial, an indictment to the
  complaint it grew from.
- `court_case_defendant`: one row per person charged, with charges (JSONB),
  disposition, sentence and whether they cooperated. `member_id` may be empty
  for someone the wiki has no member for, who then carries a `label` (CHECK).
  The member FK is SET NULL: `delete_member` copies the name into `label`
  first, because the court record outlives the wiki row.
- `court_case_incident`, `court_case_set`, `court_case_source`: what a case
  covers, which sets it is about, and what cites it. Both ends cascade.
- `member_incarceration.court_case_id`: the case a spell was served for, SET
  NULL on delete. The free-text `case_id` beside it stays as the custody record
  gave it.

Until now all of this lived in `member_incarceration.case_id` (443 spells, 175
spellings), OTIS notes, and biography prose.

Hand-trimmed: autogenerate also proposed dropping the trigram indexes, the
partial unique indexes on member_set and set_relationships, and rewriting a
dozen foreign keys and column types that the models do not declare. None of
that is this change.

Revision ID: 437b8ac567a8
Revises: 81e18d3c4faa
Create Date: 2026-10-02
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "437b8ac567a8"
down_revision = "81e18d3c4faa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "court_case",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("universe_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=True),
        sa.Column("jurisdiction", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), server_default="CRIMINAL", nullable=False),
        sa.Column("court", sa.String(), nullable=False),
        sa.Column("docket", sa.String(), nullable=True),
        sa.Column(
            "docket_aliases", postgresql.ARRAY(sa.String()), server_default="{}", nullable=False
        ),
        sa.Column("parent_case_id", sa.Uuid(), nullable=True),
        sa.Column("filed_at", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("closed_at", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("judge", sa.String(), nullable=True),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column(
            "courtlistener_ids", postgresql.ARRAY(sa.Integer()), server_default="{}", nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["parent_case_id"], ["court_case.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["universe_id"], ["universe.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_court_case_name", "court_case", ["name"])
    op.create_index("ix_court_case_slug", "court_case", ["slug"])
    op.create_index("ix_court_case_universe_id", "court_case", ["universe_id"])
    op.create_index(
        "uq_court_case_court_docket",
        "court_case",
        ["court", "docket"],
        unique=True,
        postgresql_where=sa.text("docket IS NOT NULL"),
    )
    op.create_index(
        "uq_court_case_universe_slug", "court_case", ["universe_id", "slug"], unique=True
    )
    # Same trigram search the other named entities get (9065522d726a).
    op.execute("CREATE INDEX ix_court_case_name_trgm ON court_case USING gin (name gin_trgm_ops)")

    op.create_table(
        "court_case_defendant",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("court_case_id", sa.Uuid(), nullable=False),
        sa.Column("member_id", sa.Uuid(), nullable=True),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("defendant_number", sa.String(), nullable=True),
        sa.Column("disposition", sa.String(), server_default="PENDING", nullable=False),
        sa.Column(
            "charges", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False
        ),
        sa.Column("sentence_months", sa.Integer(), nullable=True),
        sa.Column("life_sentence", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("supervised_release_months", sa.Integer(), nullable=True),
        sa.Column("sentenced_at", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("cooperated", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "member_id IS NOT NULL OR label IS NOT NULL",
            name="ck_court_case_defendant_member_or_label",
        ),
        sa.ForeignKeyConstraint(["court_case_id"], ["court_case.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["member_id"], ["member.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_court_case_defendant_court_case_id", "court_case_defendant", ["court_case_id"]
    )
    op.create_index("ix_court_case_defendant_member_id", "court_case_defendant", ["member_id"])
    op.create_index(
        "uq_court_case_defendant_case_member",
        "court_case_defendant",
        ["court_case_id", "member_id"],
        unique=True,
        postgresql_where=sa.text("member_id IS NOT NULL"),
    )

    for table, column, target in (
        ("court_case_incident", "incident_id", "incident.id"),
        ("court_case_set", "set_id", "sets.id"),
        ("court_case_source", "source_id", "source.id"),
    ):
        op.create_table(
            table,
            sa.Column("court_case_id", sa.Uuid(), nullable=False),
            sa.Column(column, sa.Uuid(), nullable=False),
            sa.ForeignKeyConstraint(["court_case_id"], ["court_case.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint([column], [target], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("court_case_id", column),
        )
        op.create_index(f"ix_{table}_{column}", table, [column])

    op.add_column("member_incarceration", sa.Column("court_case_id", sa.Uuid(), nullable=True))
    op.create_index(
        "ix_member_incarceration_court_case_id", "member_incarceration", ["court_case_id"]
    )
    op.create_foreign_key(
        "member_incarceration_court_case_id_fkey",
        "member_incarceration",
        "court_case",
        ["court_case_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "member_incarceration_court_case_id_fkey", "member_incarceration", type_="foreignkey"
    )
    op.drop_index("ix_member_incarceration_court_case_id", table_name="member_incarceration")
    op.drop_column("member_incarceration", "court_case_id")
    for table, column in (
        ("court_case_source", "source_id"),
        ("court_case_set", "set_id"),
        ("court_case_incident", "incident_id"),
    ):
        op.drop_index(f"ix_{table}_{column}", table_name=table)
        op.drop_table(table)
    op.drop_index("uq_court_case_defendant_case_member", table_name="court_case_defendant")
    op.drop_index("ix_court_case_defendant_member_id", table_name="court_case_defendant")
    op.drop_index("ix_court_case_defendant_court_case_id", table_name="court_case_defendant")
    op.drop_table("court_case_defendant")
    op.execute("DROP INDEX ix_court_case_name_trgm")
    op.drop_index("uq_court_case_universe_slug", table_name="court_case")
    op.drop_index("uq_court_case_court_docket", table_name="court_case")
    op.drop_index("ix_court_case_universe_id", table_name="court_case")
    op.drop_index("ix_court_case_slug", table_name="court_case")
    op.drop_index("ix_court_case_name", table_name="court_case")
    op.drop_table("court_case")
