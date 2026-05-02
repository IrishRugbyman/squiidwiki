import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.database import get_session
from app.core.enums import GlobalRole
from app.crud import research_note as crud
from app.schemas.common import OffsetPage
from app.schemas.research_note import (
    ResearchNoteCreate,
    ResearchNoteListItem,
    ResearchNoteRead,
    ResearchNoteUpdate,
)

router = APIRouter(prefix="/research", tags=["research"])


@router.get("/", response_model=OffsetPage[ResearchNoteListItem])
async def list_notes(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    items, total = await crud.list_notes(session, universe_id, offset=offset, limit=limit)
    return OffsetPage(items=items, total=total)


@router.post("/", response_model=ResearchNoteRead, status_code=201)
async def create_note(
    data: ResearchNoteCreate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await crud.create_note(session, data, current_user.id)


@router.get("/search", response_model=list[ResearchNoteListItem])
async def search_notes(
    universe_id: uuid.UUID,
    q: str,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    if len(q.strip()) < 2:
        return []
    return await crud.search_notes(session, universe_id, q)


@router.get("/{id}", response_model=ResearchNoteRead)
async def get_note(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_note(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    return obj


@router.patch("/{id}", response_model=ResearchNoteRead)
async def update_note(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    data: ResearchNoteUpdate,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.update_note(session, id, universe_id, data)
    if obj is None:
        raise HTTPException(404)
    return obj


@router.delete("/{id}", status_code=204)
async def delete_note(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    __: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    ok = await crud.delete_note(session, id, universe_id)
    if not ok:
        raise HTTPException(404)
