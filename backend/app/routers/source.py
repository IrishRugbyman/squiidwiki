import csv
import io
import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.database import get_session
from app.core.enums import GlobalRole, SourceReliability
from app.crud import source as crud
from app.schemas.citation import EntityType, SourceCitationRow, SourceCustodyRow
from app.schemas.common import OffsetPage
from app.schemas.source import (
    SourceBulkUpdate,
    SourceCreate,
    SourceFacets,
    SourceListItem,
    SourceListPage,
    SourceLookup,
    SourceMerge,
    SourceMergeResult,
    SourceRead,
    SourceReadDetail,
    SourceUpdate,
)

router = APIRouter(prefix="/sources", tags=["sources"])

Session = Annotated[AsyncSession, Depends(get_session)]


def _csv(items) -> StreamingResponse:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(
        [
            "id",
            "title",
            "url",
            "kind",
            "publication",
            "published",
            "reliability",
            "archive_url",
            "citations",
            "created_at",
        ]
    )
    for s in items:
        pub = s.published_at or {}
        published = "-".join(
            f"{pub[k]:02d}" if k != "year" else str(pub[k])
            for k in ("year", "month", "day")
            if isinstance(pub.get(k), int)
        )
        writer.writerow(
            [
                s.id,
                s.title,
                s.url,
                s.kind,
                s.publication or "",
                published,
                s.reliability.value,
                s.archive_url or "",
                s.counts.total,
                s.created_at.isoformat(),
            ]
        )
    return StreamingResponse(
        iter([out.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sources.csv"},
    )


@router.get("/", response_model=SourceListPage)
async def list_sources(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Session,
    q: str | None = None,
    kind: str | None = None,
    reliability: SourceReliability | None = None,
    publication: str | None = None,
    uncited: bool = False,
    sort: Literal["added", "title", "published", "cited", "reliability", "relevance"] = "added",
    order: Literal["asc", "desc"] = "desc",
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    format: Literal["json", "csv"] = "json",
):
    if format == "csv":
        items, _total, _facets = await crud.list_sources(
            session,
            universe_id,
            q=q,
            kind=kind,
            reliability=reliability,
            publication=publication,
            uncited=uncited,
            sort=sort,
            order=order,
            limit=100_000,
        )
        return _csv(items)
    items, total, facets = await crud.list_sources(
        session,
        universe_id,
        q=q,
        kind=kind,
        reliability=reliability,
        publication=publication,
        uncited=uncited,
        sort=sort,
        order=order,
        offset=offset,
        limit=limit,
    )
    return SourceListPage(
        items=[SourceListItem.model_validate(s) for s in items],
        total=total,
        facets=SourceFacets(**facets),
    )


@router.post("/", response_model=SourceRead, status_code=201)
async def create_source(data: SourceCreate, current_user: CurrentUser, session: Session):
    await crud.check_new_url(session, data.universe_id, data.url, data.allow_duplicate)
    return await crud.create_source(session, data, current_user.id)


@router.get("/search", response_model=list[SourceListItem])
async def search_sources(
    universe_id: uuid.UUID,
    q: str,
    _: CurrentUser,
    session: Session,
    limit: int = Query(20, ge=1, le=50),
):
    if len(q.strip()) < 2:
        return []
    return await crud.search_sources(session, universe_id, q, limit)


@router.get("/lookup", response_model=SourceLookup)
async def lookup_url(universe_id: uuid.UUID, url: str, _: CurrentUser, session: Session):
    """What the universe already holds for a URL: the same page, its custody
    lookup source with the record number to cite, or sources on the same site."""
    return await crud.lookup_url(session, universe_id, url)


@router.patch("/bulk", response_model=dict)
async def bulk_update(
    universe_id: uuid.UUID, data: SourceBulkUpdate, _: CurrentUser, session: Session
):
    if data.reliability is None and data.kind is None:
        raise HTTPException(422, "Nothing to change")
    n = await crud.bulk_update(
        session,
        universe_id,
        data.ids,
        data.reliability,
        data.kind.value if data.kind else None,
    )
    return {"updated": n}


@router.get("/{id}", response_model=SourceReadDetail)
async def get_source(id: uuid.UUID, universe_id: uuid.UUID, _: CurrentUser, session: Session):
    obj = await crud.get_source(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    counts = (await crud.counts_for(session, [obj.id]))[obj.id]
    return SourceReadDetail(**SourceRead.model_validate(obj).model_dump(), counts=counts)


@router.get("/{id}/citations", response_model=OffsetPage[SourceCitationRow])
async def list_source_citations(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    entity_type: EntityType,
    _: CurrentUser,
    session: Session,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    obj = await crud.get_source(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    items, total = await crud.list_source_citations(session, obj, entity_type, offset, limit)
    return OffsetPage(items=items, total=total)


@router.get("/{id}/custody-ids", response_model=list[SourceCustodyRow])
async def list_source_custody_ids(
    id: uuid.UUID, universe_id: uuid.UUID, _: CurrentUser, session: Session
):
    obj = await crud.get_source(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    return await crud.list_source_custody_ids(session, obj.id)


@router.patch("/{id}", response_model=SourceRead)
async def update_source(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    data: SourceUpdate,
    _: CurrentUser,
    session: Session,
):
    obj = await crud.update_source(session, id, universe_id, data)
    if obj is None:
        raise HTTPException(404)
    return obj


@router.post("/{id}/merge", response_model=SourceMergeResult)
async def merge_source(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    data: SourceMerge,
    session: Session,
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    """Fold this source into another: its citations, custody numbers, aliases
    and photos move across, and it is deleted."""
    src = await crud.get_source(session, id, universe_id)
    into = await crud.get_source(session, data.into_id, universe_id)
    if src is None or into is None:
        raise HTTPException(404)
    out = await crud.merge_into(session, src, into)
    return SourceMergeResult(**out, into_id=into.id)


@router.delete("/{id}", status_code=204)
async def delete_source(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    session: Session,
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
    force: bool = False,
):
    ok = await crud.delete_source(session, id, universe_id, force=force)
    if not ok:
        raise HTTPException(404)
