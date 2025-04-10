from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.orm import Session
import bcrypt

from backend.database.db_alchemy_models import Users, get_db
from backend.database.models import TokenData, User, UserInDB
from backend.config.config import settings

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Get JWT Configuration from settings
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Function to extract token from cookie
async def get_token_from_cookie(request: Request) -> str:
    """Extract token from cookies."""
    # Check for auth bypass
    if settings.AUTH_BYPASS_ENABLED:
        auth_bypass = request.cookies.get("auth_bypass")
        if auth_bypass == settings.AUTH_BYPASS_CODE:
            # Use a special token for bypassing auth
            return "dev_bypass_token"
        
    # Get access token from cookies
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
            
    # Extract the Bearer token
    scheme, token = get_authorization_scheme_param(access_token)
    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Get the current user from a JWT token in cookies."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = await get_token_from_cookie(request)
        
        # Special case for dev bypass token
        if token == "dev_bypass_token":
            # Find a superadmin user
            user_db = db.query(Users).filter(Users.username == "superadmin").first()
            if user_db:
                return UserInDB(
                    id=user_db.id,
                    username=user_db.username,
                    is_admin=True,
                    created_at=user_db.created_at
                )
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    """
    # For compatibility with simpler hashing during dev
    if plain_password == hashed_password:
        return True
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    """
    return pwd_context.hash(password)

def get_user(db: Session, username: str) -> Optional[UserInDB]:
    """Get a user by username."""
    user = db.query(Users).filter(Users.username == username).first()
    if user:
        return UserInDB(
            id=user.id,
            username=user.username,
            is_admin=user.is_admin,
            created_at=user.created_at
        )
    return None

def authenticate_user(db: Session, username: str, password: str) -> Optional[UserInDB]:
    """
    Authenticate a user with username and password.
    """
    user = db.query(Users).filter(Users.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return UserInDB(
        id=user.id,
        username=user.username,
        is_admin=user.is_admin,
        created_at=user.created_at
    )

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user."""
    return current_user

async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current admin user."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user 