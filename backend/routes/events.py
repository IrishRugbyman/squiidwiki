import sqlite3

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


def validate_member_exists(member_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM members WHERE id = ?", (member_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Member not found")
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


# Modify these three route handlers
@router.get("/shootings/{member_id}", response_class=HTMLResponse)
async def get_shootings(request: Request, member_id: int):
    validate_member_exists(member_id)
    shootings = get_events_by_type(member_id, "shooting")

    # Get all other members
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM members WHERE id != ?", (member_id,))
    all_members = cursor.fetchall()

    return templates.TemplateResponse("event_list.html", {
        "request": request,
        "events": shootings,
        "event_type": "shooting",
        "member_id": member_id,
        "all_members": all_members  # Add this
    })


@router.get("/murders/{member_id}", response_class=HTMLResponse)
async def get_murders(request: Request, member_id: int):
    validate_member_exists(member_id)
    murders = get_events_by_type(member_id, "murder")

    # Get all other members
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM members WHERE id != ?", (member_id,))
    all_members = cursor.fetchall()

    return templates.TemplateResponse("event_list.html", {
        "request": request,
        "events": murders,
        "event_type": "murder",
        "member_id": member_id,
        "all_members": all_members  # Add this
    })


@router.get("/assists/{member_id}", response_class=HTMLResponse)
async def get_assists(request: Request, member_id: int):
    validate_member_exists(member_id)
    assists = get_events_by_type(member_id, "assist")

    # Get all other members
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM members WHERE id != ?", (member_id,))
    all_members = cursor.fetchall()

    return templates.TemplateResponse("event_list.html", {
        "request": request,
        "events": assists,
        "event_type": "assist",
        "member_id": member_id,
        "all_members": all_members  # Add this
    })

@router.post("/add/{event_type}/{member_id}", response_class=RedirectResponse)
async def add_event(
        event_type: str,
        member_id: int,
        victim_id: int = Form(...),
        date: str = Form(...)
):
    validate_member_exists(member_id)
    validate_member_exists(victim_id)

    if member_id == victim_id:
        raise HTTPException(status_code=400, detail="Cannot add self-event")

    conn = get_db()
    try:
        conn.execute(
            f"INSERT INTO {event_type}s (shooter_id, victim_id, date) VALUES (?, ?, ?)",
            (member_id, victim_id, date)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Invalid event data")

    return RedirectResponse(url=f"/members/{member_id}", status_code=303)


@router.post("/delete/{event_type}/{event_id}", response_class=RedirectResponse)
async def delete_event(event_type: str, event_id: int):
    conn = get_db()
    cursor = conn.cursor()

    # Get member_id before deletion for redirect
    cursor.execute(f"SELECT shooter_id FROM {event_type}s WHERE id = ?", (event_id,))
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Event not found")

    member_id = result[0]

    cursor.execute(f"DELETE FROM {event_type}s WHERE id = ?", (event_id,))
    conn.commit()

    return RedirectResponse(url=f"/members/{member_id}", status_code=303)