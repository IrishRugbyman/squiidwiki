from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.routes.sets import router as sets_router
from backend.routes.members import router as members_router
from backend.routes.alliances import router as alliances_router
from backend.routes.calendar import router as calendar_router
from backend.database import init_db

app = FastAPI()

# Initialize the database
init_db()

# Serve static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Include routes
app.include_router(sets_router, prefix="/sets", tags=["sets"])
app.include_router(members_router, prefix="/members", tags=["members"])
app.include_router(alliances_router, prefix="/alliances", tags=["alliances"])
app.include_router(calendar_router, prefix="/calendar", tags=["calendar"])