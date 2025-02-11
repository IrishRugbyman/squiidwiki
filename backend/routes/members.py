from datetime import datetime
import sqlite3
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

# Import your database helper and templates as before
from backend.database.database import get_db
from backend.config.templates import templates

# Import the Pydantic models.
# (Adjust the import paths as needed.)
from backend.database.models import (
    Member, MemberCreate,
    Shooting, Murder, Assist
)

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def list_members(request: Request):
    """
    List all members (joined with their set names), then sort them by member name.
    """
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT members.id, members.name, members.description, members.status,
                   members.release_date, members.release_date_approx,
                   members.death_date, members.death_date_approx,
                   members.set_id, members.alliance_id,
                   sets.name as set_name 
            FROM members 
            LEFT JOIN sets ON members.set_id = sets.id
        ''')
        rows = cursor.fetchall()
        # Create a list of dictionaries for easier templating.
        # (If you want to use a Pydantic model that includes the extra field, you could define a MemberDetail.)
        members = []
        for row in rows:
            member_dict = {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "status": row["status"],
                "release_date": row["release_date"],
                "release_date_approx": row["release_date_approx"],
                "death_date": row["death_date"],
                "death_date_approx": row["death_date_approx"],
                "set_id": row["set_id"],
                "alliance_id": row["alliance_id"],
                "set_name": row["set_name"]
            }
            members.append(member_dict)
        # Sort members by name (case–insensitive)
        members = sorted(members, key=lambda m: m["name"].lower())
        return templates.TemplateResponse("members/index.html", {
            "request": request,
            "members": members
        })
    finally:
        conn.close()

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
        # For a member who is "locked_up"
        release_date_precision: str = Form(None),  # 'exact', 'year', or 'life'
        release_date_exact: str = Form(None),
        release_date_year: str = Form(None),
        # For a member who is "dead"
        death_date_exact: str = Form(None),
        death_date_year: str = Form(None),
        alliance_id: str = Form(None)  # Pass empty string if none selected
):
    conn = get_db()
    cursor = conn.cursor()
    try:
        valid_statuses = {'alive', 'locked_up', 'dead', 'unknown'}
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail="Invalid status value")

        # Process the release date values (for "locked_up" status)
        release_date = None
        release_date_approx = None
        if status == 'locked_up':
            if release_date_precision == 'life':
                release_date_approx = "life"
            elif release_date_precision == 'year' and release_date_year:
                if not release_date_year.isdigit() or len(release_date_year) != 4:
                    raise HTTPException(400, "Invalid release year format (must be YYYY)")
                release_date_approx = release_date_year
            elif release_date_precision == 'exact' and release_date_exact:
                try:
                    parsed_date = datetime.strptime(release_date_exact, "%Y-%m-%d").date()
                    release_date = parsed_date
                    release_date_approx = parsed_date.strftime("%Y")
                except ValueError:
                    raise HTTPException(400, "Invalid release date format (must be YYYY-MM-DD)")
            else:
                release_date_approx = 'unknown'

        # Process the death date values (for "dead" status)
        death_date = None
        death_date_approx = None
        if status == "dead":
            if death_date_year:
                if not death_date_year.isdigit() or len(death_date_year) != 4:
                    raise HTTPException(400, "Invalid death year format (must be YYYY)")
                death_date_approx = death_date_year
            elif death_date_exact:
                try:
                    parsed_date = datetime.strptime(death_date_exact, "%Y-%m-%d").date()
                    death_date = parsed_date
                    death_date_approx = parsed_date.strftime("%Y")
                except ValueError:
                    raise HTTPException(400, "Invalid death date format (must be YYYY-MM-DD)")
            else:
                death_date_approx = 'unknown'

        # Convert alliance_id to an integer (if provided)
        alliance_id_int = int(alliance_id) if alliance_id and alliance_id.strip() else None

        # Now build a MemberCreate instance using our model for validation.
        new_member = MemberCreate(
            name=name,
            description=description,
            status=status,
            release_date=release_date,
            release_date_approx=release_date_approx,
            death_date=death_date,
            death_date_approx=death_date_approx,
            set_id=set_id,
            alliance_id=alliance_id_int
        )
        data = new_member.dict()
        # Insert into the database. (Make sure the order of columns matches your model.)
        cursor.execute(
            """
            INSERT INTO members 
            (name, description, status, release_date, release_date_approx, 
             death_date, death_date_approx, set_id, alliance_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["name"],
                data["description"],
                data["status"],
                data["release_date"],
                data["release_date_approx"],
                data["death_date"],
                data["death_date_approx"],
                data["set_id"],
                data["alliance_id"],
            )
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()
    return RedirectResponse(url=f"/sets/{set_id}", status_code=303)


@router.get("/edit/{member_id}", response_class=HTMLResponse)
def edit_member_form(request: Request, member_id: int):
    """
    Retrieve a member record from the database, convert it to a dict (or even a Pydantic model)
    and then render the edit form.
    """
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE id = ?", (member_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Member not found")
        # Map the tuple to a dict (you could also use a helper function here)
        member_data = {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "status": row["status"],
            "release_date": row["release_date"],
            "release_date_approx": row["release_date_approx"],
            "death_date": row["death_date"],
            "death_date_approx": row["death_date_approx"],
            "set_id": row["set_id"],
            "alliance_id": row["alliance_id"]
        }
        # Optionally, create a Pydantic model instance:
        member_obj = Member.parse_obj(member_data)
        return templates.TemplateResponse("members/edit_member.html", {
            "request": request,
            "member": member_obj.dict()
        })
    finally:
        conn.close()


@router.post("/edit/{member_id}", response_class=RedirectResponse)
def edit_member(
        member_id: int,
        name: str = Form(...),
        description: str = Form(None),
        status: str = Form(...),
        # For release date (when status is "locked_up")
        release_date_precision: str = Form(None),
        release_date_exact: str = Form(None),
        release_date_year: str = Form(None),
        # For death date (when status is "dead")
        death_precision: str = Form(None),
        death_date_exact: str = Form(None),
        death_date_year: str = Form(None),
        alliance_id: str = Form(None)
):
    conn = get_db()
    cursor = conn.cursor()
    try:
        valid_statuses = {'alive', 'locked_up', 'dead', 'unknown'}
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail="Invalid status value")

        # Process release date if needed.
        release_date = None
        release_date_approx = None
        if status == 'locked_up':
            if release_date_precision == 'year' and release_date_year:
                if not release_date_year.isdigit() or len(release_date_year) != 4:
                    raise HTTPException(400, "Invalid release year format (must be YYYY)")
                release_date_approx = release_date_year
            elif release_date_precision == 'exact' and release_date_exact:
                try:
                    parsed_date = datetime.strptime(release_date_exact, "%Y-%m-%d").date()
                    release_date = parsed_date
                    release_date_approx = parsed_date.strftime("%Y")
                except ValueError:
                    raise HTTPException(400, "Invalid release date format (must be YYYY-MM-DD)")
            elif release_date_precision == 'life':
                release_date_approx = "life"
            else:
                release_date_approx = 'unknown'

        # Process death date if needed.
        death_date = None
        death_date_approx = None
        if status == "dead":
            if death_precision == 'year' and death_date_year:
                if not death_date_year.isdigit() or len(death_date_year) != 4:
                    raise HTTPException(400, "Invalid death year format (must be YYYY)")
                death_date_approx = death_date_year
            elif death_precision == 'exact' and death_date_exact:
                try:
                    parsed_date = datetime.strptime(death_date_exact, "%Y-%m-%d").date()
                    death_date = parsed_date
                    death_date_approx = parsed_date.strftime("%Y")
                except ValueError:
                    raise HTTPException(400, "Invalid death date format (must be YYYY-MM-DD)")
            else:
                death_date_approx = 'unknown'

        alliance_id_int = int(alliance_id) if alliance_id and alliance_id.strip() else None

        # Build a MemberCreate instance (which here serves as our data validation schema for updates)
        updated_member = MemberCreate(
            name=name,
            description=description,
            status=status,
            release_date=release_date,
            release_date_approx=release_date_approx,
            death_date=death_date,
            death_date_approx=death_date_approx,
            set_id=0,  # not updating set_id here – it remains unchanged
            alliance_id=alliance_id_int
        )
        data = updated_member.dict()
        # Update the member in the database.
        cursor.execute(
            """
            UPDATE members SET 
            name = ?, description = ?, status = ?, 
            release_date = ?, release_date_approx = ?, 
            death_date = ?, death_date_approx = ?, alliance_id = ?
            WHERE id = ?
            """,
            (
                data["name"],
                data["description"],
                data["status"],
                data["release_date"],
                data["release_date_approx"],
                data["death_date"],
                data["death_date_approx"],
                data["alliance_id"],
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
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        return templates.TemplateResponse("members/delete_member.html", {
            "request": request,
            "member": {
                "id": member["id"],
                "name": member["name"],
                "set_id": member["set_id"]
            }
        })
    finally:
        conn.close()


@router.post("/delete/{member_id}", response_class=RedirectResponse)
def delete_member(member_id: int):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Get the member's set_id for redirection.
        cursor.execute("SELECT set_id FROM members WHERE id = ?", (member_id,))
        member = cursor.fetchone()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        set_id = member["set_id"]
        # Delete related incidents first.
        cursor.execute("DELETE FROM shootings WHERE shooter_id = ? OR victim_id = ?", (member_id, member_id))
        cursor.execute("DELETE FROM murders WHERE shooter_id = ? OR victim_id = ?", (member_id, member_id))
        cursor.execute("DELETE FROM assists WHERE shooter_id = ? OR victim_id = ?", (member_id, member_id))
        # Then delete the member.
        cursor.execute("DELETE FROM members WHERE id = ?", (member_id,))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
    redirect_url = f"/sets/{set_id}" if set_id is not None else "/"
    return RedirectResponse(url=redirect_url, status_code=303)


# Helper functions for events and member details

def get_events_as_dicts(cursor, query, params):
    cursor.execute(query, params)
    rows = cursor.fetchall()
    if not rows:
        return []
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def fetch_member_details(cursor, member_id: int) -> dict:
    cursor.execute('''
        SELECT id, name, description, status, 
               release_date, release_date_approx,
               death_date, death_date_approx,
               set_id, alliance_id
        FROM members 
        WHERE id = ?
    ''', (member_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Member not found")
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "status": row["status"],
        "release_date": row["release_date"],
        "release_date_approx": row["release_date_approx"],
        "death_date": row["death_date"],
        "death_date_approx": row["death_date_approx"],
        "set_id": row["set_id"],
        "alliance_id": row["alliance_id"]
    }


def fetch_set_and_alliance_names(cursor, member: dict):
    try:
        cursor.execute("SELECT name FROM sets WHERE id = ?", (member["set_id"],))
        set_row = cursor.fetchone()
        set_name = set_row["name"] if set_row else "Unknown Set"
    except Exception as e:
        set_name = "Unknown Set"
        print(f"Error fetching set name: {e}")

    try:
        cursor.execute("SELECT name FROM alliances WHERE id = ?", (member["alliance_id"],))
        alliance_row = cursor.fetchone()
        alliance_name = alliance_row["name"] if alliance_row else None
    except Exception as e:
        alliance_name = None
        print(f"Error fetching alliance name: {e}")

    return set_name, alliance_name


def fetch_activities(cursor, member_id: int):
    # Convert each event row into its Pydantic model for type safety.
    shootings_dicts = get_events_as_dicts(cursor, "SELECT * FROM shootings WHERE shooter_id = ?", (member_id,))
    murders_dicts = get_events_as_dicts(cursor, "SELECT * FROM murders WHERE shooter_id = ?", (member_id,))
    assists_dicts = get_events_as_dicts(cursor, "SELECT * FROM assists WHERE shooter_id = ?", (member_id,))

    # Using .parse_obj on each dictionary.
    shootings = [Shooting.parse_obj(item) for item in shootings_dicts]
    murders = [Murder.parse_obj(item) for item in murders_dicts]
    assists = [Assist.parse_obj(item) for item in assists_dicts]
    return shootings, murders, assists


def fetch_victim_details(cursor, victim_ids):
    member_names = {}
    victim_set_ids = {}
    if victim_ids:
        placeholders = ','.join(['?'] * len(victim_ids))
        cursor.execute(f"SELECT id, name, set_id FROM members WHERE id IN ({placeholders})", tuple(victim_ids))
        results = cursor.fetchall()
        member_names = {row["id"]: row["name"] for row in results}
        victim_set_ids = {row["id"]: row["set_id"] for row in results}

    set_ids = list(victim_set_ids.values())
    sets_dict = {}
    if set_ids:
        placeholders = ','.join(['?'] * len(set_ids))
        cursor.execute(f"SELECT id, name FROM sets WHERE id IN ({placeholders})", tuple(set_ids))
        sets_dict = {row["id"]: row["name"] for row in cursor.fetchall()}

    victim_sets = {vid: sets_dict.get(sid, 'Unknown Set') for vid, sid in victim_set_ids.items()}
    return member_names, victim_sets


@router.get("/{member_id}", response_class=HTMLResponse)
def member_details(request: Request, member_id: int):
    """
    Fetch the full details of a member (including incidents) and pass them to the detail template.
    """
    conn = get_db()
    cursor = conn.cursor()
    try:
        member_dict = fetch_member_details(cursor, member_id)
        # Convert to a Member model instance if desired.
        member_obj = Member.parse_obj(member_dict)
        set_name, alliance_name = fetch_set_and_alliance_names(cursor, member_dict)
        shootings, murders, assists = fetch_activities(cursor, member_id)
        victim_ids = {event.dict().get('victim_id') for event in shootings + murders + assists}
        member_names, victim_sets = fetch_victim_details(cursor, victim_ids)
    finally:
        conn.close()

    return templates.TemplateResponse("members/member_details.html", {
        "request": request,
        "member": member_obj.dict(),
        "set_name": set_name,
        "alliance_name": alliance_name,
        "member_names": member_names,
        "victim_sets": victim_sets,
        "activities": {
            "shootings": [s.dict() for s in shootings],
            "murders": [m.dict() for m in murders],
            "assists": [a.dict() for a in assists]
        },
        "victim_id": victim_ids
    })