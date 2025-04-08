from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.requests import Request
import logging

from backend.sets.sets_router import router as sets_router
from backend.members.members_router import router as members_router
from backend.alliances.alliances_router import router as alliances_router
from backend.calendar.calendar_router import router as calendar_router
from backend.events.events_router import router as events_router
from backend.home.home_router import router as home_router
from backend.auth.auth_router import router as auth_router
from backend.auth.auth_middleware import AuthMiddleware
from backend.errors.error_handler import register_exception_handlers
from backend.config.config import settings
from backend.config.templates import templates

# Configure logging
logger = logging.getLogger("app")
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create the FastAPI app
app = FastAPI(
    title="SquiidWiki",
    description="API for SquiidWiki application",
    version="1.0.0",
    debug=settings.DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
app.middleware("http")(AuthMiddleware())

# Register error handlers
register_exception_handlers(app)

# Serve static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Include routes
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(home_router, tags=["home"])
app.include_router(sets_router, prefix="/sets", tags=["sets"])
app.include_router(members_router, prefix="/members", tags=["members"])
app.include_router(alliances_router, prefix="/alliances", tags=["alliances"])
app.include_router(calendar_router, prefix="/calendar", tags=["calendar"])
app.include_router(events_router, prefix="/events", tags=["events"])

# API routes for JSON endpoints
app_api = FastAPI(title="SquiidWiki API")
app.mount("/api", app_api)
app_api.include_router(sets_router, prefix="/sets", tags=["sets"])
app_api.include_router(members_router, prefix="/members", tags=["members"])
app_api.include_router(alliances_router, prefix="/alliances", tags=["alliances"])
app_api.include_router(calendar_router, prefix="/calendar", tags=["calendar"])
app_api.include_router(events_router, prefix="/events", tags=["events"])

# Healthcheck endpoint
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "environment": settings.APP_ENV}

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting SquiidWiki in {settings.APP_ENV} environment")
    logger.info(f"Using database: {settings.DB_PATH}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down SquiidWiki")
