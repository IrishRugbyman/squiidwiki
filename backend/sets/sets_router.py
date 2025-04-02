from fastapi import APIRouter, Request, Form, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from backend.config.templates import templates
from typing import Optional
from backend.database.db_alchemy_models import get_db  # get_db now yields a SQLAlchemy session
from backend.database.enums import eSetType
from sqlalchemy.orm import Session
from backend.database.db_alchemy_models import (
    Sets, Members, Config, SetAlliesMap, SetEnemiesMap,
    Murders, Shootings, Assists, AllianceSetsMap, Alliances
)
from backend.sets.sets_funcs import group_sets, process_relations, get_special_set_id

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    # Query all sets via ORM.
    sets_list = db.query(Sets).all()
    grouped = group_sets(sets_list, db)
    sorted_groups = sorted(grouped.items(), key=lambda x: x[0])
    sorted_grouped_sets = {char: sorted(group, key=lambda s: s.name) for char, group in sorted_groups}
    # Convert ORM models to dictionaries for the template.
    grouped_dict = {
        char: [{"id": s.id, "name": s.name, "description": s.description, "type": s.type, "emoji": s.emoji}
               for s in group]
        for char, group in sorted_grouped_sets.items()
    }
    return templates.TemplateResponse("sets/index.html", {
        "request": request,
        "grouped_sets": grouped_dict
    })


@router.get("/add", response_class=HTMLResponse)
def add_set_form(request: Request):
    return templates.TemplateResponse("sets/add_set.html", {"request": request})


@router.post("/add", response_class=RedirectResponse)
def add_set(
        name: str = Form(...),
        description: Optional[str] = Form(None),
        allies: Optional[str] = Form(None),
        enemies: Optional[str] = Form(None),
        is_extinct: bool = Form(False),
        emoji: Optional[str] = Form(None),
        db: Session = Depends(get_db)
):
    # Validate allies and enemies.
    ally_list = [n.strip() for n in allies.split(",") if n.strip()] if allies else []
    enemy_list = [n.strip() for n in enemies.split(",") if n.strip()] if enemies else []
    if name in ally_list or name in enemy_list:
        raise HTTPException(status_code=400, detail="A set cannot be its own ally or enemy.")
    if set(ally_list).intersection(set(enemy_list)):
        raise HTTPException(status_code=400, detail="A set cannot be both an ally and enemy of the same set.")

    # Determine the set type.
    set_type = eSetType.EXTINCT if is_extinct else eSetType.ACTIVE
    # Create a new set via ORM.
    new_set = Sets(name=name, description=description,
                   type=(set_type.value if hasattr(set_type, 'value') else set_type),
                   emoji=emoji)
    db.add(new_set)
    db.commit()
    db.refresh(new_set)

    # Process ally and enemy relations.
    process_relations(db, new_set.id, allies, SetAlliesMap)
    process_relations(db, new_set.id, enemies, SetEnemiesMap)
    db.commit()
    return RedirectResponse(url="/sets/", status_code=303)


@router.get("/set_options", response_class=JSONResponse)
def set_options(exclude: Optional[int] = Query(None), db: Session = Depends(get_db)):
    # Retrieve default set IDs from the Config table.
    default_configs = db.query(Config).filter(Config.key.in_(["unknown_set_id", "civilian_set_id"])).all()
    default_ids = [c.value for c in default_configs]
    query = db.query(Sets)
    if exclude:
        query = query.filter(Sets.id != exclude)
    if default_ids:
        query = query.filter(~Sets.id.in_(default_ids))
    options = query.all()
    options_list = [{"id": opt.id, "name": opt.name} for opt in options]
    return JSONResponse(content=options_list)


@router.get("/edit/{set_id}", response_class=HTMLResponse)
def edit_set_form(request: Request, set_id: int, db: Session = Depends(get_db)):
    set_obj = db.query(Sets).filter(Sets.id == set_id).first()
    if not set_obj:
        raise HTTPException(status_code=404, detail="Set not found")
    # Check if the set is a system/default set.
    special_configs = db.query(Config).filter(Config.key.in_(["unknown_set_id", "civilian_set_id"])).all()
    special_ids = [c.value for c in special_configs]
    is_default_set = set_id in special_ids

    # Retrieve allies and enemies via the mapping tables.
    allies_relations = db.query(SetAlliesMap).filter(SetAlliesMap.set_id == set_id).all()
    allies = [db.query(Sets).filter(Sets.id == rel.ally_id).first().name for rel in allies_relations if
              db.query(Sets).filter(Sets.id == rel.ally_id).first()]
    enemies_relations = db.query(SetEnemiesMap).filter(SetEnemiesMap.set_id == set_id).all()
    enemies = [db.query(Sets).filter(Sets.id == rel.enemy_id).first().name for rel in enemies_relations if
               db.query(Sets).filter(Sets.id == rel.enemy_id).first()]

    set_dict = {"id": set_obj.id, "name": set_obj.name, "description": set_obj.description, "type": set_obj.type, "emoji": set_obj.emoji}
    return templates.TemplateResponse("sets/edit_set.html", {
        "request": request,
        "set": set_dict,
        "allies": ", ".join(allies),
        "enemies": ", ".join(enemies),
        "is_default_set": is_default_set
    })


