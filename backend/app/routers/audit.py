import uuid
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.database import get_session
from app.core.enums import AuditAction, GlobalRole
from app.models.auth import AuditLog
from app.schemas.common import OffsetPage

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditLogRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    entity_type: str
    entity_id: uuid.UUID
    action: AuditAction
    diff_json: Optional[dict]
    created_at: datetime


@router.get("/", response_model=OffsetPage[AuditLogRead])
async def list_audit_logs(
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
    session: Annotated[AsyncSession, Depends(get_session)],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    entity_type: Optional[str] = None,
    user_id: Optional[uuid.UUID] = None,
    action: Optional[AuditAction] = None,
):
    stmt = select(AuditLog)
    count_stmt = select(func.count()).select_from(AuditLog)

    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
        count_stmt = count_stmt.where(AuditLog.entity_type == entity_type)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
        count_stmt = count_stmt.where(AuditLog.user_id == user_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
        count_stmt = count_stmt.where(AuditLog.action == action)

    total = (await session.execute(count_stmt)).scalar_one()
    items = (await session.execute(
        stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    )).scalars().all()

    return OffsetPage(items=items, total=total)
