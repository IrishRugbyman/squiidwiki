from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from backend.database.database import get_db
from ..config.templates import templates  # Instead of local initialization


router = APIRouter()


@router.get("/{member_id}", response_class=HTMLResponse)
def member_details(request: Request, member_id: int):
    conn = get_db()
    cursor = conn.cursor()

    # Get member details
    cursor.execute('''
        SELECT id, name, status, 
        CASE WHEN status = 'locked_up' THEN strftime('%d/%m/%Y', release_date) ELSE NULL END as release_date,
        CASE WHEN status = 'dead' THEN strftime('%d-%m/%Y', date_of_death) ELSE NULL END as date_of_death,
        set_id 
        FROM members 
        WHERE id = ?
    ''', (member_id,))
    member = cursor.fetchone()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    set_id = member[5]
    cursor.execute("SELECT name FROM sets WHERE id = ?", (set_id,))
    set_row = cursor.fetchone()
    set_name = set_row[0] if set_row else "Unknown Set"

    # Get events
    cursor.execute("SELECT * FROM shootings WHERE shooter_id = ? OR victim_id = ?", (member_id, member_id))
    shootings = cursor.fetchall()
    cursor.execute("SELECT * FROM murders WHERE shooter_id = ? OR victim_id = ?", (member_id, member_id))
    murders = cursor.fetchall()
    cursor.execute("SELECT * FROM assists WHERE shooter_id = ? OR victim_id = ?", (member_id, member_id))
    assists = cursor.fetchall()

    # Collect all victim IDs
    victim_ids = set()
    for event in shootings + murders + assists:
        victim_ids.add(event[2])  # Assuming victim_id is at index 2

    # Get victim names and set IDs
    member_names = {}
    victim_set_ids = {}
    if victim_ids:
        placeholders = ','.join(['?'] * len(victim_ids))
        # Get member names
        cursor.execute(f"SELECT id, name FROM members WHERE id IN ({placeholders})", tuple(victim_ids))
        member_names = {row[0]: row[1] for row in cursor.fetchall()}

        # Get victim set IDs
        cursor.execute(f"SELECT id, set_id FROM members WHERE id IN ({placeholders})", tuple(victim_ids))
        victim_set_ids = {row[0]: row[1] for row in cursor.fetchall()}

    # Get set names for victim sets
    set_ids = list(victim_set_ids.values())
    sets_dict = {}
    if set_ids:
        placeholders = ','.join(['?'] * len(set_ids))
        cursor.execute(f"SELECT id, name FROM sets WHERE id IN ({placeholders})", tuple(set_ids))
        sets_dict = {row[0]: row[1] for row in cursor.fetchall()}

    # Build victim_sets mapping
    victim_sets = {}
    for victim_id, set_id in victim_set_ids.items():
        victim_sets[victim_id] = sets_dict.get(set_id, 'Unknown Set')

    return templates.TemplateResponse("members/member_details.html", {
        "request": request,
        "member": member,
        "set_name": set_name,
        "member_names": member_names,
        "victim_sets": victim_sets,
        "activities": {
            "shootings": shootings,
            "murders": murders,
            "assists": assists
        }
    })

@router.get("/add/{set_id}", response_class=HTMLResponse)
def add_member_form(request: Request, set_id: int):
    return templates.TemplateResponse("members/add_member.html", {"request": request, "set_id": set_id})


# In your add_member route
@router.post("/add/{set_id}", response_class=RedirectResponse)
def add_member(
    set_id: int,
    name: str = Form(...),
    status: str = Form(...),
    release_date: str = Form(None),
    date_of_death: str = Form(None)
):
    # Remove the status mapping since we're using direct values now
    # Convert empty strings to None for dates
    release_date = release_date if release_date else None
    date_of_death = date_of_death if date_of_death else None

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO members (name, status, release_date, date_of_death, set_id) VALUES (?, ?, ?, ?, ?)",
        (name, status, release_date, date_of_death, set_id)  # Use status directly
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
    # Validate status
    valid_statuses = {'alive', 'locked_up', 'dead', 'unknown'}
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status value")

    # Clear dates if not applicable
    if status != 'locked_up':
        release_date = None
    if status != 'dead':
        date_of_death = None
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