@router.post("/edit/{set_id}", response_class=RedirectResponse)
def edit_set(
        set_id: int,
        name: str = Form(...),
        description: Optional[str] = Form(None),
        allies: Optional[str] = Form(None),
        enemies: Optional[str] = Form(None),
        is_extinct: bool = Form(False),
        emoji: Optional[str] = Form(None),
        db: Session = Depends(get_db)
):
    special_configs = db.query(Config).filter(Config.key.in_(["unknown_set_id", "civilian_set_id"])).all()
    special_ids = [c.value for c in special_configs]
    if set_id in special_ids:
        raise HTTPException(
            status_code=303,
            detail="System sets cannot be modified",
            headers={"Location": f"/sets/{set_id}?error=system_set"}
        )
    set_obj = db.query(Sets).filter(Sets.id == set_id).first()
    if not set_obj:
        raise HTTPException(status_code=404, detail="Set not found")

    current_name = set_obj.name
    ally_list = [n.strip() for n in allies.split(",")] if allies else []
    enemy_list = [n.strip() for n in enemies.split(",")] if enemies else []

    if current_name in ally_list or current_name in enemy_list:
        raise HTTPException(status_code=400, detail="A set cannot be its own ally or enemy.")
    if set(ally_list).intersection(set(enemy_list)):
        raise HTTPException(status_code=400, detail="A set cannot be both an ally and enemy of the same set.")

    set_type = eSetType.EXTINCT if is_extinct else eSetType.ACTIVE
    # Update fields via ORM.
    set_obj.name = name
    set_obj.description = description
    set_obj.type = (set_type.value if hasattr(set_type, 'value') else set_type)
    set_obj.emoji = emoji
    db.commit()
    process_relations(db, set_id, allies, SetAlliesMap)
    process_relations(db, set_id, enemies, SetEnemiesMap)
    db.commit()
    return RedirectResponse(url=f"/sets/{set_id}", status_code=303)


@router.get("/delete/{set_id}", response_class=HTMLResponse)
def delete_set_confirmation(request: Request, set_id: int, db: Session = Depends(get_db)):
    special_configs = db.query(Config).filter(Config.key.in_(["unknown_set_id", "civilian_set_id"])).all()
    special_ids = [c.value for c in special_configs]
    if set_id in special_ids:
        return RedirectResponse(url=f"/sets/{set_id}?error=Cannot delete system sets")
    set_obj = db.query(Sets).filter(Sets.id == set_id).first()
    if not set_obj:
        raise HTTPException(status_code=404, detail="Set not found")
    member_count = db.query(Members).filter(Members.set_id == set_id).count()
    special_set_id = get_special_set_id(db, 'unknown')
    set_dict = {"id": set_obj.id, "name": set_obj.name, "description": set_obj.description, "type": set_obj.type}
    return templates.TemplateResponse("sets/delete_set.html", {
        "request": request,
        "set": set_dict,
        "member_count": member_count,
        "special_set_id": special_set_id
    })


@router.post("/delete/{set_id}", response_class=RedirectResponse)
def delete_set(
        request: Request,
        set_id: int,
        member_action: str = Form(...),
        target_set: Optional[int] = Form(None),
        db: Session = Depends(get_db)
):
    set_obj = db.query(Sets).filter(Sets.id == set_id).first()
    if not set_obj:
        raise HTTPException(status_code=404, detail="Set not found")
    if member_action == "move":
        if not target_set:
            raise HTTPException(status_code=400, detail="Target set required for member transfer")
        target = db.query(Sets).filter(Sets.id == target_set).first()
        if not target:
            raise HTTPException(status_code=400, detail="Invalid destination set")
        db.query(Members).filter(Members.set_id == set_id).update({"set_id": target_set})
    elif member_action == "delete":
        # Delete incidents (assists, shootings, murders) for members in this set.
        members_ids = [m.id for m in db.query(Members).filter(Members.set_id == set_id).all()]
        if members_ids:
            db.query(Assists).filter(Assists.shooter_id.in_(members_ids) | Assists.victim_id.in_(members_ids)).delete(
                synchronize_session=False)
            db.query(Shootings).filter(
                Shootings.shooter_id.in_(members_ids) | Shootings.victim_id.in_(members_ids)).delete(
                synchronize_session=False)
            db.query(Murders).filter(Murders.shooter_id.in_(members_ids) | Murders.victim_id.in_(members_ids)).delete(
                synchronize_session=False)
        db.query(Members).filter(Members.set_id == set_id).delete(synchronize_session=False)
    db.query(SetAlliesMap).filter((SetAlliesMap.set_id == set_id) | (SetAlliesMap.ally_id == set_id)).delete(
        synchronize_session=False)
    db.query(SetEnemiesMap).filter((SetEnemiesMap.set_id == set_id) | (SetEnemiesMap.enemy_id == set_id)).delete(
        synchronize_session=False)
    db.delete(set_obj)
    db.commit()
    return RedirectResponse(url="/sets/", status_code=303)


