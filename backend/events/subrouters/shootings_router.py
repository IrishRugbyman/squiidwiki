from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from backend.templates import templates
from backend.database import get_db
from backend.events.models import Shootings
from backend.members.models import Members
from ..events_funcs import validate_member, get_events_by_type, get_victim_info, parse_date, handle_error, transaction_scope

router = APIRouter()

@router.get("/{member_id}", response_class=HTMLResponse)
async def get_shootings(request: Request, member_id: int, db: Session = Depends(get_db)):
    validate_member(db, member_id)
    # Instead of trying to render a non-existent template, redirect to the member details page
    return RedirectResponse(url=f"/members/{member_id}", status_code=303)

# Show form to add a shooting
@router.get("/add/{member_id}", response_class=HTMLResponse)
async def show_add_shooting_form(request: Request, member_id: int, db: Session = Depends(get_db)):
    validate_member(db, member_id)
    all_members = db.query(Members).filter(Members.id != member_id).all()
    
    # Find duplicate names
    name_counts = {}
    for member in all_members:
        name_counts[member.name] = name_counts.get(member.name, 0) + 1
    duplicate_names = {name for name, count in name_counts.items() if count > 1}
    
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
    
    return templates.TemplateResponse("events/shootings/add_shooting.html", {
        "request": request,
        "event_type": "shooting",
        "member_id": member_id,
        "all_members": all_members_data,
        "duplicate_names": duplicate_names
    })

