import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import backend.database.models  # noqa: F401 — register all models with metadata
from backend.database.db_init import init_db
from backend.auth.auth_middleware import AuthMiddleware
from backend.settings import settings

from backend.sets.routes import router as sets_router
from backend.members.routes import router as members_router
from backend.alliances.alliances_router import router as alliances_router
from backend.calendar.calendar_router import router as calendar_router
from backend.events.events_router import router as events_router
from backend.home.home_router import router as home_router
from backend.auth.auth_router import router as auth_router

logger = logging.getLogger("app")
logging.basicConfig(
    level=logging.DEBUG if settings.is_development() else logging.INFO,
    format=settings.logging.format,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting SquiidWiki in {settings.env} environment")
    if init_db():
        logger.info("Database initialization completed successfully")
    else:
        logger.warning("Database initialization completed with warnings")
    yield
    logger.info("Shutting down SquiidWiki")


app = FastAPI(
    title="SquiidWiki",
    description="API for SquiidWiki application",
    version="2.0.0",
    debug=settings.is_development(),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(AuthMiddleware())

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(home_router, tags=["home"])
app.include_router(sets_router, prefix="/sets", tags=["sets"])
app.include_router(members_router, prefix="/members", tags=["members"])
app.include_router(alliances_router, prefix="/alliances", tags=["alliances"])
app.include_router(calendar_router, prefix="/calendar", tags=["calendar"])
app.include_router(events_router, prefix="/events", tags=["events"])

app_api = FastAPI(title="SquiidWiki API")
app.mount("/api", app_api)

app_api.include_router(auth_router, prefix="/auth", tags=["auth"])
app_api.include_router(home_router, tags=["home"])
app_api.include_router(sets_router, prefix="/sets", tags=["sets"])
app_api.include_router(members_router, prefix="/members", tags=["members"])
app_api.include_router(alliances_router, prefix="/alliances", tags=["alliances"])
app_api.include_router(calendar_router, prefix="/calendar", tags=["calendar"])
app_api.include_router(events_router, prefix="/events", tags=["events"])


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "environment": settings.env}
