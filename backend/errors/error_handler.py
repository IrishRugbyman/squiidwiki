from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError
import logging
from typing import Dict, Any, Optional, Union

from backend.config.templates import templates
from backend.config.config import settings

# Set up logging
logger = logging.getLogger(__name__)
if settings.DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


class AppError(Exception):
    """Base application error class."""
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppError):
    """Resource not found error."""
    def __init__(self, message: str = "Resource not found", **kwargs):
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            **kwargs
        )


class ValidationFailedError(AppError):
    """Validation error for API requests."""
    def __init__(self, message: str = "Validation failed", **kwargs):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            **kwargs
        )


class DatabaseError(AppError):
    """Database-related error."""
    def __init__(self, message: str = "Database error occurred", **kwargs):
        super().__init__(
            message=message,
            status_code=500,
            error_code="DATABASE_ERROR",
            **kwargs
        )


class AuthenticationError(AppError):
    """Authentication-related error."""
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            **kwargs
        )


class AuthorizationError(AppError):
    """Authorization-related error."""
    def __init__(self, message: str = "Not authorized to perform this action", **kwargs):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
            **kwargs
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app."""
    
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> Union[JSONResponse, HTMLResponse]:
        """Handle all application errors."""
        # Log the error
        logger.error(f"AppError: {exc.message}", exc_info=exc if settings.DEBUG else False)
        
        # Create the error response
        content = {
            "error": True,
            "code": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
        
        # For API endpoints, return JSON response
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=exc.status_code,
                content=jsonable_encoder(content)
            )
        
        # For HTML endpoints, return a rendered error page
        return templates.TemplateResponse(
            "errors/error.html",
            {
                "request": request,
                "status_code": exc.status_code,
                "error_message": exc.message,
                "error_details": exc.details,
                "error_code": exc.error_code,
            },
            status_code=exc.status_code
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> Union[JSONResponse, HTMLResponse]:
        """Handle FastAPI's validation errors."""
        # Convert FastAPI validation error to our format
        app_error = ValidationFailedError(
            message="Request validation failed",
            details={"errors": exc.errors()}
        )
        return await app_error_handler(request, app_error)
    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_error_handler(request: Request, exc: ValidationError) -> Union[JSONResponse, HTMLResponse]:
        """Handle Pydantic validation errors."""
        # Convert Pydantic validation error to our format
        app_error = ValidationFailedError(
            message="Data validation failed",
            details={"errors": exc.errors()}
        )
        return await app_error_handler(request, app_error)
    
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> Union[JSONResponse, HTMLResponse]:
        """Handle SQLAlchemy errors."""
        # Convert SQLAlchemy error to our format
        app_error = DatabaseError(
            message=str(exc),
            details={"error_type": exc.__class__.__name__}
        )
        return await app_error_handler(request, app_error)
    
    @app.exception_handler(404)
    async def not_found_error_handler(request: Request, exc: Any) -> HTMLResponse:
        """Handle 404 errors."""
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request},
            status_code=404
        )
    
    @app.exception_handler(500)
    async def server_error_handler(request: Request, exc: Any) -> HTMLResponse:
        """Handle 500 errors."""
        # Log the error
        logger.error(f"Internal server error: {str(exc)}", exc_info=exc if settings.DEBUG else False)
        
        return templates.TemplateResponse(
            "errors/500.html",
            {"request": request, "debug": settings.DEBUG},
            status_code=500
        )


# Helper functions for raising errors in controllers
def raise_not_found(resource_type: str, resource_id: Any) -> None:
    """Raise a not found error with details about the resource."""
    raise NotFoundError(
        message=f"{resource_type} with ID {resource_id} not found",
        details={"resource_type": resource_type, "resource_id": resource_id}
    )

def raise_validation_error(message: str, errors: Dict[str, Any]) -> None:
    """Raise a validation error with details about the validation failures."""
    raise ValidationFailedError(
        message=message,
        details={"errors": errors}
    )

def raise_auth_error(message: str = "Authentication required") -> None:
    """Raise an authentication error."""
    raise AuthenticationError(message=message)

def raise_permission_error(message: str = "Insufficient permissions") -> None:
    """Raise a permission error."""
    raise AuthorizationError(message=message) 