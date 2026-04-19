from fastapi import Request, status
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt

from backend.auth.auth_utils import ALGORITHM
from backend.database.imports import get_db, Users
from backend.settings import settings


class AuthMiddleware:
    async def __call__(self, request: Request, call_next):
        if not settings.auth.enabled:
            request.state.user = "dev_user"
            request.state.is_admin = True
            return await call_next(request)

        if (
            request.url.path.startswith("/static")
            or request.url.path.startswith("/auth/login")
            or request.url.path in ("/docs", "/openapi.json", "/redoc", "/health")
        ):
            return await call_next(request)

        token = request.cookies.get("access_token")
        if not token or not token.startswith("Bearer "):
            if request.url.path != "/auth/login":
                return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
            return await call_next(request)

        token = token.replace("Bearer ", "")
        try:
            payload = jwt.decode(token, settings.auth.jwt_secret_key, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username is None:
                raise ValueError("no sub claim")

            request.state.user = username
            db = next(get_db())
            user = db.query(Users).filter(Users.username == username).first()
            request.state.is_admin = user.is_admin if user else False
            return await call_next(request)

        except (JWTError, ValueError):
            response = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
            response.delete_cookie("access_token")
            return response
