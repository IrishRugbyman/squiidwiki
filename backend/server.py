from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.sets.sets_router import router as sets_router
from backend.members.members_router import router as members_router
from backend.alliances.alliances_router import router as alliances_router
from backend.calendar.calendar_router import router as calendar_router
from backend.events.events_router import router as events_router
from backend.home.home_router import router as home_router

app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Include routes
app.include_router(home_router, tags=["home"])
app.include_router(sets_router, prefix="/sets", tags=["sets"])
app.include_router(members_router, prefix="/members", tags=["members"])
app.include_router(alliances_router, prefix="/alliances", tags=["alliances"])
app.include_router(calendar_router, prefix="/calendar", tags=["calendar"])
app.include_router(events_router, prefix="/events", tags=["events"])
