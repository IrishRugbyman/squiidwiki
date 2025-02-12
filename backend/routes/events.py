import sqlite3
from typing import Optional

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from backend.database.database import get_db
from datetime import datetime
from backend.config.templates import templates


router = APIRouter()

VALID_EVENT_TYPES = {"shootings": "shootings", "murders": "murders", "assists": "assists"}


def validate_member(member_id: int, event_date: Optional[str] = None, check_alive: bool = False):
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT id, status, death_date FROM members WHERE id = ?"
    cursor.execute(query, (member_id,))
    member = cursor.fetchone()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if check_alive:
        if member['status'] == 'dead':
            if event_date:
                # Parse dates for comparison
                try:
                    event_dt = datetime.strptime(event_date, "%Y-%m-%d").date()
                    death_dt = datetime.strptime(member['death_date'], "%Y-%m-%d").date() if member['death_date'] else None
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid date format, use YYYY-MM-DD")

                if death_dt and event_dt > death_dt:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Member was dead on {member['death_date']}, cannot participate in event on {event_date}"
                    )
            else:
                raise HTTPException(status_code=400, detail="Member is dead")

    return member_id

def normalize_event_type(event_type: str) -> str:
    return event_type.strip().lower()

def get_events_by_type(member_id: int, event_type: str, db: sqlite3.Connection):
    event_type = normalize_event_type(event_type)
    if event_type not in VALID_EVENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid event type")
    table_name = VALID_EVENT_TYPES[event_type]
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM {table_name} WHERE shooter_id = ? OR victim_id = ? ORDER BY date DESC", (member_id, member_id))
    return cursor.fetchall()

def get_victim_info(events: list):
    """Helper function to get victim information for events"""
    conn = get_db()
    cursor = conn.cursor()

    victim_ids = {event['victim_id'] for event in events}  # victim_id is at index 2
    member_names = {}
    victim_set_ids = {}

    if victim_ids:
        placeholders = ','.join(['?'] * len(victim_ids))
        cursor.execute(f"SELECT id, name, set_id FROM members WHERE id IN ({placeholders})", tuple(victim_ids))
        results = cursor.fetchall()
        member_names = {row['id']: row['name'] for row in results}
        victim_set_ids = {row['id']: row['set_id'] for row in results}

    set_ids = list(victim_set_ids.values())
    sets_dict = {}
    if set_ids:
        placeholders = ','.join(['?'] * len(set_ids))
        cursor.execute(f"SELECT id, name FROM sets WHERE id IN ({placeholders})", tuple(set_ids))
        sets_dict = {row['id']: row['name'] for row in cursor.fetchall()}

    victim_sets = {vid: sets_dict.get(sid, 'Unknown Set') for vid, sid in victim_set_ids.items()}

    return {
        "member_names": member_names,
        "victim_sets": victim_sets,
        "victim_set_ids": victim_set_ids
    }

@router.get("/shootings/{member_id}", response_class=HTMLResponse)
async def get_shootings(request: Request, member_id: int):
    validate_member(member_id)
    conn = get_db()
    shootings = get_events_by_type(member_id, "shootings", conn)
    victim_info = get_victim_info(shootings)

    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM members WHERE id != ?", (member_id,))
    all_members = cursor.fetchall()

    return templates.TemplateResponse("events/add_event.html", {
        "request": request,
        "events": shootings,
        "event_type": "shooting",
        "member_id": member_id,
        "all_members": all_members,
        **victim_info
    })

@router.get("/murders/{member_id}", response_class=HTMLResponse)
async def get_murders(request: Request, member_id: int):
    validate_member(member_id)
    conn = get_db()
    murders = get_events_by_type(member_id, "murders", conn)
    victim_info = get_victim_info(murders)

    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM members WHERE id != ?", (member_id,))
    all_members = cursor.fetchall()

    return templates.TemplateResponse("events/add_event.html", {
        "request": request,
        "events": murders,
        "event_type": "murder",
        "member_id": member_id,
        "all_members": all_members,
        **victim_info
    })

