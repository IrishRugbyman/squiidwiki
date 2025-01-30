import sqlite3
from typing import Optional

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from backend.database.database import get_db
from pathlib import Path
from fastapi.templating import Jinja2Templates
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)

router = APIRouter()


def validate_member(member_id: int, event_date: Optional[str] = None, check_alive: bool = False):
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT id, status, date_of_death FROM members WHERE id = ?"
    cursor.execute(query, (member_id,))
    member = cursor.fetchone()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if check_alive:
        if member[1] == 'dead':
            if event_date:
                # Parse dates for comparison
                try:
                    event_dt = datetime.strptime(event_date, "%Y-%m-%d").date()
                    death_dt = datetime.strptime(member[2], "%Y-%m-%d").date() if member[2] else None
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid date format, use YYYY-MM-DD")

                if death_dt and event_dt > death_dt:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Member was dead on {member[2]}, cannot participate in event on {event_date}"
                    )
            else:
                raise HTTPException(status_code=400, detail="Member is dead")

    return member_id


def get_events_by_type(member_id: int, event_type: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT * FROM {event_type}s 
        WHERE shooter_id = ? OR victim_id = ?
        ORDER BY date DESC
    """, (member_id, member_id))
    return cursor.fetchall()


def get_victim_info(events: list):
    """Helper function to get victim information for events"""
    conn = get_db()
    cursor = conn.cursor()

    victim_ids = {event[2] for event in events}  # victim_id is at index 2
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

    return {
        "member_names": member_names,
        "victim_sets": victim_sets,
        "victim_set_ids": victim_set_ids
    }


@router.get("/shootings/{member_id}", response_class=HTMLResponse)
async def get_shootings(request: Request, member_id: int):
    validate_member(member_id)
    shootings = get_events_by_type(member_id, "shooting")
    victim_info = get_victim_info(shootings)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM members WHERE id != ?", (member_id,))
    all_members = cursor.fetchall()

    return templates.TemplateResponse("event_list.html", {
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
    murders = get_events_by_type(member_id, "murder")
    victim_info = get_victim_info(murders)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM members WHERE id != ?", (member_id,))
    all_members = cursor.fetchall()

    return templates.TemplateResponse("event_list.html", {
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
    assists = get_events_by_type(member_id, "assist")
    victim_info = get_victim_info(assists)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM members WHERE id != ?", (member_id,))
    all_members = cursor.fetchall()

    return templates.TemplateResponse("event_list.html", {
        "request": request,
        "events": assists,
        "event_type": "assist",
        "member_id": member_id,
        "all_members": all_members,
        **victim_info
    })


@router.post("/add/{event_type}/{member_id}")
async def add_event(
    request: Request,
    event_type: str,
    member_id: int,
    victim_id: int = Form(...),
    date: str = Form(...)
):
    conn = None
    error_message = None
    form_data = {"victim_id": victim_id, "date": date}  # Preserve form inputs

    try:
        # Basic validations
        if member_id == victim_id:
            raise HTTPException(status_code=400, detail="Cannot add self-event")

        conn = get_db()
        cursor = conn.cursor()

        # Validate shooter exists and was alive at event time
        validate_member(member_id, event_date=date, check_alive=True)
        # Validate victim exists
        validate_member(victim_id)

        # Additional validations for murders
        if event_type == 'murder':
            # Check if victim is already murdered
            cursor.execute("SELECT id FROM murders WHERE victim_id = ?", (victim_id,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Victim already has a murder record")

            # Check victim's current status and death date
            cursor.execute("SELECT status, date_of_death FROM members WHERE id = ?", (victim_id,))
            victim_status, victim_dod = cursor.fetchone()

            # If victim is already dead, check murder date is not after their death
            if victim_status == 'dead' and victim_dod:
                try:
                    murder_date = datetime.strptime(date, "%Y-%m-%d").date()
                    existing_dod = datetime.strptime(victim_dod, "%Y-%m-%d").date()
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid date format, use YYYY-MM-DD")

                if murder_date > existing_dod:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Murder date {date} is after victim's date of death {victim_dod}"
                    )

            # Insert murder record
            cursor.execute(
                "INSERT INTO murders (shooter_id, victim_id, date) VALUES (?, ?, ?)",
                (member_id, victim_id, date)
            )

            # Update victim's status and date_of_death
            update_query = """
                UPDATE members
                SET status = 'dead',
                    date_of_death = CASE
                        WHEN date_of_death IS NULL OR date_of_death > ? THEN ?
                        ELSE date_of_death
                    END
                WHERE id = ?
            """
            cursor.execute(update_query, (date, date, victim_id))

        else:  # shootings and assists
            cursor.execute(
                f"INSERT INTO {event_type}s (shooter_id, victim_id, date) VALUES (?, ?, ?)",
                (member_id, victim_id, date)
            )

        conn.commit()
        return RedirectResponse(url=f"/members/{member_id}", status_code=303)

    except HTTPException as he:
        error_message = he.detail  # Capture error message for display
    except sqlite3.IntegrityError as e:
        error_message = "Victim already has a murder record" if "murders.victim_id" in str(e) else str(e)
    except Exception as e:
        error_message = str(e)
    finally:
        if conn:
            conn.close()

    if error_message:
        # Get required data for template
        conn = get_db()
        try:
            events = get_events_by_type(member_id, event_type)
            victim_info = get_victim_info(events)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM members WHERE id != ?", (member_id,))
            all_members = cursor.fetchall()

            return templates.TemplateResponse("event_list.html", {
                "request": request,
                "events": events,
                "event_type": event_type,
                "member_id": member_id,
                "all_members": all_members,
                "form_data": form_data,  # Pass preserved form data
                "error_message": error_message,  # Pass error message
                **victim_info
            })
        finally:
            conn.close()

    return RedirectResponse(url=f"/members/{member_id}", status_code=303)

@router.post("/delete/{event_type}/{event_id}", response_class=RedirectResponse)
async def delete_event(event_type: str, event_id: int):
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Get member_id before deletion for redirect
        cursor.execute(f"SELECT shooter_id FROM {event_type}s WHERE id = ?", (event_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Event not found")

        member_id = result[0]

        cursor.execute(f"DELETE FROM {event_type}s WHERE id = ?", (event_id,))
        conn.commit()

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

    return RedirectResponse(url=f"/members/{member_id}", status_code=303)