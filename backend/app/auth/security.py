import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from app.core.config import settings

_ph = PasswordHasher()

ALGORITHM = "HS256"


def hash_password(plain: str) -> str:
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: uuid.UUID, global_role: str) -> str:
    expire = _now() + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": global_role,
        "type": "access",
        "exp": expire,
        "iat": _now(),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(user_id: uuid.UUID, jti: uuid.UUID) -> str:
    expire = _now() + timedelta(days=settings.refresh_token_expire_days)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "jti": str(jti),
        "type": "refresh",
        "exp": expire,
        "iat": _now(),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Raises JWTError if invalid/expired."""
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
