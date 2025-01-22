from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from backend.database.database import get_db
from pathlib import Path
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from backend.database.enums import eSetType

# Define the absolute path to the templates directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Points to the project root
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)

router = APIRouter()

@contextmanager
def db_connection():
    conn = get_db()
    try:
        yield conn
    finally:
        conn.close()

def fetch_sets(cursor):
    cursor.execute("SELECT * FROM sets")
    return cursor.fetchall()

def group_sets(sets):
    grouped_sets = {}
    for set in sets:
        name = set[1]  # Assuming set[1] is the set name
        first_char = name[0].upper() if name[0].isalpha() else '#'
        if first_char not in grouped_sets:
            grouped_sets[first_char] = []
        grouped_sets[first_char].append(set)
    return grouped_sets

def process_relations(cursor, set_id, relation_names, relation_table):
    # Determine the relation column (ally_id or enemy_id)
    if relation_table == "set_allies_map":
        relation_column = "ally_id"
    elif relation_table == "set_enemies_map":
        relation_column = "enemy_id"
    else:
        raise ValueError(f"Unknown relation table: {relation_table}")

    # Fetch current relations for the set
    cursor.execute(f"SELECT {relation_column} FROM {relation_table} WHERE set_id = ?", (set_id,))
    current_relation_ids = [row[0] for row in cursor.fetchall()]

    # Convert new relation names to their IDs
    new_relation_ids = []
    if relation_names:
        names = [name.strip() for name in relation_names.split(",") if name.strip()]
        for name in names:
            cursor.execute("SELECT id FROM sets WHERE name = ?", (name,))
            relation_id_row = cursor.fetchone()
            if relation_id_row:
                new_relation_ids.append(relation_id_row[0])

    # Determine which relations to remove (current - new)
    removed_relation_ids = set(current_relation_ids) - set(new_relation_ids)

    # Delete both directions for removed relations
    for removed_id in removed_relation_ids:
        # Delete (set_id, removed_id)
        cursor.execute(
            f"DELETE FROM {relation_table} WHERE set_id = ? AND {relation_column} = ?",
            (set_id, removed_id)
        )
        # Delete (removed_id, set_id)
        cursor.execute(
            f"DELETE FROM {relation_table} WHERE set_id = ? AND {relation_column} = ?",
            (removed_id, set_id)
        )

    # Determine which relations to add (new - current)
    added_relation_ids = set(new_relation_ids) - set(current_relation_ids)

    # Insert both directions for new relations
    for added_id in added_relation_ids:
        # Insert (set_id, added_id)
        cursor.execute(
            f"INSERT OR IGNORE INTO {relation_table} (set_id, {relation_column}) VALUES (?, ?)",
            (set_id, added_id)
        )
        # Insert (added_id, set_id)
        cursor.execute(
            f"INSERT OR IGNORE INTO {relation_table} (set_id, {relation_column}) VALUES (?, ?)",
            (added_id, set_id)
        )

@router.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    with db_connection() as conn:
        cursor = conn.cursor()
        sets = fetch_sets(cursor)
        grouped_sets = group_sets(sets)
        sorted_groups = sorted(grouped_sets.items(), key=lambda x: x[0])
        sorted_grouped_sets = {char: sorted(group, key=lambda x: x[1]) for char, group in sorted_groups}
        return templates.TemplateResponse("sets/index.html", {"request": request, "grouped_sets": sorted_grouped_sets})

@router.get("/add", response_class=HTMLResponse)
def add_set_form(request: Request):
    return templates.TemplateResponse("sets/add_set.html", {"request": request})

@router.post("/add", response_class=RedirectResponse)
def add_set(
        name: str = Form(...),
        description: str = Form(None),
        allies: str = Form(None),
        enemies: str = Form(None),
        is_extinct: bool = Form(False),
):
    with db_connection() as conn:
        cursor = conn.cursor()
        try:
            set_type = eSetType.EXTINCT if is_extinct else eSetType.ACTIVE
            cursor.execute(
                "INSERT INTO sets (name, description, type) VALUES (?, ?, ?)",
                (name, description, set_type.value),
            )
            set_id = cursor.lastrowid

            process_relations(cursor, set_id, allies, "set_allies_map")
            process_relations(cursor, set_id, enemies, "set_enemies_map")

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return RedirectResponse(url="/sets/", status_code=303)

