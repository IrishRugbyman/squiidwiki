"""member_set many-to-many: members can belong to multiple sets

Revision ID: 02b201cab602
Revises: 1a22eaa1c32a
Create Date: 2026-05-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "02b201cab602"
down_revision: Union[str, None] = "d99c4fb11310"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SET_STATS_V3 = """
CREATE MATERIALIZED VIEW set_stats AS
SELECT
    s.id                                                                AS set_id,
    s.universe_id,
    COUNT(DISTINCT m.id)                                                AS member_count,
    COUNT(DISTINCT m.id) FILTER (
        WHERE m.status IN ('FREE','LOCKED','ESCAPEE','ABSCONDER')
    )                                                                   AS active_member_count,
    COUNT(DISTINCT m.id) FILTER (WHERE m.status = 'DEAD')               AS dead_members,
    COALESCE(SUM(ms2.shootings), 0)                                     AS total_shootings,
    COALESCE(SUM(ms2.assists), 0)                                       AS total_assists,
    COALESCE(SUM(ms2.kills), 0)                                         AS total_kills,
    (
        SELECT MAX((i.date->>'year')::int)
        FROM incident i
        JOIN incident_participant ip ON ip.incident_id = i.id
        WHERE EXISTS (
            SELECT 1 FROM member_set ms3
            WHERE ms3.member_id = ip.member_id AND ms3.set_id = s.id
        )
          AND i.date IS NOT NULL
          AND i.date->>'year' ~ E'^\\d+$'
    )                                                                   AS last_incident_year,
    (
        SELECT MIN((i.date->>'year')::int)
        FROM incident i
        JOIN incident_participant ip ON ip.incident_id = i.id
        WHERE EXISTS (
            SELECT 1 FROM member_set ms3
            WHERE ms3.member_id = ip.member_id AND ms3.set_id = s.id
        )
          AND i.date IS NOT NULL
          AND i.date->>'year' ~ E'^\\d+$'
    )                                                                   AS first_incident_year
FROM sets s
LEFT JOIN member_set ms  ON ms.set_id = s.id
LEFT JOIN member m        ON m.id = ms.member_id
LEFT JOIN member_stats ms2 ON ms2.member_id = m.id
GROUP BY s.id, s.universe_id
"""

# Original set_stats that joined member.set_id directly
SET_STATS_V2 = """
CREATE MATERIALIZED VIEW set_stats AS
SELECT
    s.id                                                                AS set_id,
    s.universe_id,
    COUNT(DISTINCT m.id)                                                AS member_count,
    COUNT(DISTINCT m.id) FILTER (
        WHERE m.status IN ('FREE','LOCKED','ESCAPEE','ABSCONDER')
    )                                                                   AS active_member_count,
    COUNT(DISTINCT m.id) FILTER (WHERE m.status = 'DEAD')               AS dead_members,
    COALESCE(SUM(ms.shootings), 0)                                      AS total_shootings,
    COALESCE(SUM(ms.assists), 0)                                        AS total_assists,
    COALESCE(SUM(ms.kills), 0)                                          AS total_kills,
    (
        SELECT MAX((i.date->>'year')::int)
        FROM incident i
        JOIN incident_participant ip ON ip.incident_id = i.id
        JOIN member sm              ON sm.id = ip.member_id
        WHERE sm.set_id = s.id
          AND i.date IS NOT NULL
          AND i.date->>'year' ~ E'^\\d+$'
    )                                                                   AS last_incident_year,
    (
        SELECT MIN((i.date->>'year')::int)
        FROM incident i
        JOIN incident_participant ip ON ip.incident_id = i.id
        JOIN member sm              ON sm.id = ip.member_id
        WHERE sm.set_id = s.id
          AND i.date IS NOT NULL
          AND i.date->>'year' ~ E'^\\d+$'
    )                                                                   AS first_incident_year
FROM sets s
LEFT JOIN member m       ON m.set_id = s.id
LEFT JOIN member_stats ms ON ms.member_id = m.id
GROUP BY s.id, s.universe_id
"""


def upgrade() -> None:
    # 1. Create member_set join table
    op.create_table(
        "member_set",
        sa.Column("member_id", sa.Uuid(), sa.ForeignKey("member.id", ondelete="CASCADE"), primary_key=True, nullable=False),
        sa.Column("set_id", sa.Uuid(), sa.ForeignKey("sets.id", ondelete="CASCADE"), primary_key=True, nullable=False),
        sa.Column("rank", sa.String(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index("ix_member_set_set_id", "member_set", ["set_id"])
    # Partial unique index: at most one primary affiliation per member
    op.execute(
        "CREATE UNIQUE INDEX ux_member_set_one_primary ON member_set (member_id) WHERE is_primary"
    )

    # 2. Backfill from existing member.set_id / member.set_rank
    op.execute(
        """
        INSERT INTO member_set (member_id, set_id, rank, is_primary)
        SELECT id, set_id, set_rank, true
        FROM member
        WHERE set_id IS NOT NULL
        """
    )

    # 3. Drop set_stats (depends on member.set_id) before altering member
    op.execute("DROP MATERIALIZED VIEW IF EXISTS set_stats")

    # 4. Drop the old index + columns on member
    op.execute("DROP INDEX IF EXISTS ix_member_set_id")
    op.drop_column("member", "set_id")
    op.drop_column("member", "set_rank")

    # 5. Re-create set_stats using member_set join
    op.execute(SET_STATS_V3)
    op.execute("CREATE UNIQUE INDEX ON set_stats (set_id)")


def downgrade() -> None:
    # Re-add columns to member
    op.add_column("member", sa.Column("set_id", sa.Uuid(), nullable=True))
    op.add_column("member", sa.Column("set_rank", sa.String(), nullable=True))
    op.create_index("ix_member_set_id", "member", ["set_id"])

    # Backfill scalar from primary affiliation
    op.execute(
        """
        UPDATE member m
        SET set_id   = ms.set_id,
            set_rank = ms.rank
        FROM member_set ms
        WHERE ms.member_id = m.id
          AND ms.is_primary = true
        """
    )

    # Drop set_stats that uses member_set
    op.execute("DROP MATERIALIZED VIEW IF EXISTS set_stats")

    # Drop member_set
    op.execute("DROP INDEX IF EXISTS ux_member_set_one_primary")
    op.execute("DROP INDEX IF EXISTS ix_member_set_set_id")
    op.drop_table("member_set")

    # Re-create original set_stats
    op.execute(SET_STATS_V2)
    op.execute("CREATE UNIQUE INDEX ON set_stats (set_id)")
