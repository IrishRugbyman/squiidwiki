from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from backend.database.database import get_db
from pathlib import Path
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from backend.database.enums import eSetType
from backend.database.models import SetCreate, Set, Member
from fastapi import Query
from fastapi.responses import JSONResponse

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


def fetch_sets(cursor) -> List[Set]:
    cursor.execute("SELECT id, name, description, type FROM sets")
    rows = cursor.fetchall()
    sets_list = []
    for row in rows:
        set_dict = {
            "id": row['id'],
            "name": row['name'],
            "description": row['description'],
            "type": row['type'],  # This is stored as a string; Pydantic will convert it if needed.
        }
        try:
            set_obj = Set.parse_obj(set_dict)
        except Exception as e:
            set_obj = set_dict
        sets_list.append(set_obj)
    return sets_list


def group_sets(sets: List[Any]) -> Dict[str, List[Any]]:
    grouped_sets = {}
    for s in sets:
        name = s.name if hasattr(s, "name") else s['name']
        first_char = name[0].upper() if name and name[0].isalpha() else '#'
        grouped_sets.setdefault(first_char, []).append(s)
    return grouped_sets


def process_relations(cursor, set_id: int, relation_names: Optional[str], relation_table: str):
    """
    Handles both the removal and insertion of relation links. (Works for allies and enemies.)
    """
    if relation_table == "set_allies_map":
        relation_column = "ally_id"
    elif relation_table == "set_enemies_map":
        relation_column = "enemy_id"
    else:
        raise ValueError(f"Unknown relation table: {relation_table}")

    cursor.execute(f"SELECT {relation_column} FROM {relation_table} WHERE set_id = ?", (set_id,))
    current_relation_ids = [row[relation_column] for row in cursor.fetchall()]

    new_relation_ids = []
    if relation_names:
        names = [name.strip() for name in relation_names.split(",") if name.strip()]
        for name in names:
            cursor.execute("SELECT id FROM sets WHERE name = ?", (name,))
            relation_id_row = cursor.fetchone()
            if relation_id_row:
                new_relation_ids.append(relation_id_row['id'])

    removed_relation_ids = set(current_relation_ids) - set(new_relation_ids)
    for removed_id in removed_relation_ids:
        cursor.execute(
            f"DELETE FROM {relation_table} WHERE set_id = ? AND {relation_column} = ?",
            (set_id, removed_id)
        )
        cursor.execute(
            f"DELETE FROM {relation_table} WHERE set_id = ? AND {relation_column} = ?",
            (removed_id, set_id)
        )

    added_relation_ids = set(new_relation_ids) - set(current_relation_ids)
    for added_id in added_relation_ids:
        cursor.execute(
            f"INSERT OR IGNORE INTO {relation_table} (set_id, {relation_column}) VALUES (?, ?)",
            (set_id, added_id)
        )
        cursor.execute(
            f"INSERT OR IGNORE INTO {relation_table} (set_id, {relation_column}) VALUES (?, ?)",
            (added_id, set_id)
        )


