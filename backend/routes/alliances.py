from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from backend.database import get_db
from pathlib import Path
from fastapi.templating import Jinja2Templates

# Define the absolute path to the templates directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Points to the project root
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)


router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def read_alliances(request: Request):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alliances")
    alliances = cursor.fetchall()
    return templates.TemplateResponse("alliances/index.html", {"request": request, "alliances": alliances})

@router.get("/{alliance_id}", response_class=HTMLResponse)
def read_alliance(request: Request, alliance_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alliances WHERE id = ?", (alliance_id,))
    alliance = cursor.fetchone()
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")
    return templates.TemplateResponse("alliances/alliance_detail.html", {"request": request, "alliance": alliance})

@router.get("/add", response_class=HTMLResponse)
def add_alliance_form(request: Request):
    return templates.TemplateResponse("alliances/add_alliance.html", {"request": request})

@router.post("/add", response_class=RedirectResponse)
def add_alliance(name: str = Form(...), description: str = Form(None)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO alliances (name, description) VALUES (?, ?)",
        (name, description)
    )
    conn.commit()
    return RedirectResponse(url="/alliances", status_code=303)

@router.get("/edit/{alliance_id}", response_class=HTMLResponse)
def edit_alliance_form(request: Request, alliance_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alliances WHERE id = ?", (alliance_id,))
    alliance = cursor.fetchone()
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")
    return templates.TemplateResponse("alliances/edit_alliance.html", {"request": request, "alliance": alliance})

@router.post("/edit/{alliance_id}", response_class=RedirectResponse)
def edit_alliance(
    alliance_id: int,
    name: str = Form(...),
    description: str = Form(None)
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE alliances SET name = ?, description = ? WHERE id = ?",
        (name, description, alliance_id)
    )
    conn.commit()
    return RedirectResponse(url=f"/alliances/{alliance_id}", status_code=303)

@router.post("/delete/{alliance_id}", response_class=RedirectResponse)
def delete_alliance(alliance_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM alliances WHERE id = ?", (alliance_id,))
    conn.commit()
    return RedirectResponse(url="/alliances", status_code=303)