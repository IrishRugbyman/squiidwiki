"""people in a photo

Revision ID: 53921e33fe68
Revises: 818bf834b8a3
Create Date: 2026-10-13

A photo still belongs to exactly one entity through `media`. `media_member` says
which members appear in it, optionally left to right (`position` null = order
unknown), and lets the photo show on those members' pages. Both ends cascade.
Nothing on `media` or its CHECK changes.
"""

import sqlalchemy as sa

from alembic import op

revision = "53921e33fe68"
down_revision = "818bf834b8a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "media_member",
        sa.Column("media_id", sa.Uuid(), nullable=False),
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["media_id"], ["media.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["member_id"], ["member.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("media_id", "member_id"),
    )
    op.create_index("ix_media_member_member_id", "media_member", ["member_id"])


def downgrade() -> None:
    op.drop_index("ix_media_member_member_id", table_name="media_member")
    op.drop_table("media_member")
