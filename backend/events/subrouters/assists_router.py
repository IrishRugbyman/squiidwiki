from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from backend.templates import templates
from backend.database import get_db
from backend.events.models import Assists
from backend.members.models import Members
from ..events_funcs import validate_member, get_events_by_type, get_victim_info, parse_date, transaction_scope

router = APIRouter()

@router.get("/{member_id}", response_class=HTMLResponse)
async def get_assists(request: Request, member_id: int, db: Session = Depends(get_db)):
    validate_member(db, member_id)
    # Instead of trying to render a non-existent template, redirect to the member details page
    return RedirectResponse(url=f"/members/{member_id}", status_code=303)

# Show form to add an assist
@router.get("/add/{member_id}", response_class=HTMLResponse)
async def show_add_assist_form(request: Request, member_id: int, db: Session = Depends(get_db)):
    validate_member(db, member_id)
    # Only show victims who are dead (have a murder record)
    all_victims = db.query(Members).join(Murders, Members.id == Murders.victim_id).filter(
        Members.id != member_id,
        Members.status == "dead"
    ).all()
    
    # Find duplicate names
    name_counts = {}
    for member in all_victims:
        name_counts[member.name] = name_counts.get(member.name, 0) + 1
    duplicate_names = {name for name, count in name_counts.items() if count > 1}
    
    all_victims_data = []
    for m in all_victims:
        # Clear death_date_approx if it's 'unknown' and member is alive (should not happen in this case, but for consistency)
        if m.status == "alive" and m.death_date_approx == "unknown":
            m.death_date_approx = None
            
        all_victims_data.append({
            "id": m.id, 
            "name": m.name,
            "set_name": m.set.name if m.set else "Unknown Set",
            "death_date": m.death_date,
            "death_date_approx": m.death_date_approx,
            "status": m.status,
            "release_date": m.release_date,
            "release_date_approx": m.release_date_approx
        })
    
    return templates.TemplateResponse("events/assists/add_assist.html", {
        "request": request,
        "event_type": "assist",
        "member_id": member_id,
        "all_members": all_victims_data,
        "duplicate_names": duplicate_names
    })

# Handle adding an assist
@router.post("/add/{member_id}", response_class=RedirectResponse)
async def add_assist(
    request: Request,
    member_id: int,
    victim_id: int = Form(...),
    assist_type: str = Form('other'),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        # Validate assist type
        valid_types = {'driver', 'spotter', 'setup', 'other'}
        if assist_type not in valid_types:
            raise HTTPException(status_code=400, detail="Invalid assist type")
            
        assistant = validate_member(db, member_id)
        victim = db.query(Members).get(victim_id)
        if not victim:
            raise HTTPException(status_code=404, detail="Victim not found")
            
        if victim.status != "dead":
            raise HTTPException(status_code=400, detail="Victim must be dead to add an assist")
            
        if assistant.id == victim.id:
            raise HTTPException(status_code=400, detail="Assistant and victim cannot be the same")

        murder = db.query(Murders).filter(Murders.victim_id == victim_id).first()
        if not murder:
            raise HTTPException(status_code=400, detail="No murder record found for victim")
            
        if murder.shooter_id == member_id:
            raise HTTPException(status_code=400, detail="Murderer cannot assist their own murder")

        # Check if assistant was alive at murder time
        validate_member(db, member_id, str(murder.date), check_alive=True)
        
        # Check if assist already exists
        existing_assist = db.query(Assists).filter(
            Assists.shooter_id == member_id,
            Assists.victim_id == victim_id
        ).first()
        
        if existing_assist:
            raise HTTPException(status_code=400, detail="This member already has an assist record for this victim")

        assist = Assists(
            shooter_id=member_id,
            victim_id=victim_id,
            date=murder.date,
            date_approx=murder.date_approx,
            assist_type=assist_type,
            notes=notes
        )

        db.add(assist)
        db.commit()
        return RedirectResponse(url=f"/members/{member_id}", status_code=303)
    except HTTPException as e:
        db.rollback()
        # For assists, we don't have date precision, so pass None for those fields
        return handle_error(request, db, member_id, "assists", victim_id, None, None, None, e)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add assist: {str(e)}")

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
    
    # Create full member data including status information
    all_members_data = []
    for m in all_members:
        # Clear death_date_approx if it's 'unknown' and member is alive
        if m.status == "alive" and m.death_date_approx == "unknown":
            m.death_date_approx = None
            
        all_members_data.append({
            "id": m.id, 
            "name": m.name,
            "set_name": m.set.name if m.set else "Unknown Set",
            "death_date": m.death_date,
            "death_date_approx": m.death_date_approx,
            "status": m.status,
            "release_date": m.release_date,
            "release_date_approx": m.release_date_approx
        })
    
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

    # Store original shooter ID for redirection
    original_shooter_id = assist.shooter_id

    # Get the murder record for validation
    murder = db.query(Murders).filter(Murders.victim_id == assist.victim_id).first()
    if not murder:
        raise HTTPException(status_code=400, detail="Associated murder not found")

    # Start transaction
    with transaction_scope(db, error_message="Failed to update assist"):
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

    # Ensure we're returning a proper 303 redirect response
    # This will force the browser to perform a GET request to the new URL
    target_url = f"/members/{assist.shooter_id}"
    return RedirectResponse(
        url=target_url, 
        status_code=303,
        headers={"Location": target_url}
    )

# Delete an assist
@router.post("/delete/{event_id}", response_class=RedirectResponse)
async def delete_assist(event_id: int, db: Session = Depends(get_db)):
    assist = db.query(Assists).get(event_id)
    if not assist:
        raise HTTPException(status_code=404, detail="Assist event not found")
    
    # Store member ID for redirection
    member_id = assist.shooter_id
    
    # Start transaction
    with transaction_scope(db, error_message="Failed to delete assist"):
        db.delete(assist)
    
    # Ensure we're returning a proper 303 redirect response
    target_url = f"/members/{member_id}"
    return RedirectResponse(
        url=target_url, 
        status_code=303,
        headers={"Location": target_url}
    )