@router.get("/assists/{member_id}", response_class=HTMLResponse)
async def get_assists(request: Request, member_id: int):
    validate_member(member_id)
    conn = get_db()
    assists = get_events_by_type(member_id, "assists", conn)
    victim_info = get_victim_info(assists)

    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM members WHERE id != ?", (member_id,))
    all_members = cursor.fetchall()

    return templates.TemplateResponse("events/add_event.html", {
        "request": request,
        "events": assists,
        "event_type": "assist",
        "member_id": member_id,
        "all_members": all_members,
        **victim_info
    })

@router.get("/add/{event_type}/{member_id}")
async def show_add_event_form(
        request: Request,
        member_id: int,
        event_type: str,
):
    """
    Shows a form for adding an event (e.g. shooting, murder, assist) for a given member.
    """
    conn = get_db()
    try:
        event_type = normalize_event_type(event_type)
        cursor = conn.cursor()

        if event_type == "assists":
            # For assists, only show dead members
            cursor.execute("SELECT id, name, death_date, death_date_approx FROM members WHERE id != ? AND status = 'dead'", (member_id,))
            template_name = "events/add_assist.html"
        elif event_type == "murders":
            # For murders, show all members except those who already have a murder record
            cursor.execute("""
                SELECT m.id, m.name, m.death_date, m.death_date_approx
                FROM members m
                LEFT JOIN murders mu ON m.id = mu.victim_id
                WHERE m.id != ? AND mu.id IS NULL
            """, (member_id,))
            template_name = "events/add_murder.html"
        else:
            # For shootings, show all members
            cursor.execute("SELECT id, name, death_date FROM members WHERE id != ?", (member_id,))
            template_name = "events/add_shooting.html"

        all_members = cursor.fetchall()
        return templates.TemplateResponse(template_name, {
            "request": request,
            "event_type": event_type,
            "member_id": member_id,
            "all_members": all_members
        })
    finally:
        conn.close()



async def add_shooting(
    request: Request,
    member_id: int,
    victim_id: int,
    date_precision: str,
    date_exact: Optional[str],
    date_year: Optional[str]
):
    # Handle date based on precision
    event_date, date_approx = parse_date(date_precision, date_exact, date_year)

    # Get database connection
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO shootings (shooter_id, victim_id, date, date_approx) VALUES (?, ?, ?, ?)",
            (member_id, victim_id, event_date, date_approx)
        )
        conn.commit()
        return RedirectResponse(url=f"/members/{member_id}", status_code=303)

    except HTTPException as e:
        return handle_error(request, member_id, "shootings", victim_id, date_precision, date_exact, date_year, e)

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

