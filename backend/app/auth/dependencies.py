import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import decode_token
from app.core.audit import current_user_id
from app.core.database import get_session
from app.core.enums import GlobalRole, UniverseRole
from app.models.auth import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login/form")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exc
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise credentials_exc

    from app.auth.crud import get_user_by_id
    user = await get_user_by_id(session, user_id)
    if user is None:
        raise credentials_exc

    current_user_id.set(user.id)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_global_role(min_role: GlobalRole):
    role_order = {GlobalRole.USER: 0, GlobalRole.ADMIN: 1}

    async def dependency(current_user: CurrentUser) -> User:
        if role_order[current_user.global_role] < role_order[min_role]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return Depends(dependency)


def require_universe_role(universe_id: uuid.UUID, min_role: UniverseRole):
    role_order = {UniverseRole.VIEWER: 0, UniverseRole.EDITOR: 1, UniverseRole.ADMIN: 2}

    async def dependency(
        current_user: CurrentUser,
        session: Annotated[AsyncSession, Depends(get_session)],
    ) -> User:
        from app.core.enums import GlobalRole as GR
        if current_user.global_role == GR.ADMIN:
            return current_user
        from app.auth.crud import get_universe_role
        role = await get_universe_role(session, current_user.id, universe_id)
        if role is None or role_order[role] < role_order[min_role]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient universe permissions")
        return current_user

    return Depends(dependency)
