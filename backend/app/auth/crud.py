import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.auth.security import hash_password, verify_password
from app.core.config import settings
from app.core.enums import UniverseRole
from app.models.auth import RefreshToken, User, UserUniverseAccess


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(session, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def create_user(session: AsyncSession, email: str, password: str, global_role=None) -> User:
    from app.core.enums import GlobalRole

    user = User(
        email=email,
        hashed_password=hash_password(password),
        global_role=global_role or GlobalRole.USER,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def set_last_login(session: AsyncSession, user: User) -> None:
    user.last_login_at = datetime.now(UTC)
    session.add(user)
    await session.commit()


async def create_refresh_token_record(session: AsyncSession, user_id: uuid.UUID) -> RefreshToken:
    jti = uuid.uuid4()
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    token = RefreshToken(jti=jti, user_id=user_id, expires_at=expires_at)
    session.add(token)
    await session.commit()
    return token


async def get_refresh_token(session: AsyncSession, jti: uuid.UUID) -> RefreshToken | None:
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.jti == jti, RefreshToken.revoked == False)  # noqa: E712
    )
    return result.scalar_one_or_none()


async def revoke_refresh_token(session: AsyncSession, jti: uuid.UUID) -> None:
    token = await session.get(RefreshToken, jti)
    if token:
        token.revoked = True
        session.add(token)
        await session.commit()


async def get_universe_role(
    session: AsyncSession, user_id: uuid.UUID, universe_id: uuid.UUID
) -> UniverseRole | None:
    result = await session.execute(
        select(UserUniverseAccess).where(
            UserUniverseAccess.user_id == user_id,
            UserUniverseAccess.universe_id == universe_id,
        )
    )
    access = result.scalar_one_or_none()
    return access.role if access else None


async def list_user_universe_access(
    session: AsyncSession, user_id: uuid.UUID
) -> list[UserUniverseAccess]:
    result = await session.execute(
        select(UserUniverseAccess).where(UserUniverseAccess.user_id == user_id)
    )
    return list(result.scalars().all())


async def upsert_user_universe_access(
    session: AsyncSession,
    user_id: uuid.UUID,
    universe_id: uuid.UUID,
    role: UniverseRole,
) -> UserUniverseAccess:
    existing = await session.execute(
        select(UserUniverseAccess).where(
            UserUniverseAccess.user_id == user_id,
            UserUniverseAccess.universe_id == universe_id,
        )
    )
    access = existing.scalar_one_or_none()
    if access is None:
        access = UserUniverseAccess(user_id=user_id, universe_id=universe_id, role=role)
        session.add(access)
    else:
        access.role = role
        session.add(access)
    await session.commit()
    await session.refresh(access)
    return access


async def delete_user_universe_access(
    session: AsyncSession, user_id: uuid.UUID, universe_id: uuid.UUID
) -> bool:
    result = await session.execute(
        select(UserUniverseAccess).where(
            UserUniverseAccess.user_id == user_id,
            UserUniverseAccess.universe_id == universe_id,
        )
    )
    access = result.scalar_one_or_none()
    if access is None:
        return False
    await session.delete(access)
    await session.commit()
    return True