@router.get("/set_options")
def get_set_options():
    with db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, name FROM sets")
            sets = cursor.fetchall()
            return [{"id": set[0], "name": set[1]} for set in sets]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{set_id}", response_class=HTMLResponse)
def read_set(request: Request, set_id: int):
    with db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM sets WHERE id = ?", (set_id,))
            set = cursor.fetchone()
            if not set:
                raise HTTPException(status_code=404, detail="Set not found")

            cursor.execute("SELECT * FROM members WHERE set_id = ?", (set_id,))
            members = cursor.fetchall()

            cursor.execute("""
                SELECT sets.name, sets.id FROM sets
                JOIN set_allies_map ON sets.id = set_allies_map.ally_id
                WHERE set_allies_map.set_id = ?
            """, (set_id,))
            allies = cursor.fetchall()

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

@router.get("/edit/{set_id}", response_class=HTMLResponse)
def edit_set_form(request: Request, set_id: int):
    with db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM sets WHERE id = ?", (set_id,))
            set = cursor.fetchone()
            if not set:
                raise HTTPException(status_code=404, detail="Set not found")

            # Fetch allies
            cursor.execute("""
                SELECT sets.name, sets.id FROM sets
                JOIN set_allies_map ON sets.id = set_allies_map.ally_id
                WHERE set_allies_map.set_id = ?
            """, (set_id,))
            allies = cursor.fetchall()
            ally_names = [ally[0] for ally in allies]  # Extract only names

            # Fetch enemies
            cursor.execute("""
                SELECT sets.name, sets.id FROM sets
                JOIN set_enemies_map ON sets.id = set_enemies_map.enemy_id
                WHERE set_enemies_map.set_id = ?
            """, (set_id,))
            enemies = cursor.fetchall()
            enemy_names = [enemy[0] for enemy in enemies]  # Extract only names

            return templates.TemplateResponse("sets/edit_set.html", {
                "request": request,
                "set": set,
                "allies": ally_names,  # Pass only names
                "enemies": enemy_names  # Pass only names
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/edit/{set_id}", response_class=RedirectResponse)
def edit_set(
        set_id: int,
        name: str = Form(...),
        description: str = Form(None),
        allies: str = Form(None),
        enemies: str = Form(None),
        is_extinct: bool = Form(False),
):
    with db_connection() as conn:
        cursor = conn.cursor()
        try:
            # Fetch the current set name
            cursor.execute("SELECT name FROM sets WHERE id = ?", (set_id,))
            set_name = cursor.fetchone()[0]

            # Convert allies and enemies to lists
            ally_list = [name.strip() for name in allies.split(",")] if allies else []
            enemy_list = [name.strip() for name in enemies.split(",")] if enemies else []

            # Check if the set is its own ally or enemy
            if set_name in ally_list or set_name in enemy_list:
                raise HTTPException(status_code=400, detail="A set cannot be its own ally or enemy.")

            # Check if a set is both an ally and enemy of the same set
            common_sets = set(ally_list).intersection(set(enemy_list))
            if common_sets:
                raise HTTPException(status_code=400, detail="A set cannot be both an ally and enemy of the same set.")

            set_type = eSetType.EXTINCT if is_extinct else eSetType.ACTIVE
            cursor.execute(
                "UPDATE sets SET name = ?, description = ?, type = ? WHERE id = ?",
                (name, description, set_type.value, set_id),
            )

            process_relations(cursor, set_id, allies, "set_allies_map")
            process_relations(cursor, set_id, enemies, "set_enemies_map")

            conn.commit()
        except HTTPException as he:
            raise he
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return RedirectResponse(url=f"/sets/{set_id}", status_code=303)