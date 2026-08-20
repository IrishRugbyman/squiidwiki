"""add business (people/sets/sources) tracking

New entity: legitimate or front businesses (gaming, construction, ports,
waste management, ...) with M2M links to the members who own or front them,
the sets that protect them, and the sources documenting them. Economic
capture is a first-class part of some milieus (Corsican organised crime
especially) in a way territory alone does not represent.

Revision ID: 58e15d368e68
Revises: a05bd5a97bb8
Create Date: 2026-08-20
"""

import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "58e15d368e68"
down_revision = "a05bd5a97bb8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "business",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("universe_id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("aliases", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "business_type",
            sa.Enum(
                "GAMING",
                "NIGHTLIFE",
                "CONSTRUCTION",
                "PORT",
                "WASTE_MANAGEMENT",
                "HOSPITALITY",
                "RETAIL",
                "SECURITY",
                "OTHER",
                name="businesstype",
            ),
            nullable=False,
        ),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "CLOSED", "SEIZED", name="businessstatus"),
            nullable=False,
        ),
        sa.Column("municipality_id", sa.Uuid(), nullable=True),
        sa.Column(
            "founded_at", postgresql.JSONB(none_as_null=True, astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "ended_at", postgresql.JSONB(none_as_null=True, astext_type=sa.Text()), nullable=True
        ),
        sa.Column("slug", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["municipality_id"], ["municipality.id"]),
        sa.ForeignKeyConstraint(["universe_id"], ["universe.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_business_municipality_id", "business", ["municipality_id"])
    op.create_index("ix_business_name", "business", ["name"])
    op.create_index("ix_business_slug", "business", ["slug"])
    op.create_index("ix_business_universe_id", "business", ["universe_id"])

    op.create_table(
        "business_member",
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.Column(
            "role", sa.Enum("OWNER", "FRONT", "BENEFICIARY", name="businessrole"), nullable=False
        ),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["member_id"], ["member.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("business_id", "member_id"),
    )
    op.create_table(
        "business_set",
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("set_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["set_id"], ["sets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("business_id", "set_id"),
    )
    op.create_table(
        "business_source",
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["source.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("business_id", "source_id"),
    )


def downgrade() -> None:
    op.drop_table("business_source")
    op.drop_table("business_set")
    op.drop_table("business_member")
    op.drop_index("ix_business_universe_id", table_name="business")
    op.drop_index("ix_business_slug", table_name="business")
    op.drop_index("ix_business_name", table_name="business")
    op.drop_index("ix_business_municipality_id", table_name="business")
    op.drop_table("business")
    op.execute("DROP TYPE IF EXISTS businessrole")
    op.execute("DROP TYPE IF EXISTS businessstatus")
    op.execute("DROP TYPE IF EXISTS businesstype")
