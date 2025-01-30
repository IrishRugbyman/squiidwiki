from datetime import datetime
import sqlite3
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from backend.database.database import get_db
from backend.config.templates import templates


router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def list_members(request: Request):
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Get all members with their set names
        cursor.execute('''
            SELECT members.*, sets.name as set_name 
            FROM members 
            LEFT JOIN sets ON members.set_id = sets.id
        ''')
        members = cursor.fetchall()

        return templates.TemplateResponse("members/index.html", {
            "request": request,
            "members": sorted(members, key=lambda x: x[1].lower())  # Initial sort by name
        })
    finally:
        conn.close()


@router.get("/{member_id}", response_class=HTMLResponse)
def member_details(request: Request, member_id: int):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Fetch member details (updated schema)
        cursor.execute('''
            SELECT 
                id, name, description, status, 
                release_date, release_date_approx,
                date_of_death, death_date_approx,
                set_id 
            FROM members 
            WHERE id = ?
        ''', (member_id,))
        member_row = cursor.fetchone()
        if not member_row:
            raise HTTPException(status_code=404, detail="Member not found")

        # Convert tuple to dictionary with correct indexes
        member = {
            "id": member_row[0],
            "name": member_row[1],
            "description": member_row[2],
            "status": member_row[3],
            "release_date": member_row[4],  # Exact release date
            "release_date_approx": member_row[5],  # Approximate release date
            "date_of_death": member_row[6],  # Exact date of death
            "death_date_approx": member_row[7],  # Approximate date of death
            "set_id": member_row[8]
        }

        # Get set name
        cursor.execute("SELECT name FROM sets WHERE id = ?", (member["set_id"],))
        set_row = cursor.fetchone()
        set_name = set_row[0] if set_row else "Unknown Set"

        # Fetch events (shootings, murders, assists)
        cursor.execute("SELECT * FROM shootings WHERE shooter_id = ?", (member_id,))
        shootings = cursor.fetchall()
        cursor.execute("SELECT * FROM murders WHERE shooter_id = ?", (member_id,))
        murders = cursor.fetchall()
        cursor.execute("SELECT * FROM assists WHERE shooter_id = ?", (member_id,))
        assists = cursor.fetchall()

        # Collect victim details
        victim_ids = {event[2] for event in shootings + murders + assists}
        member_names = {}
        victim_set_ids = {}
        if victim_ids:
            placeholders = ','.join(['?'] * len(victim_ids))
            cursor.execute(f"SELECT id, name, set_id FROM members WHERE id IN ({placeholders})", tuple(victim_ids))
            results = cursor.fetchall()
            member_names = {row[0]: row[1] for row in results}
            victim_set_ids = {row[0]: row[2] for row in results}

        set_ids = list(victim_set_ids.values())
        sets_dict = {}
        if set_ids:
            placeholders = ','.join(['?'] * len(set_ids))
            cursor.execute(f"SELECT id, name FROM sets WHERE id IN ({placeholders})", tuple(set_ids))
            sets_dict = {row[0]: row[1] for row in cursor.fetchall()}

        victim_sets = {vid: sets_dict.get(sid, 'Unknown Set') for vid, sid in victim_set_ids.items()}

    finally:
        conn.close()

    return templates.TemplateResponse("members/member_details.html", {
        "request": request,
        "member": member,
        "set_name": set_name,
        "member_names": member_names,
        "victim_sets": victim_sets,
        "victim_set_ids": victim_set_ids,
        "activities": {
            "shootings": shootings,
            "murders": murders,
            "assists": assists
        }
    })

@router.get("/add/{set_id}", response_class=HTMLResponse)
def add_member_form(request: Request, set_id: int):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sets WHERE id = ?", (set_id,))
        set_data = cursor.fetchone()
        if not set_data:
            raise HTTPException(status_code=404, detail="Set not found")

        return templates.TemplateResponse("members/add_member.html", {
            "request": request,
            "set_id": set_id,
            "set_name": set_data[0],
            "current_year": datetime.now().year
        })
    finally:
        conn.close()


