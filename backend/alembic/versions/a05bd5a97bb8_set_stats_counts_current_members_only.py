"""set_stats must count current members only

member_set now holds one row per spell, so a member who left a set still has a
row for it. The member_count / active_member_count / dead_members aggregates
joined member_set unfiltered and would count those departures as if they were
still in the set.

The two EXISTS subqueries are deliberately left unfiltered: they ask whether a
participant was *ever* in the set, which is the right question for the set's
first and last incident year. An incident does not leave a set's history
because the member later walked away from it.

Revision ID: a05bd5a97bb8
Revises: 57f8aaa46bdd
Create Date: 2026-08-20
"""

from alembic import op

revision = "a05bd5a97bb8"
down_revision = "57f8aaa46bdd"
branch_labels = None
depends_on = None

# Verbatim from pg_matviews except for the ms join, which gains the
# `until_date IS NULL` predicate marked below.
_SET_STATS = """
CREATE MATERIALIZED VIEW set_stats AS
 SELECT s.id AS set_id,
    s.universe_id,
    count(DISTINCT m.id) AS member_count,
    count(DISTINCT m.id) FILTER (WHERE (m.status = ANY (ARRAY['FREE'::memberstatus,
        'LOCKED'::memberstatus, 'ESCAPEE'::memberstatus,
        'ABSCONDER'::memberstatus]))) AS active_member_count,
    count(DISTINCT m.id) FILTER (WHERE (m.status = 'DEAD'::memberstatus)) AS dead_members,
    COALESCE(sum(ms2.shootings), (0)::numeric) AS total_shootings,
    COALESCE(sum(ms2.assists), (0)::numeric) AS total_assists,
    COALESCE(sum(ms2.kills), (0)::numeric) AS total_kills,
    ( SELECT max(((i.date ->> 'year'::text))::integer) AS max
           FROM (incident i
             JOIN incident_participant ip ON ((ip.incident_id = i.id)))
          WHERE ((EXISTS ( SELECT 1
                   FROM member_set ms3
                  WHERE ((ms3.member_id = ip.member_id) AND (ms3.set_id = s.id))))
                 AND (i.date IS NOT NULL)
                 AND ((i.date ->> 'year'::text) ~ '^d+$'::text))) AS last_incident_year,
    ( SELECT min(((i.date ->> 'year'::text))::integer) AS min
           FROM (incident i
             JOIN incident_participant ip ON ((ip.incident_id = i.id)))
          WHERE ((EXISTS ( SELECT 1
                   FROM member_set ms3
                  WHERE ((ms3.member_id = ip.member_id) AND (ms3.set_id = s.id))))
                 AND (i.date IS NOT NULL)
                 AND ((i.date ->> 'year'::text) ~ '^d+$'::text))) AS first_incident_year
   FROM (((sets s
     LEFT JOIN member_set ms ON (((ms.set_id = s.id) AND (ms.until_date IS NULL))))
     LEFT JOIN member m ON ((m.id = ms.member_id)))
     LEFT JOIN member_stats ms2 ON ((ms2.member_id = m.id)))
  GROUP BY s.id, s.universe_id
"""

_SET_STATS_PREVIOUS = _SET_STATS.replace(
    "LEFT JOIN member_set ms ON (((ms.set_id = s.id) AND (ms.until_date IS NULL)))",
    "LEFT JOIN member_set ms ON ((ms.set_id = s.id))",
)


def _rebuild(sql: str) -> None:
    # asyncpg rejects multi-statement execute(), so issue these separately.
    op.execute("DROP MATERIALIZED VIEW IF EXISTS set_stats")
    op.execute(sql)
    # Required by REFRESH MATERIALIZED VIEW CONCURRENTLY in crud/stats.py.
    op.execute("CREATE UNIQUE INDEX set_stats_set_id_idx ON set_stats (set_id)")


def upgrade() -> None:
    _rebuild(_SET_STATS)


def downgrade() -> None:
    _rebuild(_SET_STATS_PREVIOUS)
