from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from backend.database.database import get_db
from backend.config.templates import templates

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def read_alliances(request: Request):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, status FROM alliances")
    alliances = cursor.fetchall()

    # Convert tuples to dictionaries
    alliances = [
        {"id": row[0], "name": row[1], "description": row[2], "status": row[3]}
        for row in alliances
    ]

    return templates.TemplateResponse("alliances/index.html", {"request": request, "alliances": alliances})

@router.get("/{alliance_id}", response_class=HTMLResponse)
def read_alliance(request: Request, alliance_id: int):
    conn = get_db()
    cursor = conn.cursor()

    # Fetch alliance details
    cursor.execute("SELECT id, name, description, status FROM alliances WHERE id = ?", (alliance_id,))
    alliance = cursor.fetchone()
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")

    # Convert alliance tuple to dictionary
    alliance_dict = {
        "id": alliance[0],
        "name": alliance[1],
        "description": alliance[2],
        "status": alliance[3]
    }

    # Fetch member sets for this alliance
    cursor.execute("""
        SELECT sets.id, sets.name, sets.description, sets.type 
        FROM sets
        JOIN alliance_member_map ON sets.id = alliance_member_map.set_id
        WHERE alliance_member_map.alliance_id = ?
    """, (alliance_id,))
    member_sets = cursor.fetchall()

    # Convert member sets tuples to dictionaries
    member_sets = [
        {"id": row[0], "name": row[1], "description": row[2], "type": row[3]}
        for row in member_sets
    ]

    return templates.TemplateResponse(
        "alliances/alliance_details.html",
        {"request": request, "alliance": alliance_dict, "member_sets": member_sets}
    )

# Define the /add route
@router.get("/add", response_class=HTMLResponse)
def add_alliance_form(request: Request):
    return templates.TemplateResponse("alliances/add_alliance.html", {"request": request})

@router.post("/add", response_class=RedirectResponse)
def add_alliance(name: str = Form(...), description: str = Form(None), status: str = Form(...)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO alliances (name, description, status) VALUES (?, ?, ?)",
        (name, description, status)
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

    # Convert alliance tuple to dict
    alliance_dict = {
        "id": alliance[0],
        "name": alliance[1],
        "description": alliance[2],
        "status": alliance[3]
    }

    # Fetch available sets
    cursor.execute("""
        SELECT id, name, description, type 
        FROM sets 
        WHERE id NOT IN (
            SELECT set_id FROM alliance_member_map WHERE alliance_id = ?
        )
    """, (alliance_id,))
    available_sets = [
        {"id": row[0], "name": row[1], "description": row[2], "type": row[3]}
        for row in cursor.fetchall()
    ]

    return templates.TemplateResponse(
        "alliances/add_alliance_member.html",
        {
            "request": request,
            "alliance": alliance_dict,
            "available_sets": available_sets
        }
    )

# In your POST route
@router.post("/add_member/{alliance_id}")
def add_member(alliance_id: int, set_id: int = Form(...)):
    conn = get_db()
    cursor = conn.cursor()
    # Verify set exists
    cursor.execute("SELECT id FROM sets WHERE id = ?", (set_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Invalid set ID")
    cursor.execute(
        "INSERT INTO alliance_member_map (alliance_id, set_id) VALUES (?, ?)",
        (alliance_id, set_id)
    )
    conn.commit()
    return RedirectResponse(url=f"/alliances/{alliance_id}", status_code=303)



@router.get("/edit/{alliance_id}", response_class=HTMLResponse)
def edit_alliance_form(request: Request, alliance_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, status FROM alliances WHERE id = ?", (alliance_id,))
    alliance = cursor.fetchone()
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")

    # Convert tuple to dictionary
    alliance = {"id": alliance[0], "name": alliance[1], "description": alliance[2], "status": alliance[3]}

    return templates.TemplateResponse("alliances/edit_alliance.html", {"request": request, "alliance": alliance})

@router.post("/edit/{alliance_id}", response_class=RedirectResponse)
def edit_alliance(
    alliance_id: int,
    name: str = Form(...),
    description: str = Form(None),
    status: str = Form(...)
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE alliances SET name = ?, description = ?, status = ? WHERE id = ?",
        (name, description, status, alliance_id)
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