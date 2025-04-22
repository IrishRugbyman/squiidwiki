from fastapi import APIRouter, Request, Form, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from backend.config.templates import templates
from typing import Optional, List
from backend.database.imports import get_db, Sets, Members, Config, SetAlliesMap, SetEnemiesMap, Murders, Shootings, Assists, Alliance, AllianceSetsMap
from backend.database.enums import eSetType
from sqlalchemy.orm import Session
from backend.sets.service.sets_service import group_sets, process_relations, get_special_set_id

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
def add_set_form(request: Request, db: Session = Depends(get_db)):
    # Get all available alliances for selection
    available_alliances = db.query(Alliance).filter(Alliance.status == "active").all()
    available_alliances_data = [
        {
            "id": a.id, 
            "name": a.name
        } 
        for a in available_alliances
    ]
    
    return templates.TemplateResponse("sets/add_set.html", {
        "request": request,
        "available_alliances": available_alliances_data
    })


@router.post("/add", response_class=RedirectResponse)
def add_set(
        name: str = Form(...),
        description: Optional[str] = Form(None),
        allies: Optional[str] = Form(None),
        enemies: Optional[str] = Form(None),
        alliance_names: Optional[str] = Form(None),
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
    
    # Process alliance associations if provided
    if alliance_names:
        alliance_name_list = [n.strip() for n in alliance_names.split(",") if n.strip()]
        if alliance_name_list:
            alliances = db.query(Alliance).filter(Alliance.name.in_(alliance_name_list)).all()
            for alliance in alliances:
                alliance_mapping = AllianceSetsMap(alliance_id=alliance.id, set_id=new_set.id)
                db.add(alliance_mapping)
    
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
    
    # Get alliances this set belongs to
    alliance_mappings = db.query(AllianceSetsMap).filter(AllianceSetsMap.set_id == set_id).all()
    current_alliance_ids = [mapping.alliance_id for mapping in alliance_mappings]
    
    # Get alliance names for the current set's alliances
    alliance_names = []
    if current_alliance_ids:
        current_alliances = db.query(Alliance).filter(Alliance.id.in_(current_alliance_ids)).all()
        alliance_names = [alliance.name for alliance in current_alliances]
    
    # Get all available alliances for selection
    available_alliances = db.query(Alliance).filter(Alliance.status == "active").all()
    available_alliances_data = [
        {
            "id": a.id, 
            "name": a.name
        } 
        for a in available_alliances
    ]

    set_dict = {"id": set_obj.id, "name": set_obj.name, "description": set_obj.description, "type": set_obj.type, "emoji": set_obj.emoji}
    return templates.TemplateResponse("sets/edit_set.html", {
        "request": request,
        "set": set_dict,
        "allies": ", ".join(allies),
        "enemies": ", ".join(enemies),
        "is_default_set": is_default_set,
        "available_alliances": available_alliances_data,
        "current_alliance_ids": current_alliance_ids,
        "alliance_names": ", ".join(alliance_names)
    })


@router.post("/edit/{set_id}", response_class=RedirectResponse)
def edit_set(
        set_id: int,
        name: str = Form(...),
        description: Optional[str] = Form(None),
        allies: Optional[str] = Form(None),
        enemies: Optional[str] = Form(None),
        alliance_names: Optional[str] = Form(None),
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
    
    # Process ally and enemy relations
    process_relations(db, set_id, allies, SetAlliesMap)
    process_relations(db, set_id, enemies, SetEnemiesMap)
    
    # Update alliance associations
    # First, remove all existing alliance mappings for this set
    db.query(AllianceSetsMap).filter(AllianceSetsMap.set_id == set_id).delete()
    
    # Then add the new alliance mappings
    if alliance_names:
        alliance_name_list = [n.strip() for n in alliance_names.split(",") if n.strip()]
        if alliance_name_list:
            alliances = db.query(Alliance).filter(Alliance.name.in_(alliance_name_list)).all()
            for alliance in alliances:
                alliance_mapping = AllianceSetsMap(alliance_id=alliance.id, set_id=set_id)
                db.add(alliance_mapping)
    
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
    
    # Change the set representation to a tuple format as expected by the template
    set_data = (set_obj.id, set_obj.name, set_obj.description, set_obj.type)
    
    # Get available sets for member transfer
    available_sets = db.query(Sets).filter(Sets.id != set_id).all()
    available_sets_data = [
        {"id": s.id, "name": s.name}
        for s in available_sets if s.id not in special_ids
    ]
    
    return templates.TemplateResponse("sets/delete_set.html", {
        "request": request,
        "set": set_data,
        "member_count": member_count,
        "special_set_id": special_set_id,
        "available_sets": available_sets_data
    })


@router.post("/delete/{set_id}", response_class=RedirectResponse)
def delete_set(
        request: Request,
        set_id: int,
        member_action: str = Form(...),
        target_set: Optional[int] = Form(None),
        db: Session = Depends(get_db)
):
    special_configs = db.query(Config).filter(Config.key.in_(["unknown_set_id", "civilian_set_id"])).all()
    special_ids = [c.value for c in special_configs]
    if set_id in special_ids:
        return RedirectResponse(url=f"/sets/{set_id}?error=Cannot delete system sets")
    
    set_obj = db.query(Sets).filter(Sets.id == set_id).first()
    if not set_obj:
        raise HTTPException(status_code=404, detail="Set not found")
    
    # Handle associated members
    if member_action == "transfer" and target_set:
        # Transfer members to the target set
        db.query(Members).filter(Members.set_id == set_id).update({"set_id": target_set})
    elif member_action == "delete":
        # Delete all members of this set
        db.query(Members).filter(Members.set_id == set_id).delete()
    else:
        # Default: move to unknown set
        unknown_set_id = get_special_set_id(db, 'unknown')
        db.query(Members).filter(Members.set_id == set_id).update({"set_id": unknown_set_id})
    
    # Delete all relations
    db.query(SetAlliesMap).filter(SetAlliesMap.set_id == set_id).delete()
    db.query(SetAlliesMap).filter(SetAlliesMap.ally_id == set_id).delete()
    db.query(SetEnemiesMap).filter(SetEnemiesMap.set_id == set_id).delete()
    db.query(SetEnemiesMap).filter(SetEnemiesMap.enemy_id == set_id).delete()
    
    # Delete the set from alliance mappings
    db.query(AllianceSetsMap).filter(AllianceSetsMap.set_id == set_id).delete()
    
    # Finally, delete the set itself
    db.query(Sets).filter(Sets.id == set_id).delete()
    db.commit()
    
    return RedirectResponse(url="/sets/", status_code=303)


@router.get("/{set_id}", response_class=HTMLResponse)
def read_set(request: Request, set_id: int, db: Session = Depends(get_db)):
    set_obj = db.query(Sets).filter(Sets.id == set_id).first()
    if not set_obj:
        raise HTTPException(status_code=404, detail="Set not found")
    
    # Convert the ORM model to a dictionary for the template
    set_dict = {
        "id": set_obj.id,
        "name": set_obj.name,
        "description": set_obj.description,
        "type": set_obj.type,
        "emoji": set_obj.emoji
    }
    
    # Get members of this set
    members = db.query(Members).filter(Members.set_id == set_id).order_by(Members.name).all()
    members_list = [
        {
            "id": m.id,
            "name": m.name,
            "description": m.description,
            "status": m.status
        }
        for m in members
    ]
    
    # Get all alliances this set is part of
    alliance_mappings = db.query(AllianceSetsMap).filter(AllianceSetsMap.set_id == set_id).all()
    alliance_ids = [m.alliance_id for m in alliance_mappings]
    alliances = db.query(Alliance).filter(Alliance.id.in_(alliance_ids)).all() if alliance_ids else []
    alliances_list = [
        {
            "id": a.id,
            "name": a.name,
            "description": a.description
        }
        for a in alliances
    ]
    
    # Get allies and enemies
    ally_maps = db.query(SetAlliesMap).filter(SetAlliesMap.set_id == set_id).all()
    ally_ids = [a.ally_id for a in ally_maps]
    allies = db.query(Sets).filter(Sets.id.in_(ally_ids)).order_by(Sets.name).all() if ally_ids else []
    allies_list = [
        {
            "id": a.id,
            "name": a.name,
            "description": a.description,
            "type": a.type
        }
        for a in allies
    ]
    
    enemy_maps = db.query(SetEnemiesMap).filter(SetEnemiesMap.set_id == set_id).all()
    enemy_ids = [e.enemy_id for e in enemy_maps]
    enemies = db.query(Sets).filter(Sets.id.in_(enemy_ids)).order_by(Sets.name).all() if enemy_ids else []
    enemies_list = [
        {
            "id": e.id,
            "name": e.name,
            "description": e.description,
            "type": e.type
        }
        for e in enemies
    ]
    
    # Check if this is a system set
    special_configs = db.query(Config).filter(Config.key.in_(["unknown_set_id", "civilian_set_id"])).all()
    special_ids = [c.value for c in special_configs]
    is_default_set = set_id in special_ids
    
    return templates.TemplateResponse("sets/set_details.html", {
        "request": request,
        "set": set_dict,
        "members": members_list,
        "alliances": alliances_list,
        "allies": allies_list,
        "enemies": enemies_list,
        "is_default_set": is_default_set
    })


@router.get("/check_name", response_class=JSONResponse)
def check_name(name: str, exclude_id: Optional[int] = None, db: Session = Depends(get_db)):
    # Check if a set with this name already exists
    query = db.query(Sets).filter(Sets.name == name)
    if exclude_id:
        query = query.filter(Sets.id != exclude_id)
    existing_set = query.first()
    return {"exists": existing_set is not None} 