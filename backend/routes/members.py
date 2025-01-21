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

@router.get("/{member_id}", response_class=HTMLResponse)
def member_details(request: Request, member_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, status, strftime('%d/%m/%Y', release_date) as release_date, strftime('%d-%m-%Y', date_of_death) as date_of_death, set_id FROM members WHERE id = ?", (member_id,))
    member = cursor.fetchone()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return templates.TemplateResponse("members/member_details.html", {"request": request, "member": member})

@router.get("/add/{set_id}", response_class=HTMLResponse)
def add_member_form(request: Request, set_id: int):
    return templates.TemplateResponse("members/add_member.html", {"request": request, "set_id": set_id})

@router.post("/add/{set_id}", response_class=RedirectResponse)
def add_member(
    set_id: int,
    name: str = Form(...),
    status: str = Form(...),
    release_date: str = Form(None),
    date_of_death: str = Form(None)
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO members (name, status, release_date, date_of_death, set_id) VALUES (?, ?, ?, ?, ?)",
        (name, status, release_date, date_of_death, set_id)
    )
    conn.commit()
    return RedirectResponse(url=f"/sets/{set_id}", status_code=303)

@router.get("/edit/{member_id}", response_class=HTMLResponse)
def edit_member_form(request: Request, member_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM members WHERE id = ?", (member_id,))
    member = cursor.fetchone()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return templates.TemplateResponse("members/edit_member.html", {"request": request, "member": member})

@router.post("/edit/{member_id}", response_class=RedirectResponse)
def edit_member(
    member_id: int,
    name: str = Form(...),
    status: str = Form(...),
    release_date: str = Form(None),
    date_of_death: str = Form(None)
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE members SET name = ?, status = ?, release_date = ?, date_of_death = ? WHERE id = ?",
        (name, status, release_date, date_of_death, member_id)
    )
    conn.commit()
    return RedirectResponse(url=f"/members/{member_id}", status_code=303)

@router.post("/delete/{member_id}", response_class=RedirectResponse)
def delete_member(member_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT set_id FROM members WHERE id = ?", (member_id,))
    set_id = cursor.fetchone()[0]
    cursor.execute("DELETE FROM members WHERE id = ?", (member_id,))
    conn.commit()
    return RedirectResponse(url=f"/sets/{set_id}", status_code=303)