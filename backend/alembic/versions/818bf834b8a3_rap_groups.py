"""rap groups and labels

Revision ID: 818bf834b8a3
Revises: 3eefd9de875d
Create Date: 2026-10-13

A rap group (or a record label, told apart by `kind`) is not a set: no map, no
set stats, never an affiliation. Its members keep their real set; the group is
a separate link.

- `rap_group`: names in slots like sets and alliances (`name` is the derived
  display of the primary entry in `name_variants`), a status, the years active,
  a home municipality and a bio. Slug unique per universe.
- `rap_group_member`: a member's place in a group, with a role (SIGNED is an
  artist signed to a label), an optional span and a display position. Both ends
  cascade.
- `rap_group_relationship`: friend/enemy link between two groups, stored once in
  UUID order (CHECK), reusing the existing `setrelationshiptype`. Both ends
  cascade.
- `citation.rap_group_id` and `media.rap_group_id` (ON DELETE CASCADE), and the
  "exactly one target" CHECK on each widened to include them.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "818bf834b8a3"
down_revision = "3eefd9de875d"
branch_labels = None
depends_on = None

STATUS = postgresql.ENUM("ACTIVE", "DISBANDED", name="rapgroupstatus", create_type=False)
KIND = postgresql.ENUM("GROUP", "LABEL", name="rapgroupkind", create_type=False)
ROLE = postgresql.ENUM(
    "FOUNDER", "MEMBER", "SIGNED", "AFFILIATE", name="rapgrouprole", create_type=False
)

OLD_CITATION = (
    "num_nonnulls(member_id, incident_id, set_id, alliance_id, court_case_id, "
    "municipality_id, business_id) = 1"
)
NEW_CITATION = (
    "num_nonnulls(member_id, incident_id, set_id, alliance_id, rap_group_id, "
    "court_case_id, municipality_id, business_id) = 1"
)
OLD_MEDIA = (
    "num_nonnulls(member_id, incident_id, source_id, set_id, alliance_id, municipality_id) = 1"
)
NEW_MEDIA = (
    "num_nonnulls(member_id, incident_id, source_id, set_id, alliance_id, rap_group_id, "
    "municipality_id) = 1"
)


def upgrade() -> None:
    for enum in (STATUS, KIND, ROLE):
        enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "rap_group",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("universe_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("name_variants", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("kind", KIND, server_default="GROUP", nullable=False),
        sa.Column("status", STATUS, server_default="ACTIVE", nullable=False),
        sa.Column("active_from", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("active_to", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("municipality_id", sa.Uuid(), nullable=True),
        sa.Column("bio", sa.String(), nullable=True),
        sa.Column("slug", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["universe_id"], ["universe.id"]),
        sa.ForeignKeyConstraint(["municipality_id"], ["municipality.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rap_group_universe_id", "rap_group", ["universe_id"])
    op.create_index("ix_rap_group_name", "rap_group", ["name"])
    op.create_index("ix_rap_group_municipality_id", "rap_group", ["municipality_id"])
    op.create_index("ix_rap_group_slug", "rap_group", ["slug"])
    op.create_index("uq_rap_group_universe_slug", "rap_group", ["universe_id", "slug"], unique=True)
    op.execute("CREATE INDEX ix_rap_group_name_trgm ON rap_group USING gin (name gin_trgm_ops)")

    op.create_table(
        "rap_group_member",
        sa.Column("rap_group_id", sa.Uuid(), nullable=False),
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.Column("role", ROLE, server_default="MEMBER", nullable=False),
        sa.Column("since", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("until", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["rap_group_id"], ["rap_group.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["member_id"], ["member.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("rap_group_id", "member_id"),
    )
    op.create_index("ix_rap_group_member_member_id", "rap_group_member", ["member_id"])

    op.create_table(
        "rap_group_relationship",
        sa.Column("rap_group_a_id", sa.Uuid(), nullable=False),
        sa.Column("rap_group_b_id", sa.Uuid(), nullable=False),
        sa.Column(
            "relationship_type",
            postgresql.ENUM("FRIEND", "ENEMY", name="setrelationshiptype", create_type=False),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["rap_group_a_id"], ["rap_group.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rap_group_b_id"], ["rap_group.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("rap_group_a_id", "rap_group_b_id"),
        sa.CheckConstraint(
            "rap_group_a_id < rap_group_b_id", name="ck_rap_group_relationship_order"
        ),
    )
    op.create_index(
        "ix_rap_group_relationship_rap_group_b_id", "rap_group_relationship", ["rap_group_b_id"]
    )

    op.add_column("citation", sa.Column("rap_group_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "citation_rap_group_id_fkey",
        "citation",
        "rap_group",
        ["rap_group_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "uq_citation_rap_group_id_source",
        "citation",
        ["rap_group_id", "source_id"],
        unique=True,
        postgresql_where=sa.text("rap_group_id IS NOT NULL"),
    )
    op.drop_constraint("ck_citation_exactly_one_target", "citation", type_="check")
    op.create_check_constraint("ck_citation_exactly_one_target", "citation", NEW_CITATION)

    op.add_column("media", sa.Column("rap_group_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "media_rap_group_id_fkey",
        "media",
        "rap_group",
        ["rap_group_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_media_rap_group_id", "media", ["rap_group_id"])
    op.drop_constraint("media_attaches_to_exactly_one_entity", "media", type_="check")
    op.create_check_constraint("media_attaches_to_exactly_one_entity", "media", NEW_MEDIA)


def downgrade() -> None:
    op.drop_constraint("media_attaches_to_exactly_one_entity", "media", type_="check")
    op.execute("DELETE FROM media WHERE rap_group_id IS NOT NULL")
    op.create_check_constraint("media_attaches_to_exactly_one_entity", "media", OLD_MEDIA)
    op.drop_index("ix_media_rap_group_id", table_name="media")
    op.drop_constraint("media_rap_group_id_fkey", "media", type_="foreignkey")
    op.drop_column("media", "rap_group_id")

    op.drop_constraint("ck_citation_exactly_one_target", "citation", type_="check")
    op.execute("DELETE FROM citation WHERE rap_group_id IS NOT NULL")
    op.create_check_constraint("ck_citation_exactly_one_target", "citation", OLD_CITATION)
    op.drop_index("uq_citation_rap_group_id_source", table_name="citation")
    op.drop_constraint("citation_rap_group_id_fkey", "citation", type_="foreignkey")
    op.drop_column("citation", "rap_group_id")

    op.drop_index("ix_rap_group_relationship_rap_group_b_id", table_name="rap_group_relationship")
    op.drop_table("rap_group_relationship")
    op.drop_index("ix_rap_group_member_member_id", table_name="rap_group_member")
    op.drop_table("rap_group_member")
    op.execute("DROP INDEX IF EXISTS ix_rap_group_name_trgm")
    op.drop_index("uq_rap_group_universe_slug", table_name="rap_group")
    op.drop_index("ix_rap_group_slug", table_name="rap_group")
    op.drop_index("ix_rap_group_municipality_id", table_name="rap_group")
    op.drop_index("ix_rap_group_name", table_name="rap_group")
    op.drop_index("ix_rap_group_universe_id", table_name="rap_group")
    op.drop_table("rap_group")
    for enum in (ROLE, KIND, STATUS):
        enum.drop(op.get_bind(), checkfirst=True)
