"""pg_trgm_indexes_and_materialized_views

Revision ID: 9065522d726a
Revises: 1923e5b8ee72
Create Date: 2026-04-19 11:46:50.143085

"""
from typing import Sequence, Union

from alembic import op

revision: str = '9065522d726a'
down_revision: Union[str, None] = '1923e5b8ee72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Trigram GIN indexes for fuzzy search
    op.execute("CREATE INDEX ix_member_nickname_trgm ON member USING gin (nickname gin_trgm_ops)")
    op.execute("CREATE INDEX ix_member_legal_name_trgm ON member USING gin (legal_name gin_trgm_ops)")
    op.execute("CREATE INDEX ix_sets_name_trgm ON sets USING gin (name gin_trgm_ops)")
    op.execute("CREATE INDEX ix_alliance_name_trgm ON alliance USING gin (name gin_trgm_ops)")
    op.execute("CREATE INDEX ix_source_title_trgm ON source USING gin (title gin_trgm_ops)")

    # member_stats materialized view
    op.execute("""
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
    """)
    op.execute("CREATE UNIQUE INDEX ON member_stats (member_id)")

    # set_stats materialized view (depends on member_stats)
    op.execute("""
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
    """)
    op.execute("CREATE UNIQUE INDEX ON set_stats (set_id)")


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS set_stats")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS member_stats")

    op.execute("DROP INDEX IF EXISTS ix_source_title_trgm")
    op.execute("DROP INDEX IF EXISTS ix_alliance_name_trgm")
    op.execute("DROP INDEX IF EXISTS ix_sets_name_trgm")
    op.execute("DROP INDEX IF EXISTS ix_member_legal_name_trgm")
    op.execute("DROP INDEX IF EXISTS ix_member_nickname_trgm")
