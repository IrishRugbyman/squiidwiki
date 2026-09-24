"""member_custody_id table

One row per number a custody system issued to a member (MDOC, BOP, GDC, a
Georgia OTN, a jail booking number...), so a member can hold any mix of systems
and more than one number in a system that issues them per arrest. Backfilled
from member.mdoc_number and member.bop_register_number, which stay for now as
the write path for those two systems and are mirrored into this table by
app.crud.member.

Hand-trimmed: autogenerate also proposed dropping the trigram indexes, the
partial unique indexes on member_set and set_relationships, two unique
constraints on gang and every ON DELETE CASCADE / SET NULL foreign key, none of
which any model declares. None of that is this change.

Revision ID: dca974125ded
Revises: bd78476464dd
Create Date: 2026-09-23 10:41:39.843216

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "dca974125ded"
down_revision: str | None = "bd78476464dd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Must match app.models.member.CUSTODY_MIRROR_NOTE: the mirror only ever deletes
# rows carrying it. Kept literal so this migration never imports app code.
MIRROR_NOTE = "mirrored from the member's legacy column"


def upgrade() -> None:
    op.create_table(
        "member_custody_id",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("universe_id", sa.Uuid(), nullable=False),
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.Column("system", sa.String(), nullable=False),
        sa.Column("number", sa.String(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=True),
        sa.Column("photo_media_id", sa.UUID(), nullable=True),
        sa.Column("retrieved_at", sa.Date(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["member_id"], ["member.id"]),
        sa.ForeignKeyConstraint(["photo_media_id"], ["media.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_id"], ["source.id"]),
        sa.ForeignKeyConstraint(["universe_id"], ["universe.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_member_custody_id_member_id", "member_custody_id", ["member_id"])
    op.create_index("ix_member_custody_id_number", "member_custody_id", ["number"])
    op.create_index("ix_member_custody_id_universe_id", "member_custody_id", ["universe_id"])
    op.create_index(
        "uq_member_custody_id_member_system_number",
        "member_custody_id",
        ["member_id", "system", "number"],
        unique=True,
    )
    op.create_index(
        "uq_member_custody_id_universe_system_number",
        "member_custody_id",
        ["universe_id", "system", "number"],
        unique=True,
        postgresql_where=sa.text("system <> 'MDOC'"),
    )

    # Backfill. One statement per execute(): asyncpg rejects multi-statement SQL.
    for system, column in (("MDOC", "mdoc_number"), ("BOP", "bop_register_number")):
        op.execute(
            sa.text(
                f"""
                INSERT INTO member_custody_id
                    (id, universe_id, member_id, system, number, notes, created_at)
                SELECT gen_random_uuid(), universe_id, id, '{system}', btrim({column}),
                       :note, now()
                FROM member
                WHERE {column} IS NOT NULL AND btrim({column}) <> ''
                """
            ).bindparams(note=MIRROR_NOTE)
        )


def downgrade() -> None:
    # The legacy columns still hold every MDOC and BOP number, so dropping the
    # table loses only numbers recorded here by hand (GDC, OTNs, jail numbers).
    op.drop_index("uq_member_custody_id_universe_system_number", table_name="member_custody_id")
    op.drop_index("uq_member_custody_id_member_system_number", table_name="member_custody_id")
    op.drop_index("ix_member_custody_id_universe_id", table_name="member_custody_id")
    op.drop_index("ix_member_custody_id_number", table_name="member_custody_id")
    op.drop_index("ix_member_custody_id_member_id", table_name="member_custody_id")
    op.drop_table("member_custody_id")
