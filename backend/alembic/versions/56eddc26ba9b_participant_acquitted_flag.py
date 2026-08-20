"""incident_participant.acquitted, and keep acquitted rows out of offender stats

`member_stats.kills` counts SHOOTER rows joined to a KILLED victim, and the
member page renders it as a red "Kills" pill. Nothing distinguished a
researcher's attribution from a role a court had rejected, so recording the
three men acquitted of the 1982 Ziglioli murder would have shown "1 kill" on
each of their profiles as bare fact.

The flag is deliberately a boolean rather than a disposition enum. The default,
False, means "attributed by research" and NOT "convicted": essentially every
participant row in this database comes from press or street sourcing and was
never tested in court, so "alleged" is already the baseline meaning of the role.
The only genuinely exceptional case is a court affirmatively clearing someone,
which is what this records. Finer distinctions (suspected, charged but never
tried) belong in `notes`, not in a column one query reads.

Because False is already correct for every existing row, there is no backfill.

Also fixes a pre-existing bug in set_stats while both views are being rebuilt:
the year guard read `~ '^d+$'`, which matches a run of literal "d" characters
rather than digits, so first_incident_year and last_incident_year were NULL for
all 70 sets. Now `^[0-9]+$`.

Revision ID: 56eddc26ba9b
Revises: 572768a81ef3
Create Date: 2026-08-20
"""

import sqlalchemy as sa

from alembic import op

revision = "56eddc26ba9b"
down_revision = "572768a81ef3"
branch_labels = None
depends_on = None


# Verbatim from pg_matviews except for the three `AND NOT ip.acquitted` guards.
# times_shot_survived is the victim side and is deliberately left alone: being
# shot is not a claim about the member, so no acquittal can bear on it.
_MEMBER_STATS = """
CREATE MATERIALIZED VIEW member_stats AS
 SELECT m.id AS member_id,
    m.universe_id,
    count(
        CASE
            WHEN (ip.role = 'SHOOTER'::participantrole AND NOT ip.acquitted) THEN 1
            ELSE NULL::integer
        END) AS shootings,
    count(
        CASE
            WHEN (ip.role = 'ASSISTED'::participantrole AND NOT ip.acquitted) THEN 1
            ELSE NULL::integer
        END) AS assists,
    count(*) FILTER (WHERE ((ip.role = 'SHOOTER'::participantrole) AND (NOT ip.acquitted)
        AND (EXISTS ( SELECT 1
           FROM incident_participant ip2
          WHERE ((ip2.incident_id = ip.incident_id) AND (ip2.role = 'VICTIM'::participantrole)
            AND (ip2.outcome = 'KILLED'::participantoutcome)))))) AS kills,
    count(
        CASE
            WHEN ((ip.role = 'VICTIM'::participantrole)
                AND (ip.outcome <> 'KILLED'::participantoutcome)) THEN 1
            ELSE NULL::integer
        END) AS times_shot_survived
   FROM (member m
     LEFT JOIN incident_participant ip ON ((ip.member_id = m.id)))
  GROUP BY m.id, m.universe_id
"""

_MEMBER_STATS_PREVIOUS = (
    _MEMBER_STATS.replace(" AND NOT ip.acquitted", "")
    .replace("(NOT ip.acquitted)\n        AND ", "")
    .replace("AND (NOT ip.acquitted)\n        ", "")
)

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
                 AND ((i.date ->> 'year'::text) ~ '^[0-9]+$'::text))) AS last_incident_year,
    ( SELECT min(((i.date ->> 'year'::text))::integer) AS min
           FROM (incident i
             JOIN incident_participant ip ON ((ip.incident_id = i.id)))
          WHERE ((EXISTS ( SELECT 1
                   FROM member_set ms3
                  WHERE ((ms3.member_id = ip.member_id) AND (ms3.set_id = s.id))))
                 AND (i.date IS NOT NULL)
                 AND ((i.date ->> 'year'::text) ~ '^[0-9]+$'::text))) AS first_incident_year
   FROM (((sets s
     LEFT JOIN member_set ms ON (((ms.set_id = s.id) AND (ms.until_date IS NULL))))
     LEFT JOIN member m ON ((m.id = ms.member_id)))
     LEFT JOIN member_stats ms2 ON ((ms2.member_id = m.id)))
  GROUP BY s.id, s.universe_id
"""

_SET_STATS_PREVIOUS = _SET_STATS.replace("'^[0-9]+$'::text", "'^d+$'::text")


def _rebuild(member_sql: str, set_sql: str) -> None:
    # set_stats reads member_stats, so it has to go first and come back last.
    # asyncpg rejects multi-statement execute(), so issue these separately.
    op.execute("DROP MATERIALIZED VIEW IF EXISTS set_stats")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS member_stats")
    op.execute(member_sql)
    # Both unique indexes are required by REFRESH ... CONCURRENTLY in crud/stats.py.
    op.execute("CREATE UNIQUE INDEX member_stats_member_id_idx ON member_stats (member_id)")
    op.execute(set_sql)
    op.execute("CREATE UNIQUE INDEX set_stats_set_id_idx ON set_stats (set_id)")


def upgrade() -> None:
    op.add_column(
        "incident_participant",
        sa.Column("acquitted", sa.Boolean(), nullable=False, server_default="false"),
    )
    _rebuild(_MEMBER_STATS, _SET_STATS)


def downgrade() -> None:
    _rebuild(_MEMBER_STATS_PREVIOUS, _SET_STATS_PREVIOUS)
    op.drop_column("incident_participant", "acquitted")