@router.post("/add/{set_id}", response_class=RedirectResponse)
def add_member(
        set_id: int,
        name: str = Form(...),
        description: str = Form(None),
        status: str = Form(...),
        release_date_exact: str = Form(None),
        release_date_year: str = Form(None),
        death_date_exact: str = Form(None),
        death_date_year: str = Form(None)
):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Validate status
        valid_statuses = {'alive', 'locked_up', 'dead', 'unknown'}
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail="Invalid status value")

        # Process release date
        release_date = None
        release_date_approx = None
        if status == 'locked_up':
            if release_date_year:
                if not release_date_year.isdigit() or len(release_date_year) != 4:
                    raise HTTPException(400, "Invalid release year format (must be YYYY)")
                release_date_approx = f"{release_date_year}"
            elif release_date_exact:
                try:
                    datetime.strptime(release_date_exact, "%Y-%m-%d")
                    release_date = release_date_exact
                except ValueError:
                    raise HTTPException(400, "Invalid release date format (must be YYYY-MM-DD)")
            else:
                release_date_approx = 'unknown'

        # Process death date
        date_of_death = None
        death_date_approx = None
        if status == "dead":
            if death_date_year:
                if not death_date_year.isdigit() or len(death_date_year) != 4:
                    raise HTTPException(400, "Invalid death year format (must be YYYY)")
                death_date_approx = f"{death_date_year}"
            elif death_date_exact:
                try:
                    datetime.strptime(death_date_exact, "%Y-%m-%d")
                    date_of_death = death_date_exact
                except ValueError:
                    raise HTTPException(400, "Invalid death date format (must be YYYY-MM-DD)")
            else:
                death_date_approx = 'unknown'

        # Insert member into the database
        cursor.execute(
            """
            INSERT INTO members 
            (name, description, status, release_date, release_date_approx, 
             date_of_death, death_date_approx, set_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name, description, status, release_date, release_date_approx,
                date_of_death, death_date_approx, set_id
            )
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()
    return RedirectResponse(url=f"/sets/{set_id}", status_code=303)

# Add proper edit member form handler
@router.get("/edit/{member_id}", response_class=HTMLResponse)
def edit_member_form(request: Request, member_id: int):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE id = ?", (member_id,))
        member = cursor.fetchone()
        print(f"DEBUG: Member with ID {member_id} -> {member}")  # Debugging line
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        # Convert tuple to dict for easier handling
        member_data = {
            "id": member[0],
            "name": member[1],
            "description": member[2],
            "status": member[3],
            "release_date": member[4],
            "date_of_death": member[5],
            "set_id": member[6]
        }
        return templates.TemplateResponse("members/edit_member.html", {
            "request": request,
            "member": member_data
        })
    finally:
        conn.close()


@router.post("/edit/{member_id}", response_class=RedirectResponse)
def edit_member(
        member_id: int,
        name: str = Form(...),
        description: str = Form(None),
        status: str = Form(...),
        release_date_exact: str = Form(None),
        release_date_year: str = Form(None),
        death_date_exact: str = Form(None),
        death_date_year: str = Form(None)
):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Validate status
        valid_statuses = {'alive', 'locked_up', 'dead', 'unknown'}
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail="Invalid status value")

        # Process release date
        release_date = None
        release_date_approx = None
        if status == 'locked_up':
            if release_date_year:
                if not release_date_year.isdigit() or len(release_date_year) != 4:
                    raise HTTPException(400, "Invalid release year format (must be YYYY)")
                release_date_approx = f"{release_date_year}"
            elif release_date_exact:
                try:
                    datetime.strptime(release_date_exact, "%Y-%m-%d")
                    release_date = release_date_exact
                except ValueError:
                    raise HTTPException(400, "Invalid release date format (must be YYYY-MM-DD)")
            else:
                release_date_approx = 'unknown'

        # Process death date
        date_of_death = None
        death_date_approx = None
        if status == "dead":
            if death_date_year:
                if not death_date_year.isdigit() or len(death_date_year) != 4:
                    raise HTTPException(400, "Invalid death year format (must be YYYY)")
                death_date_approx = f"{death_date_year}"
            elif death_date_exact:
                try:
                    datetime.strptime(death_date_exact, "%Y-%m-%d")
                    date_of_death = death_date_exact
                except ValueError:
                    raise HTTPException(400, "Invalid death date format (must be YYYY-MM-DD)")
            else:
                death_date_approx = 'unknown'

        # Update the member
        cursor.execute(
            """
            UPDATE members SET 
            name = ?, description = ?, status = ?, 
            release_date = ?, release_date_approx = ?, 
            date_of_death = ?, death_date_approx = ? 
            WHERE id = ?
            """,
            (
                name, description, status,
                release_date, release_date_approx,
                date_of_death, death_date_approx,
                member_id
            )
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
    return RedirectResponse(url=f"/members/{member_id}", status_code=303)

@router.get("/delete/{member_id}", response_class=HTMLResponse)
def delete_member_confirmation(request: Request, member_id: int):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, set_id FROM members WHERE id = ?", (member_id,))
        member = cursor.fetchone()
        print(f"DEBUG: Member with ID {member_id} -> {member}")  # Debugging line
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        return templates.TemplateResponse("members/delete_member.html", {
            "request": request,
            "member": {
                "id": member[0],
                "name": member[1],
                "set_id": member[2]
            }
        })
    finally:
        conn.close()


@router.post("/delete/{member_id}", response_class=RedirectResponse)
def delete_member(member_id: int):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Get member's set_id for redirect and verify existence
        cursor.execute("SELECT set_id FROM members WHERE id = ?", (member_id,))
        member = cursor.fetchone()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        set_id = member[0]

        # Delete related incidents
        cursor.execute("DELETE FROM shootings WHERE shooter_id = ? OR victim_id = ?", (member_id, member_id))
        cursor.execute("DELETE FROM murders WHERE shooter_id = ? OR victim_id = ?", (member_id, member_id))
        cursor.execute("DELETE FROM assists WHERE shooter_id = ? OR victim_id = ?", (member_id, member_id))

        # Delete the member
        cursor.execute("DELETE FROM members WHERE id = ?", (member_id,))
        conn.commit()

    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

    # Determine redirect URL
    redirect_url = f"/sets/{set_id}" if set_id is not None else "/"
    return RedirectResponse(url=redirect_url, status_code=303)