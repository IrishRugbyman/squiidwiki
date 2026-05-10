"""set_stats_extras: add last/first incident year + active_member_count

Revision ID: e6e56afe6dd2
Revises: 29e5618942bc
Create Date: 2026-05-10

"""
from typing import Sequence, Union

from alembic import op


revision: str = "e6e56afe6dd2"
down_revision: Union[str, None] = "29e5618942bc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


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
          AND i.date->>'year' ~ '^\\d+$'
    )                                                                   AS last_incident_year,
    (
        SELECT MIN((i.date->>'year')::int)
        FROM incident i
        JOIN incident_participant ip ON ip.incident_id = i.id
        JOIN member sm              ON sm.id = ip.member_id
        WHERE sm.set_id = s.id
          AND i.date IS NOT NULL
          AND i.date->>'year' ~ '^\\d+$'
    )                                                                   AS first_incident_year
FROM sets s
LEFT JOIN member m       ON m.set_id = s.id
LEFT JOIN member_stats ms ON ms.member_id = m.id
GROUP BY s.id, s.universe_id
"""

SET_STATS_V1 = """
CREATE MATERIALIZED VIEW set_stats AS
SELECT
    s.id                                            AS set_id,
    s.universe_id,
    COUNT(DISTINCT m.id)                            AS member_count,
    COUNT(CASE WHEN m.status = 'DEAD' THEN 1 END)  AS dead_members,
    COALESCE(SUM(ms.shootings), 0)                  AS total_shootings,
    COALESCE(SUM(ms.assists), 0)                    AS total_assists,
    COALESCE(SUM(ms.kills), 0)                      AS total_kills
FROM sets s
LEFT JOIN member m ON m.set_id = s.id
LEFT JOIN member_stats ms ON ms.member_id = m.id
GROUP BY s.id, s.universe_id
"""


def upgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS set_stats")
    op.execute(SET_STATS_V2)
    op.execute("CREATE UNIQUE INDEX ON set_stats (set_id)")


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS set_stats")
    op.execute(SET_STATS_V1)
    op.execute("CREATE UNIQUE INDEX ON set_stats (set_id)")
