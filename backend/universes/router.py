from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.auth_utils import get_current_admin_user, get_current_user
from backend.auth.schemas import User
from backend.database.base_class import get_db
from backend.database.models import Universe
from backend.universes import service
from backend.universes.schemas import (
    GrantAccessRequest,
    UniverseAccessResponse,
    UniverseCreate,
    UniverseResponse,
)

router = APIRouter(prefix="/universes", tags=["universes"])


@router.get("/", response_model=list[UniverseResponse])
async def list_universes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.is_admin:
        return await service.list_universes(db)
    return await service.list_user_universes(db, current_user.id)


@router.post("/", response_model=UniverseResponse, status_code=status.HTTP_201_CREATED)
async def create_universe(
    payload: UniverseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    existing = await service.get_universe_by_slug(db, payload.slug)
    if existing:
        raise HTTPException(status_code=409, detail=f"Universe slug '{payload.slug}' already exists")
    universe = await service.create_universe(db, payload, created_by_id=current_user.id)
    await db.commit()
    return universe


@router.get("/{slug}", response_model=UniverseResponse)
async def get_universe(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    universe = await service.get_universe_by_slug(db, slug)
    if not universe:
        raise HTTPException(status_code=404, detail=f"Universe '{slug}' not found")
    return universe


@router.post("/{slug}/access", response_model=UniverseAccessResponse)
async def grant_access(
    slug: str,
    payload: GrantAccessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    universe = await service.get_universe_by_slug(db, slug)
    if not universe:
        raise HTTPException(status_code=404, detail=f"Universe '{slug}' not found")
    access = await service.grant_access(db, universe.id, payload.user_id, payload.role)
    await db.commit()
    return access


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_universe(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    universe = await service.get_universe_by_slug(db, slug)
    if not universe:
        raise HTTPException(status_code=404, detail=f"Universe '{slug}' not found")
    await service.soft_delete_universe(db, universe)
    await db.commit()
