from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from backend.config.templates import templates
from backend.database import get_db
from backend.events.models import Murders, Assists
from backend.members.models import Members
from ..events_funcs import validate_member, get_events_by_type, get_victim_info, parse_date, transaction_scope

router = APIRouter()

@router.get("/{member_id}", response_class=HTMLResponse)
async def get_murders(request: Request, member_id: int, db: Session = Depends(get_db)):
    """Display a list of murders for a member."""
    validate_member(db, member_id)
    # Instead of trying to render a non-existent template, redirect to the member details page
    return RedirectResponse(url=f"/members/{member_id}", status_code=303)

@router.get("/add/{member_id}", response_class=HTMLResponse)
async def show_add_murder_form(request: Request, member_id: int, db: Session = Depends(get_db)):
    validate_member(db, member_id)
    # Show members without murder records as victims
    all_members = db.query(Members).outerjoin(Murders, Members.id == Murders.victim_id).filter(
        Members.id != member_id, Murders.id == None
    ).all()
    
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
    
    return templates.TemplateResponse("events/murders/add_murder.html", {
        "request": request,
        "event_type": "murder",
        "member_id": member_id,
        "all_members": all_members_data,
        "duplicate_names": duplicate_names
    })

@router.post("/add/{member_id}", response_class=RedirectResponse)
async def add_murder(
        request: Request,
        member_id: int,
        victim_id: int = Form(...),
        date_precision: str = Form('keep'),
        date_exact: Optional[str] = Form(None),
        date_year: Optional[str] = Form(None),
        update_victim_death: bool = Form(False),
        db: Session = Depends(get_db)
):
    # Check if victim already has a murder record
    existing_murder = db.query(Murders).filter(Murders.victim_id == victim_id).first()
    if existing_murder:
        raise HTTPException(status_code=400, detail="Victim already has a murder record")

    shooter = validate_member(db, member_id)
    victim = validate_member(db, victim_id)

    # Handle date logic based on precision
    if date_precision == "keep":
        if victim.status != "dead":
            raise HTTPException(status_code=400, detail="Cannot keep death date for a living victim")
        event_date = victim.death_date
        date_approx = victim.death_date_approx or (event_date.strftime("%Y") if event_date else "unknown")
    else:
        event_date, date_approx = parse_date(date_precision, date_exact, date_year)

    # Validate shooter was alive at event time
    if shooter.status == 'dead':
        if event_date and shooter.death_date and event_date > shooter.death_date:
            raise HTTPException(
                status_code=400,
                detail=f"Shooter died on {shooter.death_date}, cannot commit murder on {event_date}"
            )
        elif (date_approx and date_approx != "unknown" and
              shooter.death_date_approx and shooter.death_date_approx != "unknown" and
              int(date_approx) > int(shooter.death_date_approx)):
            raise HTTPException(
                status_code=400,
                detail=f"Shooter died approximately in {shooter.death_date_approx}, cannot commit murder in {date_approx}"
            )

    # Handle victim's death date logic
    if victim.status == "dead" and date_precision != "keep":
        if victim.death_date and event_date and event_date != victim.death_date:
            if event_date > victim.death_date:
                if not update_victim_death:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Victim died on {victim.death_date}, cannot be murdered on {event_date}. Check 'Update victim death date' to proceed."
                    )
            elif event_date < victim.death_date and not update_victim_death:
                raise HTTPException(
                    status_code=400,
                    detail=f"Victim's recorded death date ({victim.death_date}) is later than the murder date ({event_date}). Check 'Update victim death date' to correct this discrepancy."
                )
        elif (victim.death_date_approx and victim.death_date_approx != "unknown" and
              date_approx and date_approx != "unknown" and date_approx != victim.death_date_approx):
            if int(date_approx) > int(victim.death_date_approx):
                if not update_victim_death:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Victim died approximately in {victim.death_date_approx}, cannot be murdered in {date_approx}. Check 'Update victim death date' to proceed."
                    )
            elif int(date_approx) < int(victim.death_date_approx) and not update_victim_death:
                raise HTTPException(
                    status_code=400,
                    detail=f"Victim's recorded death year ({victim.death_date_approx}) is later than the murder year ({date_approx}). Check 'Update victim death date' to correct this discrepancy."
                )

    new_murder = Murders(
        shooter_id=member_id,
        victim_id=victim_id,
        date=event_date,
        date_approx=date_approx
    )
    try:
        db.add(new_murder)
        # Update victim's status
        victim.status = 'dead'
        victim.death_date = event_date
        victim.death_date_approx = date_approx
        db.commit()
        return RedirectResponse(url=f"/members/{member_id}", status_code=303)
    except HTTPException as e:
        db.rollback()
        return handle_error(request, db, member_id, "murders", victim_id, date_precision, date_exact, date_year, e)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/edit/{event_id}", response_class=HTMLResponse)
async def show_edit_murder_form(request: Request, event_id: int, db: Session = Depends(get_db)):
    murder = db.query(Murders).get(event_id)
    if not murder:
        raise HTTPException(status_code=404, detail="Murder event not found")
    
    # Get current shooter's information
    current_shooter = db.query(Members).get(murder.shooter_id)
    
    # Find members from the same set as the shooter, or alliance if no set
    if current_shooter.set_id:
        # Get members from the same set
        shooter_members = db.query(Members).filter(
            Members.id != murder.victim_id,
            Members.set_id == current_shooter.set_id
        ).all()
    elif current_shooter.alliance_id:
        # Get members from the same alliance
        shooter_members = db.query(Members).filter(
            Members.id != murder.victim_id,
            Members.alliance_id == current_shooter.alliance_id
        ).all()
    else:
        # Fallback: only include the current shooter
        shooter_members = [current_shooter]
    
    # Create full member data including status information
    all_members_data = []
    for m in shooter_members:
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
    
    return templates.TemplateResponse("events/murders/edit_murder.html", {
        "request": request,
        "murder": murder,
        "all_members": all_members_data
    })

