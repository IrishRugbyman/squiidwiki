"""sources + auditlog: citation tracking and immutable write log

Revision ID: 0006_sources_auditlog
Revises: 0005_incidents
Create Date: 2026-04-19
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_sources_auditlog"
down_revision = "0005_incidents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Sources
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("universe_id", sa.Integer(), sa.ForeignKey("universes.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("publication", sa.Text(), nullable=True),
        sa.Column("published_at", sa.JSON(), nullable=True),
        sa.Column("published_at_sortable", sa.Date(), nullable=True),
        sa.Column("accessed_at", sa.Date(), nullable=True),
        sa.Column("reliability", sa.Text(), nullable=False, server_default="unverified"),
        sa.Column("archive_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )

    # Member ↔ Source M2M
    op.create_table(
        "member_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("member_id", sa.Integer(), sa.ForeignKey("members.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True),
    )
    op.create_unique_constraint("uq_member_source", "member_sources", ["member_id", "source_id"])

    # Incident ↔ Source M2M
    op.create_table(
        "incident_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("incident_id", sa.Integer(), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True),
    )
    op.create_unique_constraint("uq_incident_source", "incident_sources", ["incident_id", "source_id"])

    # AuditLog
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("diff_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_audit_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("idx_audit_user", "audit_logs", ["user_id"])
    op.create_index("idx_audit_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("incident_sources")
    op.drop_table("member_sources")
    op.drop_table("sources")
