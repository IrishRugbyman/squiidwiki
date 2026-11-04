import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.database import get_session
from app.core.enums import GlobalRole
from app.crud import citation as citation_crud
from app.crud import court_case as crud
from app.crud import incident as incident_crud
from app.schemas.common import OffsetPage
from app.schemas.court_case import (
    CourtCaseBrief,
    CourtCaseCreate,
    CourtCaseListItem,
    CourtCaseRead,
    CourtCaseReadDetail,
    CourtCaseSetBrief,
    CourtCaseSpellBrief,
    CourtCaseUpdate,
    DefendantCreate,
    DefendantRead,
    DefendantUpdate,
    SentencingEvent,
)

router = APIRouter(prefix="/court-cases", tags=["court-cases"])


async def _read(session: AsyncSession, obj) -> CourtCaseRead:
    read = CourtCaseRead.model_validate(obj)
    read.universe_slug = (await incident_crud.universe_slugs(session, {obj.universe_id})).get(
        obj.universe_id
    )
    return read


async def _case_or_404(session: AsyncSession, id_or_slug: str, universe_id: uuid.UUID):
    try:
        obj = await crud.get_court_case(session, uuid.UUID(id_or_slug), universe_id)
    except ValueError:
        obj = await crud.get_court_case_by_slug(session, id_or_slug, universe_id)
    if obj is None:
        raise HTTPException(404)
    return obj


@router.get("/", response_model=OffsetPage[CourtCaseListItem])
async def list_court_cases(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    member_id: uuid.UUID | None = None,
    set_id: uuid.UUID | None = None,
    incident_id: uuid.UUID | None = None,
    alliance_id: uuid.UUID | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """A universe's cases, or, filtered, every case a member, set or incident is
    in whatever universe the case sits in."""
    if member_id is not None:
        items = await crud.list_court_cases_by_member(session, member_id)
    elif set_id is not None:
        items = await crud.list_court_cases_by_set(session, set_id)
    elif incident_id is not None:
        items = await crud.list_court_cases_by_incident(session, incident_id)
    elif alliance_id is not None:
        items = await crud.list_court_cases_by_alliance(session, alliance_id)
    else:
        items, total = await crud.list_court_cases(session, universe_id, offset=offset, limit=limit)
        return OffsetPage(items=items, total=total)
    return OffsetPage(items=items, total=len(items))


@router.get("/sentencings", response_model=list[SentencingEvent])
async def list_sentencings(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Dated sentencings in a universe's cases, for the timeline and calendar."""
    return await crud.list_sentencings(session, universe_id)


@router.get("/search", response_model=list[CourtCaseListItem])
async def search_court_cases(
    universe_id: uuid.UUID,
    q: str,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    if len(q.strip()) < 2:
        return []
    return await crud.search_court_cases(session, universe_id, q)


@router.post("/", response_model=CourtCaseRead, status_code=201)
async def create_court_case(
    data: CourtCaseCreate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await _read(session, await crud.create_court_case(session, data, current_user.id))


@router.get("/{id_or_slug}", response_model=CourtCaseReadDetail)
async def get_court_case(
    id_or_slug: str,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await _case_or_404(session, id_or_slug, universe_id)
    defendants = await crud.list_defendants(session, obj.id)
    spells = await crud.list_case_spells(session, obj.id)
    members = await crud.members_by_id(
        session,
        {d.member_id for d in defendants if d.member_id} | {s.member_id for s in spells},
    )
    parent, children = await crud.related_cases(session, obj)
    universes = {obj.universe_id} | {m.universe_id for m in members.values()}
    universes |= {c.universe_id for c in [parent, *children] if c is not None}
    slugs = await incident_crud.universe_slugs(session, universes)

    def who(member_id):
        m = members.get(member_id)
        if m is None:
            return {}
        return {
            "member_name": m.display_name,
            "member_slug": m.slug,
            "member_universe_slug": slugs.get(m.universe_id),
        }

    def brief(case):
        b = CourtCaseBrief.model_validate(case)
        b.universe_slug = slugs.get(case.universe_id)
        return b

    defendant_reads = []
    for d in defendants:
        dr = DefendantRead.model_validate(d)
        for k, v in who(d.member_id).items():
            setattr(dr, k, v)
        if d.member_id is not None and (m := members.get(d.member_id)):
            dr.member_status = m.status
        defendant_reads.append(dr)
    incidents = await crud.list_case_incidents(session, obj.id)
    citations = await citation_crud.list_citations(session, "court_case", obj.id)
    base = CourtCaseRead.model_validate(obj)
    base.universe_slug = slugs.get(obj.universe_id)
    return CourtCaseReadDetail(
        **base.model_dump(),
        defendants=defendant_reads,
        incidents=await incident_crud.enrich_participant_names(session, incidents),
        sets=[
            CourtCaseSetBrief(id=s.id, name=s.name, slug=s.slug)
            for s in await crud.list_case_sets(session, obj.id)
        ],
        citations=citations,
        spells=[
            CourtCaseSpellBrief(
                id=s.id,
                member_id=s.member_id,
                from_date=s.from_date,
                to_date=s.to_date,
                facility=s.facility,
                life_sentence=s.life_sentence,
                **who(s.member_id),
            )
            for s in spells
        ],
        parent=brief(parent) if parent else None,
        children=[brief(c) for c in children],
    )


@router.patch("/{id}", response_model=CourtCaseRead)
async def update_court_case(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    data: CourtCaseUpdate,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.update_court_case(session, id, universe_id, data)
    if obj is None:
        raise HTTPException(404)
    return await _read(session, obj)


@router.delete("/{id}", status_code=204)
async def delete_court_case(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    if not await crud.delete_court_case(session, id, universe_id):
        raise HTTPException(404)


@router.post("/{id}/defendants", response_model=DefendantRead, status_code=201)
async def add_defendant(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    data: DefendantCreate,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    case = await crud.get_court_case(session, id, universe_id)
    if case is None:
        raise HTTPException(404)
    return await crud.add_defendant(session, case, data)


@router.patch("/{id}/defendants/{defendant_id}", response_model=DefendantRead)
async def update_defendant(
    id: uuid.UUID,
    defendant_id: uuid.UUID,
    universe_id: uuid.UUID,
    data: DefendantUpdate,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    case = await crud.get_court_case(session, id, universe_id)
    if case is None:
        raise HTTPException(404)
    obj = await crud.update_defendant(session, case, defendant_id, data)
    if obj is None:
        raise HTTPException(404)
    return obj


@router.delete("/{id}/defendants/{defendant_id}", status_code=204)
async def delete_defendant(
    id: uuid.UUID,
    defendant_id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    case = await crud.get_court_case(session, id, universe_id)
    if case is None or not await crud.delete_defendant(session, case, defendant_id):
        raise HTTPException(404)
