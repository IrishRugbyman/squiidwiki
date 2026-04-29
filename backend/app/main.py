import uuid
from contextlib import asynccontextmanager

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings

logger = structlog.get_logger()

scheduler = AsyncIOScheduler()


async def refresh_stats() -> None:
    from app.core.database import AsyncSessionLocal
    from app.crud.stats import refresh_materialized_views

    async with AsyncSessionLocal() as session:
        await refresh_materialized_views(session)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.audit import attach_audit_listeners

    attach_audit_listeners()
    scheduler.add_job(refresh_stats, "interval", minutes=5)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="SquiidWiki API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    with structlog.contextvars.bound_contextvars(request_id=request_id):
        response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}


# Routers
from app.auth.router import router as auth_router  # noqa: E402
from app.routers.alliance import router as alliance_router  # noqa: E402
from app.routers.admin import router as admin_router  # noqa: E402
from app.routers.audit import router as audit_router  # noqa: E402
from app.routers.gang_set import router as gang_set_router  # noqa: E402
from app.routers.incident import router as incident_router  # noqa: E402
from app.routers.member import router as member_router  # noqa: E402
from app.routers.municipality import router as municipality_router  # noqa: E402
from app.routers.media import router as media_router  # noqa: E402
from app.routers.research_note import router as research_note_router  # noqa: E402
from app.routers.source import router as source_router  # noqa: E402
from app.routers.universe import router as universe_router  # noqa: E402

app.include_router(auth_router, prefix="/api/v1")
app.include_router(universe_router, prefix="/api/v1")
app.include_router(municipality_router, prefix="/api/v1")
app.include_router(source_router, prefix="/api/v1")
app.include_router(alliance_router, prefix="/api/v1")
app.include_router(gang_set_router, prefix="/api/v1")
app.include_router(member_router, prefix="/api/v1")
app.include_router(incident_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(research_note_router, prefix="/api/v1")
app.include_router(media_router, prefix="/api/v1")
