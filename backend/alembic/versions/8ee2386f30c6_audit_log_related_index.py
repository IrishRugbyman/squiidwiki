"""audit_log: index the far-side ids of link-change rows

The History tab reads two kinds of audit_log row for an entity: its own
snapshots (entity_type + entity_id, already indexed) and link-change rows
written on *another* entity that touched it - "Member A was added to this set"
is a row on the member whose diff_json carries the set's id in `_related`
(see `record_link_change` in app/core/audit.py). This GIN index makes that
containment lookup (`diff_json -> '_related' @> '["<id>"]'`) cheap. Rows
without the key index nothing, so snapshot rows cost no index space.

Revision ID: 8ee2386f30c6
Revises: 3c7f32fad6eb
Create Date: 2026-11-03
"""

from alembic import op

revision = "8ee2386f30c6"
down_revision = "3c7f32fad6eb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_audit_log_diff_json_related ON audit_log "
        "USING gin ((diff_json -> '_related') jsonb_path_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_audit_log_diff_json_related")
