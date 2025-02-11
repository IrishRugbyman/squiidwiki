from typing import List

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from backend.database.database import get_db
from backend.config.templates import templates
from backend.database.models import AllianceCreate, AllianceOption

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def read_alliances(request: Request):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, status FROM alliances")
    alliances = cursor.fetchall()

    return templates.TemplateResponse("alliances/index.html", {"request": request, "alliances": alliances})

# Define the /add route BEFORE the /{alliance_id} route
@router.get("/add", response_class=HTMLResponse)
def add_alliance_form(request: Request):
    return templates.TemplateResponse("alliances/add_alliance.html", {"request": request})

@router.post("/add", response_class=RedirectResponse)
def add_alliance(alliance: AllianceCreate = Depends()):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO alliances (name, description, status) VALUES (?, ?, ?)",
        (alliance.name, alliance.description, alliance.status)
    )
    conn.commit()
    return RedirectResponse(url="/alliances", status_code=303)

# Define the /add_member route BEFORE the /{alliance_id} route
@router.get("/add_member/{alliance_id}", response_class=HTMLResponse)
def add_member_form(request: Request, alliance_id: int):
    conn = get_db()
    cursor = conn.cursor()
    # Fetch alliance
    cursor.execute("SELECT id, name, description, status FROM alliances WHERE id = ?", (alliance_id,))
    alliance = cursor.fetchone()
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")

    # Fetch available sets
    cursor.execute("""
        SELECT id, name, description, type
        FROM sets
        WHERE id NOT IN (
            SELECT set_id FROM alliance_sets_map WHERE alliance_id = ?
        )
    """, (alliance_id,))
    available_sets = cursor.fetchall()

    return templates.TemplateResponse(
        "alliances/add_alliance_member.html",
        {
            "request": request,
            "alliance": alliance,
            "available_sets": available_sets
        }
    )

@router.post("/add_member/{alliance_id}")
def add_member(alliance_id: int, set_id: int = Form(...)):
    conn = get_db()
    cursor = conn.cursor()
    # Verify set exists
    cursor.execute("SELECT id FROM sets WHERE id = ?", (set_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Invalid set ID")
    cursor.execute(
        "INSERT INTO alliance_sets_map (alliance_id, set_id) VALUES (?, ?)",
        (alliance_id, set_id)
    )
    conn.commit()
    return RedirectResponse(url=f"/alliances/{alliance_id}", status_code=303)

@router.get("/options", response_model=List[AllianceOption])
def get_alliance_options():
    """
    Returns a list of active alliances.
    Each alliance is represented as a dictionary with keys 'id' and 'name'.
    """
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM alliances WHERE status = 'active'")
        alliances = cursor.fetchall()
        return [AllianceOption(**row) for row in alliances]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# General route for reading a single alliance
@router.get("/{alliance_id}", response_class=HTMLResponse)
def read_alliance(request: Request, alliance_id: int):
    conn = get_db()
    cursor = conn.cursor()
    # Fetch alliance details
    cursor.execute("SELECT id, name, description, status FROM alliances WHERE id = ?", (alliance_id,))
    alliance = cursor.fetchone()
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")

    # Fetch member sets for this alliance
    cursor.execute("""
        SELECT sets.id, sets.name, sets.description, sets.type
        FROM sets
        JOIN alliance_sets_map ON sets.id = alliance_sets_map.set_id
        WHERE alliance_sets_map.alliance_id = ?
    """, (alliance_id,))
    member_sets = cursor.fetchall()

    return templates.TemplateResponse(
        "alliances/alliance_details.html",
        {"request": request, "alliance": alliance, "member_sets": member_sets}
    )

@router.get("/edit/{alliance_id}", response_class=HTMLResponse)
def edit_alliance_form(request: Request, alliance_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, status FROM alliances WHERE id = ?", (alliance_id,))
    alliance = cursor.fetchone()
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")

    return templates.TemplateResponse("alliances/edit_alliance.html", {"request": request, "alliance": alliance})

@router.post("/edit/{alliance_id}", response_class=RedirectResponse)
def edit_alliance(
    alliance_id: int,
    alliance: AllianceCreate = Depends()
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE alliances SET name = ?, description = ?, status = ? WHERE id = ?",
        (alliance.name, alliance.description, alliance.status, alliance_id)
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