# Handle editing a murder
@router.post("/edit/{event_id}", response_class=RedirectResponse)
async def edit_murder(
    request: Request,
    event_id: int,
    shooter_id: int = Form(...),
    date_precision: str = Form('exact'),
    date_exact: Optional[str] = Form(None),
    date_year: Optional[str] = Form(None),
    update_victim_death: bool = Form(False),
    db: Session = Depends(get_db)
):
    # Fetch the murder record
    murder = db.query(Murders).get(event_id)
    if not murder:
        raise HTTPException(status_code=404, detail="Murder event not found")
        
    original_shooter_id = murder.shooter_id
    victim_id = murder.victim_id

    # Start a managed transaction
    with transaction_scope(db, error_message="Failed to update murder"):
        # Update shooter if changed
        if murder.shooter_id != shooter_id:
            # Validate new shooter exists and is a valid member
            validate_member(db, shooter_id, check_alive=False)
            
            # Validate shooter was alive at event time - will be checked with the date below
            murder.shooter_id = shooter_id

        # Get victim for validation
        victim = db.query(Members).get(victim_id)
        if not victim:
            raise HTTPException(status_code=404, detail="Victim not found")

        # Parse and validate date based on precision
        original_date = murder.date
        original_date_approx = murder.date_approx
        event_date = original_date
        date_approx = original_date_approx
        
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
        
        # Only perform validation if date has changed
        if event_date != original_date or date_approx != original_date_approx:
            # Validate shooter was alive at event time
            shooter = db.query(Members).get(shooter_id)
            if event_date and shooter.status == 'dead' and shooter.death_date and event_date > shooter.death_date:
                raise HTTPException(
                    status_code=400,
                    detail=f"Shooter died on {shooter.death_date}, cannot commit murder on {event_date}"
                )
            elif (shooter.status == 'dead' and shooter.death_date_approx and 
                  shooter.death_date_approx != "unknown" and date_approx > shooter.death_date_approx):
                raise HTTPException(
                    status_code=400,
                    detail=f"Shooter died approximately in {shooter.death_date_approx}, cannot commit murder in {date_approx}"
                )

            # Validate against victim's death date if not updating it
            if not update_victim_death:
                if victim.death_date and event_date and event_date != victim.death_date:
                    # Check if date is before or after current death date
                    if event_date > victim.death_date:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Victim died on {victim.death_date}, cannot be murdered on {event_date}. Check 'Update victim death date' to proceed."
                        )
                    elif event_date < victim.death_date:
                        raise HTTPException(
                            status_code=400,
                            detail=f"New murder date ({event_date}) is earlier than victim's death date ({victim.death_date}). Check 'Update victim death date' to update records."
                        )
                elif (victim.death_date_approx and victim.death_date_approx != "unknown" and
                      date_approx and date_approx != victim.death_date_approx):
                    # Check if year is before or after current death year
                    if date_approx > victim.death_date_approx:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Victim died approximately in {victim.death_date_approx}, cannot be murdered in {date_approx}. Check 'Update victim death date' to proceed."
                        )
                    elif date_approx < victim.death_date_approx:
                        raise HTTPException(
                            status_code=400,
                            detail=f"New murder year ({date_approx}) is earlier than victim's death year ({victim.death_date_approx}). Check 'Update victim death date' to update records."
                        )

            # Update murder date
            murder.date = event_date
            murder.date_approx = date_approx

            # Update victim's death date if requested
            if update_victim_death:
                victim.death_date = event_date
                victim.death_date_approx = date_approx

            # Sync assists - all assists for this victim should have the same date as the murder
            assists = db.query(Assists).filter(Assists.victim_id == murder.victim_id).all()
            for assist in assists:
                assist.date = event_date
                assist.date_approx = date_approx

    # Ensure we're returning a proper 303 redirect response
    # This will force the browser to perform a GET request to the new URL
    target_url = f"/members/{murder.shooter_id}"
    return RedirectResponse(
        url=target_url, 
        status_code=303,
        headers={"Location": target_url}
    )

# Delete a murder
@router.post("/delete/{event_id}", response_class=RedirectResponse)
async def delete_murder(event_id: int, db: Session = Depends(get_db)):
    murder = db.query(Murders).get(event_id)
    if not murder:
        raise HTTPException(status_code=404, detail="Murder event not found")
    member_id = murder.shooter_id
    victim_id = murder.victim_id
    
    # Start a transaction
    try:
        # Delete all assists related to this victim first
        db.query(Assists).filter(Assists.victim_id == victim_id).delete(synchronize_session=False)
        
        # Delete the murder record
        db.delete(murder)
        
        # Check if there are any other murders for this victim before changing status
        other_murders = db.query(Murders).filter(Murders.victim_id == victim_id).first()
        if not other_murders:
            # No other murders, so update victim status based on other events
            victim = db.query(Members).get(victim_id)
            if victim:
                # Default to unknown status unless we have more information
                new_status = "unknown"
                # Check for shootings - if victim has shooting events, they were at least alive then
                shootings = db.query(Shootings).filter(Shootings.victim_id == victim_id).order_by(Shootings.date.desc()).first()
                if shootings:
                    new_status = "alive"
                
                # Update victim status
                victim.status = new_status
                victim.death_date = None
                victim.death_date_approx = None if new_status == "alive" else "unknown"
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete murder: {str(e)}")
    
    # Ensure we're returning a proper 303 redirect response
    target_url = f"/members/{member_id}"
    return RedirectResponse(
        url=target_url, 
        status_code=303,
        headers={"Location": target_url}
    )