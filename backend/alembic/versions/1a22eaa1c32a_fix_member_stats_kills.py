"""fix member_stats.kills: count shooters in incidents with a killed victim

Previously `kills` counted SHOOTER rows whose own outcome=KILLED — i.e. shooters
who were themselves killed (nonsensical). A kill is when the member is a
SHOOTER in an incident that has a VICTIM with outcome=KILLED. set_stats sums
member_stats.kills, so it inherited the bug.

Revision ID: 1a22eaa1c32a
Revises: e6e56afe6dd2
Create Date: 2026-05-10

"""
from typing import Sequence, Union

from alembic import op


revision: str = "1a22eaa1c32a"
down_revision: Union[str, None] = "e6e56afe6dd2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


MEMBER_STATS_V2 = """
CREATE MATERIALIZED VIEW member_stats AS
SELECT
    m.id                                                                    AS member_id,
    m.universe_id,
    COUNT(CASE WHEN ip.role = 'SHOOTER'                              THEN 1 END) AS shootings,
    COUNT(CASE WHEN ip.role = 'ASSISTED'                             THEN 1 END) AS assists,
    COUNT(*) FILTER (
        WHERE ip.role = 'SHOOTER'
          AND EXISTS (
              SELECT 1 FROM incident_participant ip2
              WHERE ip2.incident_id = ip.incident_id
                AND ip2.role = 'VICTIM'
                AND ip2.outcome = 'KILLED'
          )
    )                                                                       AS kills,
    COUNT(CASE WHEN ip.role = 'VICTIM'   AND ip.outcome != 'KILLED'  THEN 1 END) AS times_shot_survived
FROM member m
LEFT JOIN incident_participant ip ON ip.member_id = m.id
GROUP BY m.id, m.universe_id
"""

MEMBER_STATS_V1 = """
CREATE MATERIALIZED VIEW member_stats AS
SELECT
    m.id                                                                    AS member_id,
    m.universe_id,
    COUNT(CASE WHEN ip.role = 'SHOOTER'                              THEN 1 END) AS shootings,
    COUNT(CASE WHEN ip.role = 'ASSISTED'                             THEN 1 END) AS assists,
    COUNT(CASE WHEN ip.role = 'SHOOTER'  AND ip.outcome = 'KILLED'   THEN 1 END) AS kills,
    COUNT(CASE WHEN ip.role = 'VICTIM'   AND ip.outcome != 'KILLED'  THEN 1 END) AS times_shot_survived
FROM member m
LEFT JOIN incident_participant ip ON ip.member_id = m.id
GROUP BY m.id, m.universe_id
"""

SET_STATS = """
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


def upgrade() -> None:
    # set_stats depends on member_stats — drop it first
    op.execute("DROP MATERIALIZED VIEW IF EXISTS set_stats")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS member_stats")
    op.execute(MEMBER_STATS_V2)
    op.execute("CREATE UNIQUE INDEX ON member_stats (member_id)")
    op.execute(SET_STATS)
    op.execute("CREATE UNIQUE INDEX ON set_stats (set_id)")


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS set_stats")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS member_stats")
    op.execute(MEMBER_STATS_V1)
    op.execute("CREATE UNIQUE INDEX ON member_stats (member_id)")
    op.execute(SET_STATS)
    op.execute("CREATE UNIQUE INDEX ON set_stats (set_id)")