# Handle adding a shooting
@router.post("/add/{member_id}", response_class=RedirectResponse)
async def add_shooting(
    request: Request,
    member_id: int,
    victim_id: int = Form(...),
    date_precision: str = Form('exact'),
    date_exact: Optional[str] = Form(None),
    date_year: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        shooter = validate_member(db, member_id)
        victim = validate_member(db, victim_id)
        if shooter.id == victim.id:
            raise HTTPException(status_code=400, detail="Shooter and victim cannot be the same")

        # Handle date logic based on precision
        event_date, date_approx = parse_date(date_precision, date_exact, date_year)
        
        # Validate shooter and victim were alive at event time
        if event_date:
            validate_member(db, member_id, str(event_date), check_alive=True)
            # Check if victim was already dead
            if victim.status == "dead" and victim.death_date and event_date > victim.death_date:
                raise HTTPException(
                    status_code=400,
                    detail=f"Victim died on {victim.death_date}, cannot be shot on {event_date}"
                )
            elif (victim.status == "dead" and victim.death_date_approx and 
                  victim.death_date_approx != "unknown" and event_date.strftime("%Y") > victim.death_date_approx):
                raise HTTPException(
                    status_code=400,
                    detail=f"Victim died approximately in {victim.death_date_approx}, cannot be shot in {event_date.strftime('%Y')}"
                )

        shooting = Shootings(
            shooter_id=member_id,
            victim_id=victim_id,
            date=event_date,
            date_approx=date_approx
        )

        db.add(shooting)
        db.commit()
        return RedirectResponse(url=f"/members/{member_id}", status_code=303)
    except HTTPException as e:
        db.rollback()
        return handle_error(request, db, member_id, "shootings", victim_id, date_precision, date_exact, date_year, e)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Show form to edit a shooting
@router.get("/edit/{event_id}", response_class=HTMLResponse)
async def show_edit_shooting_form(request: Request, event_id: int, db: Session = Depends(get_db)):
    shooting = db.query(Shootings).get(event_id)
    if not shooting:
        raise HTTPException(status_code=404, detail="Shooting event not found")
    
    # Get current shooter's information
    current_shooter = db.query(Members).get(shooting.shooter_id)
    
    # Find members from the same set as the shooter, or alliance if no set
    if current_shooter.set_id:
        # Get members from the same set
        shooter_members = db.query(Members).filter(
            Members.id != shooting.victim_id,
            Members.set_id == current_shooter.set_id
        ).all()
    elif current_shooter.alliance_id:
        # Get members from the same alliance
        shooter_members = db.query(Members).filter(
            Members.id != shooting.victim_id,
            Members.alliance_id == current_shooter.alliance_id
        ).all()
    else:
        # Fallback: only include the current shooter
        shooter_members = [current_shooter]
    
    # Create full member data including status information
    shooter_members_data = []
    for m in shooter_members:
        # Clear death_date_approx if it's 'unknown' and member is alive
        if m.status == "alive" and m.death_date_approx == "unknown":
            m.death_date_approx = None
            
        shooter_members_data.append({
            "id": m.id, 
            "name": m.name,
            "set_name": m.set.name if m.set else "Unknown Set",
            "death_date": m.death_date,
            "death_date_approx": m.death_date_approx,
            "status": m.status,
            "release_date": m.release_date,
            "release_date_approx": m.release_date_approx
        })
    
    return templates.TemplateResponse("events/shootings/edit_shooting.html", {
        "request": request,
        "shooting": shooting,
        "shooter_members": shooter_members_data
    })

# Handle editing a shooting
@router.post("/edit/{event_id}", response_class=RedirectResponse)
async def edit_shooting(
    request: Request,
    event_id: int,
    shooter_id: int = Form(...),
    victim_id: int = Form(...),
    date_precision: str = Form('exact'),
    date_exact: Optional[str] = Form(None),
    date_year: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    shooting = db.query(Shootings).get(event_id)
    if not shooting:
        raise HTTPException(status_code=404, detail="Shooting event not found")

    # Store original shooter ID for redirection
    original_shooter_id = shooting.shooter_id

    # Verify victim ID matches the original event
    if shooting.victim_id != victim_id:
        raise HTTPException(status_code=400, detail="Cannot change victim for this event")

    # Get victim and validate it exists
    victim = db.query(Members).get(victim_id)
    if not victim:
        raise HTTPException(status_code=404, detail="Victim not found")

    # Start transaction
    with transaction_scope(db, error_message="Failed to update shooting"):
        # Update shooter if changed
        if shooting.shooter_id != shooter_id:
            # Validate shooter is not the victim
            if shooter_id == victim_id:
                raise HTTPException(status_code=400, detail="Shooter and victim cannot be the same person")
            
            # Validate new shooter exists
            shooter = db.query(Members).get(shooter_id)
            if not shooter:
                raise HTTPException(status_code=404, detail="Shooter not found")
                
            shooting.shooter_id = shooter_id

        # Parse and validate date based on precision
        event_date = shooting.date
        date_approx = shooting.date_approx
        
        if date_precision == 'exact' and date_exact:
            try:
                event_date = datetime.strptime(date_exact, "%Y-%m-%d").date()
                date_approx = event_date.strftime("%Y")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format (must be YYYY-MM-DD)")
        elif date_precision == 'year' and date_year:
            if not date_year.isdigit() or len(date_year) != 4:
                raise HTTPException(status_code=400, detail="Invalid year format (must be YYYY)")
            date_approx = date_year
            event_date = None
        
        # Validate shooter was alive at event time
        if event_date:
            shooter = db.query(Members).get(shooter_id)
            if shooter.status == 'dead' and shooter.death_date and event_date > shooter.death_date:
                raise HTTPException(
                    status_code=400,
                    detail=f"Shooter died on {shooter.death_date}, cannot shoot on {event_date}"
                )
            elif (shooter.status == 'dead' and shooter.death_date_approx and 
                  shooter.death_date_approx != "unknown" and date_approx > shooter.death_date_approx):
                raise HTTPException(
                    status_code=400,
                    detail=f"Shooter died approximately in {shooter.death_date_approx}, cannot shoot in {date_approx}"
                )
        
        # Validate victim was alive at event time
        if event_date and victim.status == 'dead':
            if victim.death_date and event_date > victim.death_date:
                raise HTTPException(
                    status_code=400,
                    detail=f"Victim died on {victim.death_date}, cannot be shot on {event_date}"
                )
            elif (victim.death_date_approx and victim.death_date_approx != "unknown" and 
                  date_approx > victim.death_date_approx):
                raise HTTPException(
                    status_code=400,
                    detail=f"Victim died approximately in {victim.death_date_approx}, cannot be shot in {date_approx}"
                )
        
        # Update shooting record
        if event_date != shooting.date or date_approx != shooting.date_approx:
            shooting.date = event_date
            shooting.date_approx = date_approx

    # Ensure we're returning a proper 303 redirect response
    # This will force the browser to perform a GET request to the new URL
    target_url = f"/members/{shooting.shooter_id}"
    return RedirectResponse(
        url=target_url, 
        status_code=303,
        headers={"Location": target_url}
    )

# Delete a shooting
@router.post("/delete/{event_id}", response_class=RedirectResponse)
async def delete_shooting(event_id: int, db: Session = Depends(get_db)):
    shooting = db.query(Shootings).get(event_id)
    if not shooting:
        raise HTTPException(status_code=404, detail="Shooting event not found")
    
    # Store member ID for redirection
    member_id = shooting.shooter_id
    
    # Start transaction
    with transaction_scope(db, error_message="Failed to delete shooting"):
        db.delete(shooting)
    
    # Ensure we're returning a proper 303 redirect response
    target_url = f"/members/{member_id}"
    return RedirectResponse(
        url=target_url, 
        status_code=303,
        headers={"Location": target_url}
    )