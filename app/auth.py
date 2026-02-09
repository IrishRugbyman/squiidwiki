"""Authentication system - simple password gate."""
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext
from itsdangerous import URLSafeTimedSerializer, BadSignature
from app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Session serializer
serializer = URLSafeTimedSerializer(settings.SECRET_KEY)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_session_token() -> str:
    """Create a signed session token."""
    return serializer.dumps("authenticated")


def verify_session_token(token: str) -> bool:
    """Verify a session token."""
    try:
        serializer.loads(token, max_age=86400 * 30)  # 30 days
        return True
    except (BadSignature, Exception):
        return False


def check_auth(request: Request) -> bool:
    """Check if request is authenticated."""
    token = request.cookies.get("session")
    if not token:
        return False
    return verify_session_token(token)


def require_auth(request: Request):
    """Dependency to require authentication."""
    if not check_auth(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )


def get_hashed_admin_password() -> str:
    """Get the hashed admin password (hash it once on startup)."""
    return get_password_hash(settings.ADMIN_PASSWORD)
