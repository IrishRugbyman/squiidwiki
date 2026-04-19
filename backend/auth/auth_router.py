from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.auth_utils import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_active_user,
    get_current_admin_user,
    get_password_hash,
)
from backend.auth.schemas import User, UserCreate
from backend.database.base_class import get_db
from backend.database.models import GlobalRole, User as UserModel
from backend.settings import settings
from backend.templates import templates

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request, "error": None})


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Invalid username or password"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    access_token = create_access_token({"sub": user.username})
    refresh_token = create_refresh_token({"sub": user.username})

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=settings.auth.refresh_token_expire_days * 86400,
    )
    return response


@router.post("/refresh")
async def refresh_token(request: Request, db: AsyncSession = Depends(get_db)):
    """Issue a new access token from a valid refresh token cookie."""
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("typ") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    result = await db.execute(select(UserModel).where(UserModel.username == username))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    new_access_token = create_access_token({"sub": username})
    response = JSONResponse({"access_token": new_access_token, "token_type": "bearer"})
    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_form(
    request: Request,
    current_user: User = Depends(get_current_admin_user),
):
    return templates.TemplateResponse("auth/register.html", {"request": request, "error": None})


@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    is_admin: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    result = await db.execute(select(UserModel).where(UserModel.username == username))
    if result.scalars().first():
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "Username already registered", "username": username},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    db.add(UserModel(
        username=username,
        hashed_password=get_password_hash(password),
        global_role=GlobalRole.ADMIN if is_admin else GlobalRole.USER,
    ))
    await db.commit()
    return RedirectResponse(url="/auth/users", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/users", response_class=HTMLResponse)
async def list_users(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    result = await db.execute(select(UserModel))
    users = result.scalars().all()
    return templates.TemplateResponse("auth/users.html", {"request": request, "users": users})


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    user = await db.get(UserModel, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "username": user.username, "global_role": user.global_role}


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    username: str = Form(...),
    is_admin: bool = Form(False),
    password: str = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    user = await db.get(UserModel, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.username == "admin" and username != "admin":
        raise HTTPException(status_code=403, detail="Cannot change admin username")
    if username != user.username:
        result = await db.execute(select(UserModel).where(UserModel.username == username))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Username already exists")

    user.username = username
    user.global_role = GlobalRole.ADMIN if is_admin else GlobalRole.USER
    if password and password.strip():
        user.hashed_password = get_password_hash(password)
    await db.commit()
    return {"success": True}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    user = await db.get(UserModel, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.username in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Cannot delete protected user")
    if user.id == current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete your own account")
    await db.delete(user)
    await db.commit()
    return {"success": True}


@router.get("/profile", response_class=HTMLResponse)
async def user_profile(
    request: Request,
    current_user: User = Depends(get_current_active_user),
):
    return templates.TemplateResponse("auth/profile.html", {"request": request, "user": current_user})