def get_special_set_id(set_type: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM config WHERE key = ?", (f"{set_type}_set_id",))
    return cursor.fetchone()['value']


@router.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    with db_connection() as conn:
        cursor = conn.cursor()
        sets_list = fetch_sets(cursor)
        grouped = group_sets(sets_list)
        sorted_groups = sorted(grouped.items(), key=lambda x: x[0])
        sorted_grouped_sets = {
            char: sorted(group, key=lambda s: s['name'] if isinstance(s, dict) else s.name)
            for char, group in sorted_groups
        }
        return templates.TemplateResponse("sets/index.html", {
            "request": request,
            "grouped_sets": sorted_grouped_sets
        })


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
            # Validation: Convert allies and enemies strings into lists of names.
            ally_list = [n.strip() for n in allies.split(",") if n.strip()] if allies else []
            enemy_list = [n.strip() for n in enemies.split(",") if n.strip()] if enemies else []

            # Validate that the set's own name is not included
            if name in ally_list or name in enemy_list:
                raise HTTPException(status_code=400, detail="A set cannot be its own ally or enemy.")

            # Validate that no set is provided as both ally and enemy
            if set(ally_list).intersection(set(enemy_list)):
                raise HTTPException(status_code=400, detail="A set cannot be both an ally and enemy of the same set.")

            # Determine the set type
            set_type = eSetType.EXTINCT if is_extinct else eSetType.ACTIVE

            # Create a new set using your Pydantic model for validation
            new_set = SetCreate(name=name, description=description, type=set_type)

            # Insert the new set into the database
            cursor.execute(
                "INSERT INTO sets (name, description, type) VALUES (?, ?, ?)",
                (new_set.name, new_set.description, new_set.type.value)
            )
            set_id = cursor.lastrowid

            # Process relations (allies and enemies)
            process_relations(cursor, set_id, allies, "set_allies_map")
            process_relations(cursor, set_id, enemies, "set_enemies_map")

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        return RedirectResponse(url="/sets/", status_code=303)


@router.get("/set_options", response_class=JSONResponse)
def set_options(exclude: int = Query(None)):
    with db_connection() as conn:
        cursor = conn.cursor()
        # Retrieve the default set ids from your config
        cursor.execute("SELECT value FROM config WHERE key IN ('unknown_set_id', 'civilian_set_id')")
        default_ids = [int(row['value']) for row in cursor.fetchall()]

        # Start building your query
        query = "SELECT id, name FROM sets"
        params = []
        conditions = []

        # Exclude the current set (if provided)
        if exclude:
            conditions.append("id != ?")
            params.append(exclude)

        # Exclude the default sets
        if default_ids:
            placeholders = ",".join("?" for _ in default_ids)
            conditions.append(f"id NOT IN ({placeholders})")
            params.extend(default_ids)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cursor.execute(query, tuple(params))
        options = cursor.fetchall()

        # Return list of dictionaries
        return JSONResponse(content=[{"id": option["id"], "name": option["name"]} for option in options])


@router.get("/edit/{set_id}", response_class=HTMLResponse)
def edit_set_form(request: Request, set_id: int):
    with db_connection() as conn:
        cursor = conn.cursor()
        try:
            # Fetch set details
            cursor.execute("SELECT id, name, description, type FROM sets WHERE id = ?", (set_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Set not found")
            set_dict = {"id": row['id'], "name": row['name'], "description": row['description'], "type": row['type']}

            # Check if the set is a default set
            cursor.execute("SELECT value FROM config WHERE key IN ('unknown_set_id', 'civilian_set_id')")
            special_ids = [row['value'] for row in cursor.fetchall()]
            is_default_set = set_id in special_ids

            # Fetch allies and enemies
            cursor.execute("""
                SELECT s.name FROM sets s
                JOIN set_allies_map ON s.id = set_allies_map.ally_id
                WHERE set_allies_map.set_id = ?
            """, (set_id,))
            allies = [r['name'] for r in cursor.fetchall()]

            cursor.execute("""
                SELECT s.name FROM sets s
                JOIN set_enemies_map ON s.id = set_enemies_map.enemy_id
                WHERE set_enemies_map.set_id = ?
            """, (set_id,))
            enemies = [r['name'] for r in cursor.fetchall()]

            return templates.TemplateResponse("sets/edit_set.html", {
                "request": request,
                "set": set_dict,
                "allies": ", ".join(allies),
                "enemies": ", ".join(enemies),
                "is_default_set": is_default_set  # Pass the flag to the frontend
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
            cursor.execute("SELECT value FROM config WHERE key IN ('unknown_set_id', 'civilian_set_id')")
            special_ids = [row['value'] for row in cursor.fetchall()]
            if set_id in special_ids:
                raise HTTPException(
                    status_code=303,
                    detail="System sets cannot be modified",
                    headers={"Location": f"/sets/{set_id}?error=system_set"}
                )

            cursor.execute("SELECT name FROM sets WHERE id = ?", (set_id,))
            current_name = cursor.fetchone()['name']

            ally_list = [n.strip() for n in allies.split(",")] if allies else []
            enemy_list = [n.strip() for n in enemies.split(",")] if enemies else []

            if current_name in ally_list or current_name in enemy_list:
                raise HTTPException(status_code=400, detail="A set cannot be its own ally or enemy.")
            if set(ally_list).intersection(set(enemy_list)):
                raise HTTPException(status_code=400, detail="A set cannot be both an ally and enemy of the same set.")

            set_type = eSetType.EXTINCT if is_extinct else eSetType.ACTIVE
            updated_set = SetCreate(name=name, description=description, type=set_type)

            cursor.execute(
                "UPDATE sets SET name = ?, description = ?, type = ? WHERE id = ?",
                (updated_set.name, updated_set.description, updated_set.type.value, set_id)
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


@router.get("/delete/{set_id}", response_class=HTMLResponse)
def delete_set_confirmation(request: Request, set_id: int):
    with db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT value FROM config WHERE key IN ('unknown_set_id', 'civilian_set_id')")
            special_ids = [row['value'] for row in cursor.fetchall()]
            if set_id in special_ids:
                return RedirectResponse(url=f"/sets/{set_id}?error=Cannot delete system sets")

            cursor.execute("SELECT id, name, description, type FROM sets WHERE id = ?", (set_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Set not found")
            set_dict = {"id": row['id'], "name": row['name'], "description": row['description'], "type": row['type']}

            cursor.execute("SELECT COUNT(*) FROM members WHERE set_id = ?", (set_id,))
            member_count = cursor.fetchone()['COUNT(*)']

            return templates.TemplateResponse("sets/delete_set.html", {
                "request": request,
                "set": set_dict,
                "member_count": member_count,
                "special_set_id": get_special_set_id('unknown')
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete/{set_id}", response_class=RedirectResponse)
def delete_set(
        request: Request,
        set_id: int,
        member_action: str = Form(...),
        target_set: Optional[int] = Form(None)
):
    with db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM sets WHERE id = ?", (set_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Set not found")

            if member_action == "move":
                if not target_set:
                    raise HTTPException(status_code=400, detail="Target set required for member transfer")
                cursor.execute("SELECT id FROM sets WHERE id = ?", (target_set,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=400, detail="Invalid destination set")
                cursor.execute("UPDATE members SET set_id = ? WHERE set_id = ?", (target_set, set_id))
            elif member_action == "delete":
                cursor.execute("""
                    DELETE FROM incidents 
                    WHERE shooter_id IN (SELECT id FROM members WHERE set_id = ?)
                    OR victim_id IN (SELECT id FROM members WHERE set_id = ?)
                """, (set_id, set_id))
                cursor.execute("DELETE FROM members WHERE set_id = ?", (set_id,))

            cursor.execute("DELETE FROM set_allies_map WHERE set_id = ? OR ally_id = ?", (set_id, set_id))
            cursor.execute("DELETE FROM set_enemies_map WHERE set_id = ? OR enemy_id = ?", (set_id, set_id))
            cursor.execute("DELETE FROM sets WHERE id = ?", (set_id,))
            conn.commit()
            return RedirectResponse(url="/sets/", status_code=303)
        except HTTPException as he:
            raise he
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@router.get("/{set_id}", response_class=HTMLResponse)
def read_set(request: Request, set_id: int):
    with db_connection() as conn:
        cursor = conn.cursor()
        try:
            # Fetch set details
            cursor.execute("SELECT id, name, description, type FROM sets WHERE id = ?", (set_id,))
            row = cursor.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Set not found")

            set_data = {
                "id": row['id'],
                "name": row['name'],
                "description": row['description'],
                "type": row['type']
            }
            set_obj = Set.parse_obj(set_data)

            # Count members
            cursor.execute("SELECT COUNT(*) as count FROM members WHERE set_id = ?", (set_id,))
            count_row = cursor.fetchone()
            member_count = count_row['count'] if count_row else 0

            # Fetch members and convert each row into a Member model instance
            cursor.execute("""
            SELECT id, name, description, status, release_date, release_date_approx,
                   death_date, death_date_approx, set_id, alliance_id
            FROM members WHERE set_id = ?
            """, (set_id,))
            members_rows = cursor.fetchall()
            members = []
            for row in members_rows:
                if row is not None:
                    members.append(
                        Member.parse_obj({
                            "id": row["id"],
                            "name": row["name"],
                            "description": row["description"],
                            "status": row["status"],
                            "release_date": row["release_date"],
                            "release_date_approx": row["release_date_approx"],
                            "death_date": row["death_date"] if row["death_date"] != 'unknown' else None,
                            "death_date_approx": row["death_date_approx"] if row["death_date_approx"] != 'unknown' else 'unknown',
                            "set_id": row["set_id"],
                            "alliance_id": row["alliance_id"]
                        })
                    )

            # Fetch allies and convert each row into a Set model instance
            cursor.execute("""
                SELECT s.id, s.name, s.description, s.type
                FROM sets s
                JOIN set_allies_map ON s.id = set_allies_map.ally_id
                WHERE set_allies_map.set_id = ?
            """, (set_id,))
            allies_rows = cursor.fetchall()
            allies = [Set.parse_obj(dict(row)) for row in allies_rows if row is not None]

            # Fetch enemies and convert each row into a Set model instance
            cursor.execute("""
                SELECT s.id, s.name, s.description, s.type
                FROM sets s
                JOIN set_enemies_map ON s.id = set_enemies_map.enemy_id
                WHERE set_enemies_map.set_id = ?
            """, (set_id,))
            enemies_rows = cursor.fetchall()
            enemies = [Set.parse_obj(dict(row)) for row in enemies_rows if row is not None]

            # Fetch murders details and convert rows into dictionaries
            cursor.execute("""
                SELECT m.date,
                       shooter.name AS shooter_name,
                       shooter.id AS shooter_id,
                       victim.name AS victim_name,
                       victim_set.name AS victim_set_name,
                       victim.id AS victim_id,
                       victim.set_id AS victim_set_id
                FROM murders m
                JOIN members shooter ON m.shooter_id = shooter.id
                JOIN members victim ON m.victim_id = victim.id
                JOIN sets victim_set ON victim.set_id = victim_set.id
                WHERE shooter.set_id = ?
                ORDER BY m.date DESC
            """, (set_id,))
            murders_rows = cursor.fetchall()
            murders = [dict(row) for row in murders_rows if row is not None]

            return templates.TemplateResponse("sets/set_details.html", {
                "request": request,
                "set": set_obj.dict(),
                "members": [member.dict() for member in members],
                "allies": [ally.dict() for ally in allies],
                "enemies": [enemy.dict() for enemy in enemies],
                "murders": murders,
                "member_count": member_count,
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

