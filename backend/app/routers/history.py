"""GET /history/{entity_type}/{entity_id}: one entity's change history.

Gated exactly like the global audit log (`GET /audit/`, ADMIN only), because it
is the same data seen through a narrower window: who changed what, by account.
"""

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_global_role
from app.core.database import get_prod_session, get_session
from app.core.enums import GlobalRole
from app.crud.history import (
    HISTORY_ENTITIES,
    collect_ids,
    entity_history,
    resolve_actors,
    resolve_labels,
)
from app.schemas.history import HistoryActor, HistoryEntryRead, HistoryPage

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/{entity_type}/{entity_id}", response_model=HistoryPage)
async def read_entity_history(
    entity_type: Literal["member", "set", "alliance", "incident", "source"],
    entity_id: uuid.UUID,
    universe_id: uuid.UUID,
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
    session: Annotated[AsyncSession, Depends(get_session)],
    prod_session: Annotated[AsyncSession, Depends(get_prod_session)],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    _, model = HISTORY_ENTITIES[entity_type]
    obj = await session.get(model, entity_id)
    if obj is None or obj.universe_id != universe_id:
        raise HTTPException(status_code=404, detail=f"{entity_type} not found")

    entries = await entity_history(session, entity_type, entity_id)
    page = entries[offset : offset + limit]
    labels = await resolve_labels(session, collect_ids(page))
    # Accounts live in the prod DB whatever the DB mode (auth always uses prod).
    actors = await resolve_actors(prod_session, {e.actor_id for e in page if e.actor_id})

    items = [
        HistoryEntryRead(
            id=e.id,
            created_at=e.created_at,
            action=e.action,
            actor=HistoryActor(id=e.actor_id, email=actors.get(e.actor_id)) if e.actor_id else None,
            entity_type=e.entity_type,
            entity_id=e.entity_id,
            is_self=e.is_self,
            link=e.link,
            link_key=e.link_key,
            added=e.added,
            removed=e.removed,
            changed=e.changed,
            changes=[c.__dict__ for c in e.changes],
            baseline=e.baseline,
        )
        for e in page
    ]
    return HistoryPage(items=items, total=len(entries), labels=labels)
