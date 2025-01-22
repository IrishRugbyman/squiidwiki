from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from backend.database.database import get_db
from pathlib import Path
from fastapi.templating import Jinja2Templates

# Define the absolute path to the templates directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Points to the project root
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)


router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def show_calendar(request: Request):
    conn = get_db()
    cursor = conn.cursor()

    # Fetch all members with release dates or dates of death
    cursor.execute("SELECT name, release_date, date_of_death FROM members")
    members = cursor.fetchall()

    # Prepare data for the calendar
    events = []
    for member in members:
        if member[1]:  # release_date
            events.append({
                "title": f"{member[0]} - Release",
                "date": member[1],
                "color": "green"  # Green for release dates
            })
        if member[2]:  # date_of_death
            events.append({
                "title": f"{member[0]} - Deceased",
                "date": member[2],
                "color": "red"  # Red for death dates
            })
            # Add death anniversaries
            death_year = int(member[2].split("-")[0])
            for year in range(death_year + 1, death_year + 11):  # Next 10 years
                events.append({
                    "title": f"{member[0]} - Death Anniversary",
                    "date": f"{year}-{member[2][5:]}",  # Same month and day
                    "color": "black"  # Black for death anniversaries
                })

    return templates.TemplateResponse("calendar.html", {"request": request, "events": events})