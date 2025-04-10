from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.auth.auth_utils import ALGORITHM
from backend.config.config import settings
from backend.database.db_alchemy_models import get_db, Users

class AuthMiddleware:
    async def __call__(self, request: Request, call_next):
        # AUTH BYPASS FOR DEVELOPMENT - only available in development mode
        if settings.AUTH_BYPASS_ENABLED:
            bypass_auth = request.cookies.get("auth_bypass") == settings.AUTH_BYPASS_CODE
            if bypass_auth:
                # Set admin privileges for bypass mode
                request.state.user = "dev_admin"
                request.state.is_admin = True
                return await call_next(request)
            
        # Exclude login page and static files from authentication
        if (
            request.url.path.startswith("/static") or
            request.url.path.startswith("/auth/login") or
            request.url.path == "/docs" or
            request.url.path == "/openapi.json" or
            request.url.path == "/redoc"
        ):
            return await call_next(request)

        # Get the token from the cookie
        token = request.cookies.get("access_token")
        if not token or not token.startswith("Bearer "):
            # If no token, redirect to login page
            if request.url.path != "/auth/login":
                return RedirectResponse(
                    url="/auth/login",
                    status_code=status.HTTP_303_SEE_OTHER
                )
            return await call_next(request)

        # Extract the actual token
        token = token.replace("Bearer ", "")
        
        try:
            # Decode the token
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username is None:
                raise HTTPException(status_code=401, detail="Invalid authentication credentials")
                
            # Set the current user in request state
            request.state.user = username
            
            # Get the user from database to check admin status
            db = next(get_db())
            user = db.query(Users).filter(Users.username == username).first()
            if user:
                request.state.is_admin = user.is_admin
            else:
                request.state.is_admin = False
            
            # Continue with the request
            return await call_next(request)
            
        except JWTError:
            # If token is invalid, redirect to login
            response = RedirectResponse(
                url="/auth/login",
                status_code=status.HTTP_303_SEE_OTHER
            )
            response.delete_cookie("access_token")
            return response 