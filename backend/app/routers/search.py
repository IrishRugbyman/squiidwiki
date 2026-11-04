import uuid
from typing import Annotated, Any, Literal, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.core.database import get_session
from app.crud import text_search as crud

router = APIRouter(prefix="/search", tags=["search"])

EntityType = Literal["member", "set", "alliance", "incident", "source"]


class SnippetSegment(BaseModel):
    text: str
    hit: bool


class TextSearchHit(BaseModel):
    entity_type: EntityType
    id: uuid.UUID
    label: str
    slug: Optional[str] = None
    date: Optional[dict[str, Any]] = None
    rank: float
    snippet: list[SnippetSegment]


@router.get("/text", response_model=list[TextSearchHit])
async def search_text(
    universe_id: uuid.UUID,
    q: str,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    types: Annotated[list[EntityType] | None, Query()] = None,
    limit: int = Query(20, ge=1, le=100),
):
    """Full-text search over biographies, set bios, alliance descriptions,
    incident narratives and source titles + notes, best match first.

    ``q`` takes web-search syntax: ``"exact phrase"``, ``-word``, ``a or b``.
    """
    if len(q.strip()) < 3:
        return []
    return await crud.search_text(session, universe_id, q.strip(), types=types, limit=limit)
