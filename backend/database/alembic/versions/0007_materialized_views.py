"""materialized views: member_stats and set_stats for Redis-cached aggregates

Revision ID: 0007_materialized_views
Revises: 0006_sources_auditlog
Create Date: 2026-04-19

These views are Postgres-only. They require a unique index for CONCURRENTLY refresh.
"""
from alembic import op

revision = "0007_materialized_views"
down_revision = "0006_sources_auditlog"
branch_labels = None
depends_on = None

_MEMBER_STATS_SQL = """
CREATE MATERIALIZED VIEW member_stats AS
SELECT
    m.id                AS member_id,
    m.universe_id,
    m.name,
    m.status,
    m.set_id,
    COUNT(DISTINCT ip.incident_id)
        FILTER (WHERE ip.role = 'shooter')                  AS shots_fired,
    COUNT(DISTINCT ip.incident_id)
        FILTER (WHERE ip.role = 'victim')                   AS times_targeted,
    COUNT(DISTINCT ip.incident_id)
        FILTER (WHERE ip.outcome = 'killed')                AS kills,
    COUNT(DISTINCT ip.incident_id)                          AS total_incidents
FROM members m
LEFT JOIN incident_participants ip ON ip.member_id = m.id
LEFT JOIN incidents i ON i.id = ip.incident_id AND i.deleted_at IS NULL
WHERE m.deleted_at IS NULL
GROUP BY m.id, m.universe_id, m.name, m.status, m.set_id
WITH DATA
"""

_SET_STATS_SQL = """
CREATE MATERIALIZED VIEW set_stats AS
SELECT
    s.id                AS set_id,
    s.universe_id,
    s.name,
    s.type,
    COUNT(DISTINCT m.id)                                    AS member_count,
    COUNT(DISTINCT ip.incident_id)
        FILTER (WHERE i.incident_type = 'shooting')         AS shooting_count,
    COUNT(DISTINCT ip.incident_id)
        FILTER (WHERE i.incident_type = 'murder')           AS murder_count,
    COUNT(DISTINCT ip.incident_id)                          AS total_incidents
FROM sets s
LEFT JOIN members m ON m.set_id = s.id AND m.deleted_at IS NULL
LEFT JOIN incident_participants ip ON ip.member_id = m.id
LEFT JOIN incidents i ON i.id = ip.incident_id AND i.deleted_at IS NULL
WHERE s.deleted_at IS NULL
GROUP BY s.id, s.universe_id, s.name, s.type
WITH DATA
"""


def upgrade() -> None:
    op.execute(_MEMBER_STATS_SQL)
    op.execute("CREATE UNIQUE INDEX uq_member_stats_member_id ON member_stats (member_id)")

    op.execute(_SET_STATS_SQL)
    op.execute("CREATE UNIQUE INDEX uq_set_stats_set_id ON set_stats (set_id)")


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS set_stats")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS member_stats")
