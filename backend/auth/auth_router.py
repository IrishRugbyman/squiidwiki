from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.auth.auth_utils import (
    authenticate_user, create_access_token, get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES, get_current_active_user, get_current_admin_user
)
from backend.templates import templates
from backend.database.imports import Users, get_db
from backend.auth.schemas import User, UserCreate

router = APIRouter()

@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    """Display the login form."""
    return templates.TemplateResponse(
        "auth/login.html", 
        {"request": request, "error": None}
    )

@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Process login form submission."""
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Invalid username or password"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Create response with cookie
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return response

@router.get("/logout")
async def logout():
    """Log out the current user."""
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response

@router.get("/register", response_class=HTMLResponse)
async def register_form(
    request: Request,
    current_user: User = Depends(get_current_admin_user)
):
    """Display the registration form (admin only)."""
    return templates.TemplateResponse(
        "auth/register.html",
        {"request": request, "error": None}
    )

@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    is_admin: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Process registration form submission (admin only)."""
    # Check if username already exists
    db_user = db.query(Users).filter(Users.username == username).first()
    if db_user:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "error": "Username already registered",
                "username": username
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Create new user
    hashed_password = get_password_hash(password)
    new_user = Users(
        username=username,
        password_hash=hashed_password,
        is_admin=is_admin
    )
    db.add(new_user)
    db.commit()
    
    return RedirectResponse(
        url="/auth/users",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.get("/users", response_class=HTMLResponse)
async def list_users(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """List all users (admin only)."""
    users = db.query(Users).all()
    return templates.TemplateResponse(
        "auth/users.html",
        {"request": request, "users": users}
    )

@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get a user's details (admin only)."""
    user = db.get(Users, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "username": user.username,
        "is_admin": user.is_admin
    }

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    username: str = Form(...),
    is_admin: bool = Form(False),
    password: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a user (admin only)."""
    user = db.get(Users, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Special protection for admin user
    if user.username == "admin" and username != "admin":
        raise HTTPException(status_code=403, detail="Cannot change admin username")
    
    # Check if username already exists (if username is changed)
    if username != user.username:
        existing_user = db.query(Users).filter(Users.username == username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
    
    # Update user fields
    user.username = username
    user.is_admin = is_admin
    
    # Update password if provided
    if password and password.strip():
        user.password_hash = get_password_hash(password)
    
    db.commit()
    return {"success": True}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a user (admin only)."""
    user = db.get(Users, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Special protection for admin and current user
    if user.username == "admin" or user.username == "superadmin":
        raise HTTPException(status_code=403, detail="Cannot delete protected user")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete your own account")
    
    db.delete(user)
    db.commit()
    return {"success": True}

@router.get("/profile", response_class=HTMLResponse)
async def user_profile(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Display the current user's profile."""
    return templates.TemplateResponse(
        "auth/profile.html",
        {"request": request, "user": current_user}
    )

@router.get("/bypass")
async def auth_bypass():
    """
    Development-only endpoint to bypass authentication.
    ONLY AVAILABLE IN DEVELOPMENT MODE.
    """
    if not settings.AUTH_BYPASS_ENABLED:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Auth bypass is disabled in production mode"}
        )
        
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="auth_bypass",
        value=settings.AUTH_BYPASS_CODE,
        httponly=True,
        max_age=60 * 60 * 24 * 7,  # 7 days
    )
    return response 