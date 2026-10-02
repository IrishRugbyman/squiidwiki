"""gang_card: one shared reference card per gang, across universes

`gang_card` holds what a gang is - colours, nation, origin, founding, symbols,
national history, its own parent card - once, for every universe. Each
universe's `gang` row gains `card_id` and keeps only its local side.

Backfill:

1. One card per Michigan gang, the only universe whose gangs carry researched
   reference data (2026-09-28), with the same slug and reference fields. The
   description is left empty here and filled by the data step that splits each
   Michigan description into its national and Detroit parts.
2. Michigan gangs linked to their cards; card parents copied from gang parents.
3. Every other universe's gang whose name matches a card (case-insensitive) is
   linked, and the card's reference fields are copied onto it wherever the gang
   has none of its own - the mirror the application keeps from then on.
4. Those gangs take the local parent their card's parent implies.
5. Any gang still unlinked gets a card of its own, so every gang has one.

Revision ID: ce9354d43875
Revises: 6f9e732dcae6
Create Date: 2026-09-28
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "ce9354d43875"
down_revision = "6f9e732dcae6"
branch_labels = None
depends_on = None

MICHIGAN = "4f57cae1-ebfe-408c-b435-052e2bd0ca45"


def upgrade() -> None:
    op.create_table(
        "gang_card",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("aliases", postgresql.JSONB(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("color", sa.String(16), nullable=True),
        sa.Column("color_secondary", sa.String(16), nullable=True),
        sa.Column("nation", sa.String(16), nullable=True),
        sa.Column("origin", sa.String(), nullable=True),
        sa.Column("founded_at", postgresql.JSONB(), nullable=True),
        sa.Column("symbols", postgresql.JSONB(), nullable=True),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["gang_card.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "nation IS NULL OR nation IN ('FOLK', 'PEOPLE')", name="ck_gang_card_nation"
        ),
        sa.CheckConstraint(
            "parent_id IS NULL OR parent_id <> id", name="ck_gang_card_parent_not_self"
        ),
    )
    op.create_index("ix_gang_card_slug", "gang_card", ["slug"], unique=True)
    op.create_index("ix_gang_card_parent_id", "gang_card", ["parent_id"])
    op.add_column("gang", sa.Column("card_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "gang_card_id_fkey", "gang", "gang_card", ["card_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index("ix_gang_card_id", "gang", ["card_id"])

    # 1. Cards from Michigan. Reusing the gang's id as the card's id makes
    # step 2 a plain equality, and nothing else keys on card ids yet.
    op.execute(
        f"""
        INSERT INTO gang_card (id, slug, name, aliases, color, color_secondary, nation,
                               origin, founded_at, symbols, created_at, updated_at)
        SELECT id, slug, name, aliases, color, color_secondary, nation,
               origin, founded_at, symbols, now(), now()
        FROM gang WHERE universe_id = '{MICHIGAN}' AND slug IS NOT NULL
        """
    )
    # 2. Link Michigan, and carry its hierarchy onto the cards.
    op.execute(
        f"UPDATE gang SET card_id = id WHERE universe_id = '{MICHIGAN}' AND slug IS NOT NULL"
    )
    op.execute(
        f"""
        UPDATE gang_card c SET parent_id = g.parent_id
        FROM gang g
        WHERE g.id = c.id AND g.universe_id = '{MICHIGAN}' AND g.parent_id IS NOT NULL
        """
    )
    # 3. Other universes, by name.
    op.execute(
        f"""
        UPDATE gang g SET card_id = c.id
        FROM gang_card c
        WHERE g.universe_id <> '{MICHIGAN}' AND g.card_id IS NULL
          AND lower(g.name) = lower(c.name)
        """
    )
    op.execute(
        f"""
        UPDATE gang g SET
            color = coalesce(g.color, c.color),
            color_secondary = coalesce(g.color_secondary, c.color_secondary),
            nation = coalesce(g.nation, c.nation),
            origin = coalesce(g.origin, c.origin),
            founded_at = coalesce(g.founded_at, c.founded_at),
            symbols = coalesce(g.symbols, c.symbols)
        FROM gang_card c
        WHERE g.card_id = c.id AND g.universe_id <> '{MICHIGAN}'
        """
    )

    # 4. Their hierarchy: a linked gang sits under the local gang that holds
    # its card's parent card, where that universe has one.
    op.execute(
        f"""
        UPDATE gang g SET parent_id = p.id
        FROM gang_card c, gang p
        WHERE g.card_id = c.id AND c.parent_id IS NOT NULL
          AND p.card_id = c.parent_id AND p.universe_id = g.universe_id
          AND g.parent_id IS NULL AND g.universe_id <> '{MICHIGAN}'
        """
    )

    # 5. Every gang still without a card gets one of its own (Corsica's clans,
    # the Chicago-only nations), so there is one model and not two. A slug that
    # a card already holds, or that two of these gangs share, takes the first
    # characters of the gang's id to stay unique.
    op.execute(
        """
        INSERT INTO gang_card (id, slug, name, aliases, color, color_secondary, nation,
                               origin, founded_at, symbols, created_at, updated_at)
        SELECT id,
               CASE WHEN taken OR rn > 1 THEN slug || '-' || substr(id::text, 1, 8)
                    ELSE slug END,
               name, aliases, color, color_secondary, nation,
               origin, founded_at, symbols, now(), now()
        FROM (
            SELECT g.*,
                   EXISTS (SELECT 1 FROM gang_card c WHERE c.slug = g.slug) AS taken,
                   row_number() OVER (PARTITION BY g.slug ORDER BY g.created_at, g.id) AS rn
            FROM gang g
            WHERE g.card_id IS NULL AND g.slug IS NOT NULL
        ) x
        """
    )
    op.execute("UPDATE gang SET card_id = id WHERE card_id IS NULL AND slug IS NOT NULL")
    op.execute(
        """
        UPDATE gang_card c SET parent_id = p.card_id
        FROM gang g JOIN gang p ON p.id = g.parent_id
        WHERE g.id = c.id AND c.parent_id IS NULL AND p.card_id IS NOT NULL
        """
    )


def downgrade() -> None:
    # The mirrored reference values stay on the gang rows, so nothing a page
    # shows is lost; only the link and the shared national descriptions go.
    op.drop_index("ix_gang_card_id", table_name="gang")
    op.drop_constraint("gang_card_id_fkey", "gang", type_="foreignkey")
    op.drop_column("gang", "card_id")
    op.drop_index("ix_gang_card_parent_id", table_name="gang_card")
    op.drop_index("ix_gang_card_slug", table_name="gang_card")
    op.drop_table("gang_card")
