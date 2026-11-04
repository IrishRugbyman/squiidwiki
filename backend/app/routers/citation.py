"""Citations: cite a source on a record, edit what it supports, reorder, detach.

Municipalities live in prod whatever the DB mode (routers/municipality.py),
and a citation must sit in the database its record does, so a municipality's
citations are read and written through the prod session, as its photos are.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.core.database import get_prod_session, get_session, resolve_prod_universe
from app.crud import citation as crud
from app.schemas.citation import (
    CitationBatch,
    CitationBatchResult,
    CitationCreate,
    CitationOrder,
    CitationRead,
    CitationUpdate,
)

router = APIRouter(prefix="/citations", tags=["citations"])

Session = Annotated[AsyncSession, Depends(get_session)]
ProdSession = Annotated[AsyncSession, Depends(get_prod_session)]


async def _scope(
    entity_type: str, universe_id: uuid.UUID, session: AsyncSession, prod: AsyncSession
) -> tuple[AsyncSession, uuid.UUID]:
    if entity_type != "municipality":
        return session, universe_id
    uid = await resolve_prod_universe(session, prod, universe_id)
    if uid is None:
        raise HTTPException(404, f"Universe {universe_id} not found in prod DB")
    return prod, uid


async def _find(id: uuid.UUID, universe_id: uuid.UUID, session: AsyncSession, prod: AsyncSession):
    """A citation by id: in the active DB, or in prod for a municipality's."""
    obj = await crud.get_citation(session, id, universe_id)
    if obj is not None:
        return session, obj
    uid = await resolve_prod_universe(session, prod, universe_id)
    if uid is not None:
        obj = await crud.get_citation(prod, id, uid)
        if obj is not None:
            return prod, obj
    raise HTTPException(404)


@router.get("/", response_model=list[CitationRead])
async def list_citations(
    universe_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    _: CurrentUser,
    session: Session,
    prod: ProdSession,
):
    s, _uid = await _scope(entity_type, universe_id, session, prod)
    return await crud.list_citations(s, entity_type, entity_id)


@router.post("/", response_model=CitationRead, status_code=201)
async def create_citation(
    universe_id: uuid.UUID,
    data: CitationCreate,
    current_user: CurrentUser,
    session: Session,
    prod: ProdSession,
):
    s, uid = await _scope(data.entity_type, universe_id, session, prod)
    out = await crud.create_citation(s, uid, data, current_user.id)
    await s.commit()
    return out


@router.post("/batch", response_model=CitationBatchResult)
async def batch_citations(
    universe_id: uuid.UUID,
    data: CitationBatch,
    current_user: CurrentUser,
    session: Session,
    prod: ProdSession,
):
    types = {i.entity_type == "municipality" for i in data.items}
    if len(types) > 1:
        raise HTTPException(422, "Cite municipalities in a batch of their own")
    s, uid = await _scope(data.items[0].entity_type, universe_id, session, prod)
    out = await crud.batch_citations(s, uid, data.items, data.on_conflict, current_user.id)
    await s.commit()
    return out


@router.put("/order", response_model=list[CitationRead])
async def reorder_citations(
    universe_id: uuid.UUID,
    data: CitationOrder,
    _: CurrentUser,
    session: Session,
    prod: ProdSession,
):
    s, uid = await _scope(data.entity_type, universe_id, session, prod)
    if await crud.entity_universe(s, data.entity_type, data.entity_id) != uid:
        raise HTTPException(404)
    out = await crud.reorder_citations(s, data.entity_type, data.entity_id, data.ids)
    await s.commit()
    return out


@router.patch("/{id}", response_model=CitationRead)
async def update_citation(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    data: CitationUpdate,
    _: CurrentUser,
    session: Session,
    prod: ProdSession,
):
    s, obj = await _find(id, universe_id, session, prod)
    out = await crud.update_citation(s, obj, data)
    await s.commit()
    return out


@router.delete("/{id}", status_code=204)
async def delete_citation(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Session,
    prod: ProdSession,
):
    s, obj = await _find(id, universe_id, session, prod)
    await s.delete(obj)
    await s.commit()