@router.get("/{set_id}", response_class=HTMLResponse)
def read_set(request: Request, set_id: int, db: Session = Depends(get_db)):
    set_obj = db.query(Sets).filter(Sets.id == set_id).first()
    if not set_obj:
        raise HTTPException(status_code=404, detail="Set not found")
    set_dict = {"id": set_obj.id, "name": set_obj.name, "description": set_obj.description, "type": set_obj.type, "emoji": set_obj.emoji}
    member_count = db.query(Members).filter(Members.set_id == set_id).count()
    members = db.query(Members).filter(Members.set_id == set_id).all()
    members_list = [{
        "id": m.id,
        "name": m.name,
        "description": m.description,
        "status": m.status,
        "release_date": m.release_date,
        "release_date_approx": m.release_date_approx,
        "death_date": m.death_date,
        "death_date_approx": m.death_date_approx,
        "set_id": m.set_id,
        "alliance_id": m.alliance_id
    } for m in members]

    # Fetch alliances this set belongs to
    alliance_maps = db.query(AllianceSetsMap).filter(AllianceSetsMap.set_id == set_id).all()
    alliances = []
    for map_obj in alliance_maps:
        alliance = db.get(Alliances, map_obj.alliance_id)
        if alliance:
            alliances.append({
                "id": alliance.id,
                "name": alliance.name,
                "status": alliance.status
            })

    # Fetch allies (union from both directions)
    allies_rel1 = db.query(SetAlliesMap).filter(SetAlliesMap.set_id == set_id).all()
    allies_rel2 = db.query(SetAlliesMap).filter(SetAlliesMap.ally_id == set_id).all()
    allies_set = set()
    for rel in allies_rel1:
        ally = db.query(Sets).filter(Sets.id == rel.ally_id).first()
        if ally:
            allies_set.add(ally)
    for rel in allies_rel2:
        ally = db.query(Sets).filter(Sets.id == rel.set_id).first()
        if ally:
            allies_set.add(ally)
    allies = [{"id": a.id, "name": a.name, "description": a.description, "type": a.type} for a in allies_set]

    # Fetch enemies (union from both directions)
    enemies_rel1 = db.query(SetEnemiesMap).filter(SetEnemiesMap.set_id == set_id).all()
    enemies_rel2 = db.query(SetEnemiesMap).filter(SetEnemiesMap.enemy_id == set_id).all()
    enemies_set = set()
    for rel in enemies_rel1:
        enemy = db.query(Sets).filter(Sets.id == rel.enemy_id).first()
        if enemy:
            enemies_set.add(enemy)
    for rel in enemies_rel2:
        enemy = db.query(Sets).filter(Sets.id == rel.set_id).first()
        if enemy:
            enemies_set.add(enemy)
    enemies = [{"id": a.id, "name": a.name, "description": a.description, "type": a.type} for a in enemies_set]

    # Fetch murders details using ORM relationships.
    murders_query = db.query(Murders).join(Members, Murders.shooter_id == Members.id).filter(
        Members.set_id == set_id).order_by(Murders.date.desc())
    murders = []
    for murder in murders_query.all():
        murders.append({
            "date": murder.date,
            "shooter_name": murder.shooter.name,
            "shooter_id": murder.shooter.id,
            "victim_name": murder.victim.name,
            "victim_set_name": murder.victim.set.name if murder.victim.set else None,
            "victim_id": murder.victim.id,
            "victim_set_id": murder.victim.set.id if murder.victim.set else None
        })

    return templates.TemplateResponse("sets/set_details.html", {
        "request": request,
        "set": set_dict,
        "members": members_list,
        "allies": allies,
        "enemies": enemies,
        "murders": murders,
        "member_count": member_count,
        "alliances": alliances
    })


@router.get("/check_name", response_class=JSONResponse)
def check_name(name: str, exclude_id: Optional[int] = None, db: Session = Depends(get_db)):
    # Check if a set with this name already exists
    query = db.query(Sets).filter(Sets.name == name)
    if exclude_id:
        query = query.filter(Sets.id != exclude_id)
    existing_set = query.first()
    
    return JSONResponse(content={
        "available": existing_set is None,
        "message": "Name is available" if existing_set is None else "A set with this name already exists"
    })
