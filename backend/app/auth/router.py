import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.auth.crud import (
    authenticate_user,
    create_refresh_token_record,
    create_user,
    delete_user_universe_access,
    get_refresh_token,
    get_user_by_id,
    list_user_universe_access,
    revoke_refresh_token,
    set_last_login,
    upsert_user_universe_access,
)
from app.auth.dependencies import (
    CurrentUser,
    get_current_user_optional,
    require_global_role,
)
from app.auth.schemas import CreateUserRequest, LoginRequest, TokenResponse, UserRead
from app.auth.security import create_access_token, create_refresh_token, decode_token, hash_password
from app.core.config import settings
from app.core.database import get_prod_session as get_session
from app.core.enums import GlobalRole, UniverseRole
from app.models.auth import User
from app.models.universe import Universe
from app.schemas.common import OffsetPage

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "refresh_token"
COOKIE_OPTS = dict(httponly=True, samesite="lax", secure=settings.environment != "development")


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(REFRESH_COOKIE, token, **COOKIE_OPTS)


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, **COOKIE_OPTS)


async def _issue_tokens(
    session: AsyncSession, response: Response, user_id: uuid.UUID, global_role: str
) -> TokenResponse:
    rt_record = await create_refresh_token_record(session, user_id)
    rt = create_refresh_token(user_id, rt_record.jti)
    access = create_access_token(user_id, global_role)
    _set_refresh_cookie(response, rt)
    return TokenResponse(access_token=access)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    user = await authenticate_user(session, body.email, body.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    await set_last_login(session, user)
    return await _issue_tokens(session, response, user.id, user.global_role)


@router.post("/login/form", response_model=TokenResponse, include_in_schema=False)
async def login_form(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    """OAuth2 form endpoint for Swagger UI."""
    user = await authenticate_user(session, form.username, form.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    await set_last_login(session, user)
    return await _issue_tokens(session, response, user.id, user.global_role)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE)] = None,
) -> TokenResponse:
    invalid_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
    )
    if not refresh_token:
        raise invalid_exc
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise invalid_exc
        jti = uuid.UUID(payload["jti"])
        user_id = uuid.UUID(payload["sub"])
    except Exception:
        raise invalid_exc

    record = await get_refresh_token(session, jti)
    if not record or record.expires_at < datetime.now(UTC):
        raise invalid_exc

    await revoke_refresh_token(session, jti)

    user = await get_user_by_id(session, user_id)
    if not user:
        raise invalid_exc

    return await _issue_tokens(session, response, user.id, user.global_role)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE)] = None,
) -> None:
    if refresh_token:
        try:
            payload = decode_token(refresh_token)
            jti = uuid.UUID(payload["jti"])
            await revoke_refresh_token(session, jti)
        except Exception:
            pass
    _clear_refresh_cookie(response)


@router.get("/me", response_model=UserRead)
async def me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    body: CreateUserRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
) -> UserRead:
    """Create a user. Open only when the DB has no users (bootstrap); otherwise requires ADMIN."""
    from sqlmodel import func as _func

    from app.auth.crud import get_user_by_email

    user_count = (await session.execute(select(_func.count()).select_from(User))).scalar_one()
    if user_count > 0:
        if current_user is None or current_user.global_role != GlobalRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")
    existing = await get_user_by_email(session, body.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    # Bootstrap first user is always ADMIN; subsequent users respect the requested role.
    role = body.global_role if user_count > 0 else GlobalRole.ADMIN
    user = await create_user(session, body.email, body.password, role)
    return UserRead.model_validate(user)


# ─── User Management (admin) ──────────────────────────────────────────────────


class UserListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    global_role: GlobalRole
    created_at: datetime
    last_login_at: datetime | None


class UpdateRoleRequest(BaseModel):
    global_role: GlobalRole


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.get("/users", response_model=OffsetPage[UserListItem])
async def list_users(
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
    session: Annotated[AsyncSession, Depends(get_session)],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    total = (await session.execute(select(func.count()).select_from(User))).scalar_one()
    items = (
        (await session.execute(select(User).order_by(User.created_at).offset(offset).limit(limit)))
        .scalars()
        .all()
    )
    return OffsetPage(items=items, total=total)


@router.patch("/users/{user_id}/role", response_model=UserListItem)
async def update_user_role(
    user_id: uuid.UUID,
    body: UpdateRoleRequest,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    user = await get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(404)
    user.global_role = body.global_role
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return UserListItem.model_validate(user)


@router.post("/profile/change-password", status_code=204)
async def change_password(
    body: ChangePasswordRequest,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from app.auth.security import verify_password

    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(body.new_password)
    session.add(current_user)
    await session.commit()


# ─── Per-user universe access (admin) ─────────────────────────────────────────


class UserUniverseAccessItem(BaseModel):
    universe_id: uuid.UUID
    slug: str
    name: str
    role: UniverseRole
    granted: bool


class GrantUniverseAccessRequest(BaseModel):
    role: UniverseRole = UniverseRole.VIEWER


@router.get("/users/{user_id}/universe-access", response_model=list[UserUniverseAccessItem])
async def list_user_access(
    user_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    user = await get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(404)
    grants = {a.universe_id: a.role for a in await list_user_universe_access(session, user_id)}
    universes = (await session.execute(select(Universe).order_by(Universe.name))).scalars().all()
    return [
        UserUniverseAccessItem(
            universe_id=u.id,
            slug=u.slug,
            name=u.name,
            role=grants.get(u.id, UniverseRole.VIEWER),
            granted=u.id in grants,
        )
        for u in universes
    ]


@router.put("/users/{user_id}/universe-access/{universe_id}", status_code=204)
async def grant_user_access(
    user_id: uuid.UUID,
    universe_id: uuid.UUID,
    body: GrantUniverseAccessRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    user = await get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(404, detail="User not found")
    universe = await session.get(Universe, universe_id)
    if universe is None:
        raise HTTPException(404, detail="Universe not found")
    await upsert_user_universe_access(session, user_id, universe_id, body.role)


@router.delete("/users/{user_id}/universe-access/{universe_id}", status_code=204)
async def revoke_user_access(
    user_id: uuid.UUID,
    universe_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    ok = await delete_user_universe_access(session, user_id, universe_id)
    if not ok:
        raise HTTPException(404, detail="No such grant")
