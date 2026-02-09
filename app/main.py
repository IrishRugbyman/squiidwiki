"""Main FastAPI application."""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from app.database import engine, Base
from app.config import settings
from app.routes import pages
from app.routes import api_members, api_sets, api_alliances, api_incidents, api_sources, api_graph
import os

# Create FastAPI app
app = FastAPI(title="SquiidWiki", description="Detroit Gang Research Database", version="1.0.0")

# Create static and templates directories if they don't exist
os.makedirs("app/static/css", exist_ok=True)
os.makedirs("app/static/js", exist_ok=True)
os.makedirs("app/templates", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(pages.router)
app.include_router(api_members.router)
app.include_router(api_sets.router)
app.include_router(api_alliances.router)
app.include_router(api_incidents.router)
app.include_router(api_sources.router)
app.include_router(api_graph.router)

# Create database tables
@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)


@app.get("/")
async def root():
    """Root redirect to dashboard."""
    return RedirectResponse(url="/dashboard")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
