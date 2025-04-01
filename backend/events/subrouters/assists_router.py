from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from backend.config.templates import templates
from backend.database.db_alchemy_models import Members, Assists, Murders, get_db
from ..events_funcs import validate_member, get_events_by_type, get_victim_info
from typing import Optional

router = APIRouter()

@router.get("/{member_id}", response_class=HTMLResponse)
async def get_assists(request: Request, member_id: int, db: Session = Depends(get_db)):
    validate_member(db, member_id)
    assists = get_events_by_type(db, member_id, "assists")
    victim_info = get_victim_info(db, assists)
    all_members = [{"id": m.id, "name": m.name} for m in db.query(Members).filter(Members.id != member_id).all()]
    return templates.TemplateResponse("events/assists/list_assists.html", {
        "request": request,
        "events": assists,
        "event_type": "assist",
        "member_id": member_id,
        "all_members": all_members,
        **victim_info
    })

# Show form to add an assist
@router.get("/add/{member_id}", response_class=HTMLResponse)
async def show_add_assist_form(request: Request, member_id: int, db: Session = Depends(get_db)):
    validate_member(db, member_id)
    # Only show victims who are dead (have a murder record)
    all_victims = db.query(Members).join(Murders, Members.id == Murders.victim_id).filter(
        Members.id != member_id,
        Members.status == "dead"
    ).all()
    all_victims_data = [{"id": m.id, "name": m.name, "death_date": m.death_date} for m in all_victims]
    return templates.TemplateResponse("events/assists/add_assist.html", {
        "request": request,
        "event_type": "assist",
        "member_id": member_id,
        "all_victims": all_victims_data
    })

# Handle adding an assist
@router.post("/add/{member_id}", response_class=RedirectResponse)
async def add_assist(
    request: Request,
    member_id: int,
    victim_id: int = Form(...),
    db: Session = Depends(get_db)
):
    assistant = validate_member(db, member_id)
    victim = db.query(Members).get(victim_id)
    if not victim or victim.status != "dead":
        raise HTTPException(status_code=400, detail="Victim must be dead to add an assist")
    if assistant.id == victim.id:
        raise HTTPException(status_code=400, detail="Assistant and victim cannot be the same")

    murder = db.query(Murders).filter(Murders.victim_id == victim_id).first()
    if not murder:
        raise HTTPException(status_code=400, detail="No murder record found for victim")
    if murder.shooter_id == member_id:
        raise HTTPException(status_code=400, detail="Murderer cannot assist their own murder")

    validate_member(db, member_id, str(murder.date), check_alive=True)
    assist = Assists(
        shooter_id=member_id,
        victim_id=victim_id,
        date=murder.date,
        date_approx=murder.date_approx
    )

    try:
        db.add(assist)
        db.commit()
        return RedirectResponse(url=f"/members/{member_id}", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Show form to edit an assist
@router.get("/edit/{event_id}", response_class=HTMLResponse)
async def show_edit_assist_form(request: Request, event_id: int, db: Session = Depends(get_db)):
    assist = db.query(Assists).get(event_id)
    if not assist:
        raise HTTPException(status_code=404, detail="Assist event not found")
    
    # Get the murder record
    murder = db.query(Murders).filter(Murders.victim_id == assist.victim_id).first()
    if not murder:
        raise HTTPException(status_code=400, detail="Associated murder not found")
    
    # Get current shooter's information
    current_shooter = db.query(Members).get(assist.shooter_id)
    
    # Find members from the same set as the shooter, or alliance if no set
    if current_shooter.set_id:
        # Get members from the same set
        all_members = db.query(Members).filter(
            Members.id != assist.victim_id,
            Members.id != murder.shooter_id,
            Members.set_id == current_shooter.set_id
        ).all()
    elif current_shooter.alliance_id:
        # Get members from the same alliance
        all_members = db.query(Members).filter(
            Members.id != assist.victim_id,
            Members.id != murder.shooter_id,
            Members.alliance_id == current_shooter.alliance_id
        ).all()
    else:
        # Fallback: only include the current shooter
        all_members = [current_shooter]
    
    all_members_data = [{"id": m.id, "name": m.name} for m in all_members]
    
    return templates.TemplateResponse("events/assists/edit_assist.html", {
        "request": request,
        "assist": assist,
        "all_members": all_members_data
    })

# Handle editing an assist
@router.post("/edit/{event_id}", response_class=RedirectResponse)
async def edit_assist(
    request: Request,
    event_id: int,
    shooter_id: int = Form(...),
    assist_type: str = Form(...),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    assist = db.query(Assists).get(event_id)
    if not assist:
        raise HTTPException(status_code=404, detail="Assist event not found")

    # Get the murder record for validation
    murder = db.query(Murders).filter(Murders.victim_id == assist.victim_id).first()
    if not murder:
        raise HTTPException(status_code=400, detail="Associated murder not found")

    # Validate assist type
    valid_types = {'driver', 'spotter', 'setup', 'other'}
    if assist_type not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid assist type")

    # Update shooter if changed
    if assist.shooter_id != shooter_id:
        # Validate shooter is not the victim
        if shooter_id == assist.victim_id:
            raise HTTPException(status_code=400, detail="Shooter and victim cannot be the same person")
        
        # Validate shooter is not the murderer
        if murder.shooter_id == shooter_id:
            raise HTTPException(status_code=400, detail="Murderer cannot assist their own murder")
        
        # Validate shooter was alive at murder time
        validate_member(db, shooter_id, str(murder.date), check_alive=True)
        
        assist.shooter_id = shooter_id

    # Update assist type and notes
    assist.assist_type = assist_type
    assist.notes = notes

    try:
        db.commit()
        return RedirectResponse(url=f"/members/{assist.shooter_id}", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Delete an assist
@router.post("/delete/{event_id}", response_class=RedirectResponse)
async def delete_assist(event_id: int, db: Session = Depends(get_db)):
    assist = db.query(Assists).get(event_id)
    if not assist:
        raise HTTPException(status_code=404, detail="Assist event not found")
    member_id = assist.shooter_id
    try:
        db.delete(assist)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    return RedirectResponse(url=f"/members/{member_id}", status_code=303)