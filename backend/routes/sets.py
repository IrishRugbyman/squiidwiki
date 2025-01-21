from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from backend.database import get_db
from pathlib import Path
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any

# Define the absolute path to the templates directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Points to the project root
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sets")
    sets = cursor.fetchall()
    return templates.TemplateResponse("sets/index.html", {"request": request, "sets": sets})

@router.get("/add", response_class=HTMLResponse)
def add_set_form(request: Request):
    return templates.TemplateResponse("sets/add_set.html", {"request": request})

@router.post("/add", response_class=RedirectResponse)
def add_set(
    name: str = Form(...),
    description: str = Form(None),
    allies: str = Form(None),  # Comma-separated IDs
    enemies: str = Form(None),  # Comma-separated IDs
):
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Insert the new set
        cursor.execute(
            "INSERT INTO sets (name, description) VALUES (?, ?)",
            (name, description),
        )
        set_id = cursor.lastrowid  # Get the newly created set's ID

        # Handle allies
        if allies:
            ally_ids = [int(a.strip()) for a in allies.split(",") if a.strip().isdigit()]
            for ally_id in ally_ids:
                cursor.execute(
                    "INSERT OR IGNORE INTO set_allies_map (set_id, ally_id) VALUES (?, ?)",
                    (set_id, ally_id),
                )

        # Handle enemies
        if enemies:
            enemy_ids = [int(e.strip()) for e in enemies.split(",") if e.strip().isdigit()]
            for enemy_id in enemy_ids:
                cursor.execute(
                    "INSERT OR IGNORE INTO set_enemies_map (set_id, enemy_id) VALUES (?, ?)",
                    (set_id, enemy_id),
                )

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

    return RedirectResponse(url="/sets/", status_code=303)

@router.get("/set_options")
def get_set_options() -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name FROM sets")
        sets = cursor.fetchall()
        return [{"id": set[0], "name": set[1]} for set in sets]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

@router.get("/{set_id}", response_class=HTMLResponse)
def read_set(request: Request, set_id: int):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM sets WHERE id = ?", (set_id,))
        set = cursor.fetchone()
        if not set:
            raise HTTPException(status_code=404, detail="Set not found")

        cursor.execute("SELECT * FROM members WHERE set_id = ?", (set_id,))
        members = cursor.fetchall()

        # Get allies for the set
        cursor.execute("""
            SELECT sets.name, sets.id FROM sets
            JOIN set_allies_map ON sets.id = set_allies_map.ally_id
            WHERE set_allies_map.set_id = ?
        """, (set_id,))
        allies = cursor.fetchall()

        # Get enemies for the set
        cursor.execute("""
            SELECT sets.name, sets.id FROM sets
            JOIN set_enemies_map ON sets.id = set_enemies_map.enemy_id
            WHERE set_enemies_map.set_id = ?
        """, (set_id,))
        enemies = cursor.fetchall()

        return templates.TemplateResponse("sets/set_details.html", {
            "request": request,
            "set": set,
            "members": members,
            "allies": allies,
            "enemies": enemies
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

