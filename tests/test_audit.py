"""Tests for AuditLog model and audit listener behavior."""
from __future__ import annotations

import json

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.audit.listener import register_audit_listener, unregister_audit_listener
from backend.database.models import (
    AuditAction,
    AuditLog,
    Member,
    MemberStatus,
    Set,
    SetType,
)


class TestAuditLogModel:
    async def test_audit_log_create(self, db: AsyncSession):
        log = AuditLog(
            entity_type="members",
            entity_id=1,
            action=AuditAction.CREATE,
        )
        db.add(log)
        await db.flush()

        result = await db.execute(select(AuditLog).where(AuditLog.id == log.id))
        loaded = result.scalars().first()
        assert loaded is not None
        assert loaded.entity_type == "members"
        assert loaded.action == AuditAction.CREATE
        assert loaded.diff_json is None

    async def test_audit_log_with_diff(self, db: AsyncSession):
        diff = json.dumps({"name": {"old": "OldName", "new": "NewName"}})
        log = AuditLog(
            entity_type="sets",
            entity_id=5,
            action=AuditAction.UPDATE,
            diff_json=diff,
        )
        db.add(log)
        await db.flush()

        result = await db.execute(select(AuditLog).where(AuditLog.id == log.id))
        loaded = result.scalars().first()
        parsed = json.loads(loaded.diff_json)
        assert parsed["name"]["new"] == "NewName"

    async def test_audit_log_delete_action(self, db: AsyncSession):
        log = AuditLog(
            entity_type="members",
            entity_id=42,
            action=AuditAction.DELETE,
        )
        db.add(log)
        await db.flush()

        result = await db.execute(select(AuditLog).where(AuditLog.id == log.id))
        loaded = result.scalars().first()
        assert loaded.action == AuditAction.DELETE

    async def test_audit_log_no_deleted_at(self, db: AsyncSession):
        """AuditLog is append-only — no soft_delete mixin."""
        log = AuditLog(entity_type="sets", entity_id=1, action=AuditAction.CREATE)
        assert not hasattr(log, "deleted_at")


class TestAuditListener:
    """Verify the flush listener emits AuditLog rows."""

    async def test_listener_emits_create_on_new_entity(self, db: AsyncSession):
        register_audit_listener()
        try:
            member = Member(name="AuditedMember", status=MemberStatus.ALIVE)
            db.add(member)
            await db.flush()

            result = await db.execute(
                select(AuditLog).where(
                    AuditLog.entity_type == "members",
                    AuditLog.entity_id == member.id,
                    AuditLog.action == AuditAction.CREATE,
                )
            )
            assert result.scalars().first() is not None
        finally:
            unregister_audit_listener()

    async def test_listener_emits_update_on_dirty_entity(self, db: AsyncSession):
        register_audit_listener()
        try:
            member = Member(name="BeforeUpdate", status=MemberStatus.ALIVE)
            db.add(member)
            await db.flush()

            member.name = "AfterUpdate"
            await db.flush()

            result = await db.execute(
                select(AuditLog).where(
                    AuditLog.entity_type == "members",
                    AuditLog.entity_id == member.id,
                    AuditLog.action == AuditAction.UPDATE,
                )
            )
            log = result.scalars().first()
            assert log is not None
            diff = json.loads(log.diff_json)
            assert diff["name"]["new"] == "AfterUpdate"
        finally:
            unregister_audit_listener()

    async def test_listener_emits_delete_on_soft_delete(self, db: AsyncSession):
        register_audit_listener()
        try:
            s = Set(name="SoftDeleteSet", type=SetType.ACTIVE)
            db.add(s)
            await db.flush()

            s.soft_delete()
            await db.flush()

            result = await db.execute(
                select(AuditLog).where(
                    AuditLog.entity_type == "sets",
                    AuditLog.entity_id == s.id,
                    AuditLog.action == AuditAction.DELETE,
                )
            )
            assert result.scalars().first() is not None
        finally:
            unregister_audit_listener()
