"""Research notes gain a kind and can be pinned to entities.

Revision ID: 3eefd9de875d
Revises: d38f10167a03
Create Date: 2026-10-12

research_note.kind is VARCHAR(16) with a CHECK (not a Postgres ENUM, like
media.kind), NOT NULL, server default INBOX so existing notes land in the inbox.
research_note_pin links a note to exactly one member, set, incident or alliance;
every FK cascades, so deleting the entity removes the pin and keeps the note.
"""

import sqlalchemy as sa

from alembic import op

revision = "3eefd9de875d"
down_revision = "d38f10167a03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "research_note",
        sa.Column("kind", sa.String(length=16), server_default="INBOX", nullable=False),
    )
    op.create_index(op.f("ix_research_note_kind"), "research_note", ["kind"], unique=False)
    op.create_check_constraint(
        "ck_research_note_kind",
        "research_note",
        "kind IN ('INBOX', 'FOR_YOU', 'PARKED', 'REFERENCE')",
    )

    op.create_table(
        "research_note_pin",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("note_id", sa.Uuid(), nullable=False),
        sa.Column("member_id", sa.Uuid(), nullable=True),
        sa.Column("set_id", sa.Uuid(), nullable=True),
        sa.Column("incident_id", sa.Uuid(), nullable=True),
        sa.Column("alliance_id", sa.Uuid(), nullable=True),
        sa.CheckConstraint(
            "num_nonnulls(member_id, set_id, incident_id, alliance_id) = 1",
            name="ck_research_note_pin_one_target",
        ),
        sa.ForeignKeyConstraint(["note_id"], ["research_note.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["member_id"], ["member.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["set_id"], ["sets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["incident_id"], ["incident.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["alliance_id"], ["alliance.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("note_id", "member_id", name="uq_research_note_pin_member"),
        sa.UniqueConstraint("note_id", "set_id", name="uq_research_note_pin_set"),
        sa.UniqueConstraint("note_id", "incident_id", name="uq_research_note_pin_incident"),
        sa.UniqueConstraint("note_id", "alliance_id", name="uq_research_note_pin_alliance"),
    )
    for col in ("note_id", "member_id", "set_id", "incident_id", "alliance_id"):
        op.create_index(
            op.f(f"ix_research_note_pin_{col}"), "research_note_pin", [col], unique=False
        )


def downgrade() -> None:
    op.drop_table("research_note_pin")
    op.drop_constraint("ck_research_note_kind", "research_note", type_="check")
    op.drop_index(op.f("ix_research_note_kind"), table_name="research_note")
    op.drop_column("research_note", "kind")
