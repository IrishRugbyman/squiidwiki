"""Shared FastAPI dependencies for universe-scoped requests."""
from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.auth_utils import get_current_user
from backend.auth.schemas import User
from backend.database.base_class import get_db
from backend.database.models import Universe, UniverseRole, UserUniverseAccess

_ROLE_ORDER = {UniverseRole.VIEWER: 0, UniverseRole.EDITOR: 1, UniverseRole.ADMIN: 2}


async def get_active_universe(
    x_universe_id: str | None = Header(None, alias="X-Universe-Id"),
    universe: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Universe:
    """Resolve the active universe from X-Universe-Id header or ?universe= query param."""
    slug = x_universe_id or universe
    if not slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No universe specified. Use X-Universe-Id header or ?universe=<slug>.",
        )

    result = await db.execute(
        select(Universe).where(Universe.slug == slug, Universe.deleted_at.is_(None))
    )
    univ = result.scalars().first()
    if not univ:
        raise HTTPException(status_code=404, detail=f"Universe '{slug}' not found")

    if current_user.is_admin:
        return univ

    access_result = await db.execute(
        select(UserUniverseAccess).where(
            UserUniverseAccess.user_id == current_user.id,
            UserUniverseAccess.universe_id == univ.id,
        )
    )
    if not access_result.scalars().first():
        raise HTTPException(status_code=403, detail="Access denied to this universe")

    return univ


def require_universe_role(min_role: UniverseRole):
    """Dependency factory — ensures the caller has at least `min_role` in the active universe."""
    async def _check(
        univ: Universe = Depends(get_active_universe),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> Universe:
        if current_user.is_admin:
            return univ
        result = await db.execute(
            select(UserUniverseAccess).where(
                UserUniverseAccess.user_id == current_user.id,
                UserUniverseAccess.universe_id == univ.id,
            )
        )
        access = result.scalars().first()
        if not access or _ROLE_ORDER[access.role] < _ROLE_ORDER[min_role]:
            raise HTTPException(status_code=403, detail="Insufficient universe role")
        return univ

    return _check