async def add_murder(
    request: Request,
    member_id: int,
    victim_id: int,
    date_precision: str = 'keep',
    date_exact: Optional[str] = None,
    date_year: Optional[str] = None
):
    if not date_precision:
        date_precision = 'keep'

    # Get database connection
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Check if victim already has a murder record
        cursor.execute("SELECT id FROM murders WHERE victim_id = ?", (victim_id,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Victim already has a murder record")

        # Fetch the victim's current status and death date info
        cursor.execute(
            "SELECT status, death_date, death_date_approx FROM members WHERE id = ?",
            (victim_id,)
        )
        result = cursor.fetchone()
        if result:
            victim_status, victim_dod, victim_dod_approx = result
        else:
            raise HTTPException(status_code=404, detail="Victim not found")

        # Initialize variables for the murder record
        event_date = None   # full date string ("YYYY-MM-DD") or None
        date_approx = None  # usually the year or a string like "unknown"

        if victim_status == "dead":
            # NEW: If the user chooses "keep", we want to re-use the victim's already recorded death date.
            if date_precision == "keep":
                if victim_dod:
                    # The precise date is in the expected column.
                    event_date = victim_dod
                    date_approx = victim_dod[:4]
                elif victim_dod_approx:
                    # Check if victim_dod_approx looks like a full date (YYYY-MM-DD).
                    if len(victim_dod_approx) == 10 and "-" in victim_dod_approx:
                        event_date = victim_dod_approx
                        date_approx = victim_dod_approx[:4]
                    elif victim_dod_approx != "unknown":
                        # Otherwise, treat it as only an approximate value.
                        event_date = None
                        date_approx = victim_dod_approx
                    else:
                        raise HTTPException(status_code=400, detail="No death date available to keep")
                else:
                    raise HTTPException(status_code=400, detail="No death date available to keep")
            else:
                # The user is trying to provide a new murder date.
                if victim_dod:
                    # Victim has a precise death date.
                    existing_dod = datetime.strptime(victim_dod, "%Y-%m-%d").date()
                    if date_precision == "exact":
                        if date_exact:
                            dt = datetime.strptime(date_exact, "%Y-%m-%d").date()
                            if dt > existing_dod:
                                raise HTTPException(
                                    status_code=400,
                                    detail=f"Murder date {dt.strftime('%Y-%m-%d')} is after victim's date of death {victim_dod}"
                                )
                            event_date = dt.strftime("%Y-%m-%d")
                            date_approx = dt.strftime("%Y")
                        else:
                            raise HTTPException(status_code=400, detail="Exact date is required")
                    elif date_precision == "year":
                        if date_year:
                            murder_year = int(date_year)
                            if murder_year > existing_dod.year:
                                raise HTTPException(
                                    status_code=400,
                                    detail=f"Murder year {murder_year} is after victim's date of death {victim_dod}"
                                )
                            date_approx = date_year
                        else:
                            raise HTTPException(status_code=400, detail="Year is required")
                    elif date_precision == "unknown":
                        raise HTTPException(status_code=400, detail="Death date is already known")
                elif victim_dod_approx and victim_dod_approx != "unknown":
                    # Victim has an approximate death date (but no precise date).
                    if date_precision == "exact":
                        if date_exact:
                            dt = datetime.strptime(date_exact, "%Y-%m-%d").date()
                            event_date = dt.strftime("%Y-%m-%d")
                            date_approx = dt.strftime("%Y")
                        else:
                            raise HTTPException(status_code=400, detail="Exact date is required")
                    elif date_precision == "year":
                        raise HTTPException(status_code=400, detail="A more precise date is required")
                    elif date_precision == "unknown":
                        raise HTTPException(status_code=400, detail="Death date is already known approximately")
                else:
                    # Victim is dead but no death date has been set.
                    if date_precision == "exact":
                        if date_exact:
                            dt = datetime.strptime(date_exact, "%Y-%m-%d").date()
                            event_date = dt.strftime("%Y-%m-%d")
                            date_approx = dt.strftime("%Y")
                        else:
                            raise HTTPException(status_code=400, detail="Exact date is required")
                    elif date_precision == "year":
                        if date_year:
                            date_approx = date_year
                        else:
                            raise HTTPException(status_code=400, detail="Year is required")
                    elif date_precision == "unknown":
                        date_approx = "unknown"
        else:
            # Victim is not dead.
            if date_precision == "exact":
                if date_exact:
                    dt = datetime.strptime(date_exact, "%Y-%m-%d").date()
                    event_date = dt.strftime("%Y-%m-%d")
                    date_approx = dt.strftime("%Y")
                else:
                    raise HTTPException(status_code=400, detail="Exact date is required")
            elif date_precision == "year":
                if date_year:
                    date_approx = date_year
                else:
                    raise HTTPException(status_code=400, detail="Year is required")
            elif date_precision == "unknown":
                date_approx = "unknown"

        # Insert murder record with properly formatted strings for dates.
        cursor.execute(
            "INSERT INTO murders (shooter_id, victim_id, date, date_approx) VALUES (?, ?, ?, ?)",
            (member_id, victim_id, event_date, date_approx)
        )

        # Update the victim's record based on the provided precision.
        if date_precision in ["exact", "keep"]:
            update_query = """
            UPDATE members
            SET status = 'dead',
                death_date = CASE
                    WHEN death_date IS NULL OR death_date > ? THEN ? 
                    ELSE death_date
                END,
                death_date_approx = ?
            WHERE id = ?
            """
            cursor.execute(update_query, (event_date, event_date, date_approx, victim_id))
        elif date_precision == "year":
            update_query = """
            UPDATE members
            SET status = 'dead',
                death_date_approx = ?
            WHERE id = ?
            """
            cursor.execute(update_query, (date_approx, victim_id))
        elif date_precision == "unknown":
            update_query = """
            UPDATE members
            SET status = 'dead',
                death_date_approx = 'unknown'
            WHERE id = ?
            """
            cursor.execute(update_query, (victim_id,))

        conn.commit()
        return RedirectResponse(url=f"/members/{member_id}", status_code=303)

    except HTTPException as e:
        return handle_error(
            request, member_id, "murders", victim_id,
            date_precision, date_exact, date_year, e
        )

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()





async def add_assist(
    request: Request,
    member_id: int,
    victim_id: int
):
    # Get database connection
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Fetch the murder event details to get the date
        cursor.execute("SELECT death_date, death_date_approx FROM members WHERE id = ?", (victim_id,))
        murder_event = cursor.fetchone()

        if not murder_event:
            raise HTTPException(status_code=400, detail="No murder record found for the victim")

        murder_date, murder_date_approx = murder_event

        # Insert assist record with the same date as the murder
        cursor.execute(
            "INSERT INTO assists (shooter_id, victim_id, date, date_approx) VALUES (?, ?, ?, ?)",
            (member_id, victim_id, murder_date, murder_date_approx)
        )
        conn.commit()
        return RedirectResponse(url=f"/members/{member_id}", status_code=303)

    except HTTPException as e:
        return handle_error(request, member_id, "assists", victim_id, None, None, None, e)

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


def handle_error(request, member_id, event_type, victim_id, date_precision, date_exact, date_year, error):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, death_date FROM members WHERE id != ?", (member_id,))
    all_members = cursor.fetchall()
    conn.close()
    return templates.TemplateResponse("events/add_event.html", {
        "request": request,
        "event_type": event_type,
        "member_id": member_id,
        "all_members": all_members,
        "error_message": error.detail,
        "form_data": {
            "victim_id": victim_id,
            "date_precision": date_precision,
            "date_exact": date_exact,
            "date_year": date_year
        }
    }, status_code=error.status_code)

def parse_date(date_precision, date_exact, date_year):
    event_date = None
    date_approx = None
    if date_precision == "exact" and date_exact:
        try:
            parsed_date = datetime.strptime(date_exact, "%Y-%m-%d").date()
            event_date = date_exact
            date_approx = parsed_date.strftime("%Y")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format (must be YYYY-MM-DD)")
    elif date_precision == "year" and date_year:
        if not date_year.isdigit() or len(date_year) != 4:
            raise HTTPException(status_code=400, detail="Invalid year format (must be YYYY)")
        date_approx = date_year
    elif date_precision == "unknown":
        date_approx = "unknown"
    else:
        raise HTTPException(status_code=400, detail="Invalid date precision")
    return event_date, date_approx


@router.post("/add/{event_type}/{member_id}", response_class=RedirectResponse)
async def add_event(
    request: Request,
    event_type: str,
    member_id: int,
    victim_id: int = Form(...),
    date_precision: str = Form(None),
    date_exact: Optional[str] = Form(None),
    date_year: Optional[str] = Form(None)
):
    event_type = normalize_event_type(event_type)

    # Validate event_type
    if event_type not in VALID_EVENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid event type")

    # Validate shooter exists and was alive at event time
    validate_member(member_id, check_alive=True)

    # Validate victim exists
    validate_member(victim_id)

    # Ensure shooter and victim are distinct
    if member_id == victim_id:
        raise HTTPException(status_code=400, detail="Shooter and victim cannot be the same")

    # Route to the appropriate handler
    if event_type == "shootings":
        return await add_shooting(request, member_id, victim_id, date_precision, date_exact, date_year)
    elif event_type == "murders":
        return await add_murder(request, member_id, victim_id, date_precision, date_exact, date_year)
    elif event_type == "assists":
        return await add_assist(request, member_id, victim_id)




@router.post("/delete/{event_type}/{event_id}", response_class=RedirectResponse)
async def delete_event(event_type: str, event_id: int):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Validate event type
        if event_type not in {"shooting", "murder", "assist"}:
            raise HTTPException(status_code=400, detail="Invalid event type")

        # Get member_id before deletion for redirect
        cursor.execute(f"SELECT shooter_id FROM {event_type}s WHERE id = ?", (event_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Event not found")
        member_id = result['shooter_id']

        # Delete the event
        cursor.execute(f"DELETE FROM {event_type}s WHERE id = ?", (event_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

    return RedirectResponse(url=f"/members/{member_id}", status_code=303)
