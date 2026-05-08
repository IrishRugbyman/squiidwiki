"""add gang table and gang_id on sets/alliance/member

Revision ID: 33ac22d53ce8
Revises: 9a3dc580f64a
Create Date: 2026-05-08
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "33ac22d53ce8"
down_revision: Union[str, None] = "9a3dc580f64a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SEED_GANGS = [
    "Black Disciples",
    "Gangster Disciples",
    "Latin Kings",
    "Mickey Cobras",
    "Black P. Stones",
]


def _slugify(s: str) -> str:
    import re
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-") or "gang"


def upgrade() -> None:
    op.create_table(
        "gang",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("universe_id", sa.Uuid(), sa.ForeignKey("universe.id"), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False, index=True),
        sa.Column("aliases", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("slug", sa.String(), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.UniqueConstraint("universe_id", "name", name="uq_gang_universe_name"),
        sa.UniqueConstraint("universe_id", "slug", name="uq_gang_universe_slug"),
    )

    op.add_column("sets", sa.Column("gang_id", sa.Uuid(), sa.ForeignKey("gang.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_sets_gang_id", "sets", ["gang_id"])

    op.add_column("alliance", sa.Column("gang_id", sa.Uuid(), sa.ForeignKey("gang.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_alliance_gang_id", "alliance", ["gang_id"])

    op.add_column("member", sa.Column("gang_id", sa.Uuid(), sa.ForeignKey("gang.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_member_gang_id", "member", ["gang_id"])

    # Seed: insert the well-known Chicago nations into every existing universe.
    bind = op.get_bind()
    universes = bind.execute(sa.text("SELECT id FROM universe")).fetchall()
    for (universe_id,) in universes:
        for name in SEED_GANGS:
            bind.execute(
                sa.text(
                    "INSERT INTO gang (id, universe_id, name, slug, created_at, updated_at) "
                    "VALUES (:id, :uid, :name, :slug, now(), now())"
                ),
                {
                    "id": uuid.uuid4(),
                    "uid": universe_id,
                    "name": name,
                    "slug": _slugify(name),
                },
            )


def downgrade() -> None:
    op.drop_index("ix_member_gang_id", table_name="member")
    op.drop_column("member", "gang_id")

    op.drop_index("ix_alliance_gang_id", table_name="alliance")
    op.drop_column("alliance", "gang_id")

    op.drop_index("ix_sets_gang_id", table_name="sets")
    op.drop_column("sets", "gang_id")

    op.drop_table("gang")
