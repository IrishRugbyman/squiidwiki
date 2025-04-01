from typing import List, Optional

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from backend.config.templates import templates
from backend.database.models import AllianceCreate, AllianceOption
from backend.database.db_alchemy_models import Alliances, AllianceSetsMap, Sets, Members, get_db

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def read_alliances(request: Request, db: Session = Depends(get_db)):
    alliances = db.query(Alliances).all()
    # Convert ORM objects to dicts for templating.
    alliances_data = [
        {
            "id": alliance.id,
            "name": alliance.name,
            "description": alliance.description,
            "status": alliance.status,
        }
        for alliance in alliances
    ]
    return templates.TemplateResponse("alliances/index.html", {"request": request, "alliances": alliances_data})


@router.get("/add", response_class=HTMLResponse)
def add_alliance_form(request: Request):
    return templates.TemplateResponse("alliances/add_alliance.html", {"request": request})


@router.post("/add", response_class=RedirectResponse)
def add_alliance(
        name: str = Form(...),
        description: Optional[str] = Form(None),
        status: str = Form(...),
        db: Session = Depends(get_db)
):
    new_alliance = Alliances(
        name=name,
        description=description,
        status=status,
    )
    db.add(new_alliance)
    db.commit()
    return RedirectResponse(url="/alliances", status_code=303)


@router.get("/add_member/{alliance_id}", response_class=HTMLResponse)
def add_member_form(request: Request, alliance_id: int, db: Session = Depends(get_db)):
    alliance = db.get(Alliances, alliance_id)
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")

    # Get the set IDs already associated with this alliance.
    existing_set_ids = [mapping.set_id for mapping in alliance.alliance_sets_map]
    # Query for available sets (those not yet in the alliance)
    available_sets = db.query(Sets).filter(~Sets.id.in_(existing_set_ids)).all()
    available_sets_data = [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "type": s.type,
        }
        for s in available_sets
    ]
    alliance_data = {
        "id": alliance.id,
        "name": alliance.name,
        "description": alliance.description,
        "status": alliance.status,
    }
    return templates.TemplateResponse(
        "alliances/add_alliance_member.html",
        {"request": request, "alliance": alliance_data, "available_sets": available_sets_data},
    )


@router.post("/add_member/{alliance_id}")
def add_member(
        alliance_id: int, set_id: int = Form(...), db: Session = Depends(get_db)
):
    set_obj = db.get(Sets, set_id)
    if not set_obj:
        raise HTTPException(status_code=400, detail="Invalid set ID")

    new_mapping = AllianceSetsMap(alliance_id=alliance_id, set_id=set_id)
    db.add(new_mapping)
    db.commit()
    return RedirectResponse(url=f"/alliances/{alliance_id}", status_code=303)


@router.get("/options", response_model=List[AllianceOption])
def get_alliance_options(db: Session = Depends(get_db)):
    """
    Returns a list of active alliances.
    Each alliance is represented as a dictionary with keys 'id' and 'name'.
    """
    alliances = db.query(Alliances).filter(Alliances.status == "active").all()
    return [AllianceOption(id=alliance.id, name=alliance.name) for alliance in alliances]


@router.get("/{alliance_id}", response_class=HTMLResponse)
def read_alliance(request: Request, alliance_id: int, db: Session = Depends(get_db)):
    alliance = db.get(Alliances, alliance_id)
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")

    alliance_data = {
        "id": alliance.id,
        "name": alliance.name,
        "description": alliance.description,
        "status": alliance.status,
    }
    # Retrieve sets associated with this alliance via the mapping relationship.
    member_sets = [mapping.set for mapping in alliance.alliance_sets_map]
    member_sets_data = [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "type": s.type,
        }
        for s in member_sets
    ]
    
    # Get human members directly associated with the alliance
    direct_members = db.query(Members).filter(Members.alliance_id == alliance_id).all()
    
    # Get all members who belong to any set in this alliance
    set_ids = [s.id for s in member_sets]
    set_members = []
    if set_ids:
        set_members = db.query(Members).filter(Members.set_id.in_(set_ids)).filter(Members.alliance_id != alliance_id).all()
    
    # Combine and format member data
    human_members_data = []
    
    for member in direct_members:
        member_data = {
            "id": member.id,
            "name": member.name,
            "status": member.status,
            "set_id": member.set_id,
            "set_name": member.set.name if member.set else None,
            "membership_type": "direct"
        }
        human_members_data.append(member_data)
    
    for member in set_members:
        member_data = {
            "id": member.id,
            "name": member.name,
            "status": member.status,
            "set_id": member.set_id,
            "set_name": member.set.name if member.set else None,
            "membership_type": "through_set"
        }
        human_members_data.append(member_data)
    
    return templates.TemplateResponse(
        "alliances/alliance_details.html",
        {
            "request": request, 
            "alliance": alliance_data, 
            "member_sets": member_sets_data,
            "human_members": human_members_data
        },
    )


@router.get("/edit/{alliance_id}", response_class=HTMLResponse)
def edit_alliance_form(request: Request, alliance_id: int, db: Session = Depends(get_db)):
    alliance = db.get(Alliances, alliance_id)
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")

    alliance_data = {
        "id": alliance.id,
        "name": alliance.name,
        "description": alliance.description,
        "status": alliance.status,
    }
    return templates.TemplateResponse(
        "alliances/edit_alliance.html",
        {"request": request, "alliance": alliance_data},
    )


@router.post("/edit/{alliance_id}", response_class=RedirectResponse)
def edit_alliance(
    alliance_id: int,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    alliance = db.get(Alliances, alliance_id)
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")

    # Update alliance fields
    alliance.name = name
    alliance.description = description
    alliance.status = status
    db.commit()

    return RedirectResponse(url=f"/alliances/{alliance_id}", status_code=303)


@router.post("/delete/{alliance_id}", response_class=RedirectResponse)
def delete_alliance(alliance_id: int, db: Session = Depends(get_db)):
    alliance = db.get(Alliances, alliance_id)
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")
    db.delete(alliance)
    db.commit()
    return RedirectResponse(url="/alliances", status_code=303)


@router.get("/delete/{alliance_id}", response_class=HTMLResponse)
def delete_alliance_confirmation(request: Request, alliance_id: int, db: Session = Depends(get_db)):
    alliance = db.get(Alliances, alliance_id)
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")

    alliance_data = {
        "id": alliance.id,
        "name": alliance.name,
        "description": alliance.description,
        "status": alliance.status,
    }

    # Get member sets count
    member_sets_count = len(alliance.alliance_sets_map)

    return templates.TemplateResponse(
        "alliances/delete_alliance.html",
        {
            "request": request,
            "alliance": alliance_data,
            "member_sets_count": member_sets_count
        }
    )


@router.post("/remove_member/{alliance_id}/{set_id}", response_class=RedirectResponse)
def remove_alliance_member(
    alliance_id: int,
    set_id: int,
    db: Session = Depends(get_db)
):
    # Find the mapping entry
    mapping = db.query(AllianceSetsMap).filter(
        AllianceSetsMap.alliance_id == alliance_id,
        AllianceSetsMap.set_id == set_id
    ).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail="Member set not found in alliance")
    
    # Remove the mapping
    db.delete(mapping)
    db.commit()
    
    return RedirectResponse(url=f"/alliances/{alliance_id}", status_code=303)
