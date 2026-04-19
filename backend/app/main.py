import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.audit import attach_audit_listeners
    attach_audit_listeners()
    yield


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

app.include_router(auth_router, prefix="/api/v1")
