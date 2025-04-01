from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from backend.config.templates import templates
from backend.database.db_alchemy_models import Members, Shootings, get_db
from ..events_funcs import validate_member, get_events_by_type, get_victim_info

router = APIRouter()

@router.get("/{member_id}", response_class=HTMLResponse)
async def get_shootings(request: Request, member_id: int, db: Session = Depends(get_db)):
    validate_member(db, member_id)
    shootings = get_events_by_type(db, member_id, "shootings")
    victim_info = get_victim_info(db, shootings)
    all_members = [{"id": m.id, "name": m.name} for m in db.query(Members).filter(Members.id != member_id).all()]
    return templates.TemplateResponse("events/shootings/list_shootings.html", {
        "request": request,
        "events": shootings,
        "event_type": "shooting",
        "member_id": member_id,
        "all_members": all_members,
        **victim_info
    })

# Show form to add a shooting
@router.get("/add/{member_id}", response_class=HTMLResponse)
async def show_add_shooting_form(request: Request, member_id: int, db: Session = Depends(get_db)):
    validate_member(db, member_id)
    all_members = db.query(Members).filter(Members.id != member_id).all()
    all_members_data = [{"id": m.id, "name": m.name} for m in all_members]
    return templates.TemplateResponse("events/shootings/add_shooting.html", {
        "request": request,
        "event_type": "shooting",
        "member_id": member_id,
        "all_members": all_members_data
    })

# Handle adding a shooting
@router.post("/add/{member_id}", response_class=RedirectResponse)
async def add_shooting(
    request: Request,
    member_id: int,
    victim_id: int = Form(...),
    date_exact: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    shooter = validate_member(db, member_id)
    victim = validate_member(db, victim_id)
    if shooter.id == victim.id:
        raise HTTPException(status_code=400, detail="Shooter and victim cannot be the same")

    event_date = None
    if date_exact:
        try:
            event_date = datetime.strptime(date_exact, "%Y-%m-%d").date()
            validate_member(db, member_id, date_exact, check_alive=True)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")

    shooting = Shootings(
        shooter_id=member_id,
        victim_id=victim_id,
        date=event_date,
        date_approx=event_date.strftime("%Y") if event_date else "unknown"
    )

    try:
        db.add(shooting)
        db.commit()
        return RedirectResponse(url=f"/members/{member_id}", status_code=303)
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
    
    shooter_members_data = [{"id": m.id, "name": m.name} for m in shooter_members]
    
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
    date_exact: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    shooting = db.query(Shootings).get(event_id)
    if not shooting:
        raise HTTPException(status_code=404, detail="Shooting event not found")

    # Verify victim ID matches the original event
    if shooting.victim_id != victim_id:
        raise HTTPException(status_code=400, detail="Cannot change victim for this event")

    # Update shooter if changed
    if shooting.shooter_id != shooter_id:
        # Validate shooter is not the victim
        if shooter_id == victim_id:
            raise HTTPException(status_code=400, detail="Shooter and victim cannot be the same person")
        
        # Validate shooter was alive at event time
        validate_member(db, shooter_id, date_exact or str(shooting.date), check_alive=True)
        shooting.shooter_id = shooter_id

    # Update date if provided and different
    if date_exact and date_exact != str(shooting.date):
        try:
            event_date = datetime.strptime(date_exact, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format (must be YYYY-MM-DD)")

        # Validate shooter was alive at event time
        validate_member(db, shooting.shooter_id, date_exact, check_alive=True)

        # Validate victim was alive at event time
        victim = shooting.victim
        if victim.death_date and event_date > victim.death_date:
            raise HTTPException(
                status_code=400,
                detail=f"Victim died on {victim.death_date}, cannot be shot on {event_date}"
            )
        elif (victim.death_date_approx and victim.death_date_approx != "unknown" and
              int(event_date.strftime("%Y")) > int(victim.death_date_approx)):
            raise HTTPException(
                status_code=400,
                detail=f"Victim died approximately in {victim.death_date_approx}, cannot be shot in {event_date.strftime('%Y')}"
            )

        shooting.date = event_date
        shooting.date_approx = event_date.strftime("%Y")

    try:
        db.commit()
        return RedirectResponse(url=f"/members/{shooting.shooter_id}", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Delete a shooting
@router.post("/delete/{event_id}", response_class=RedirectResponse)
async def delete_shooting(event_id: int, db: Session = Depends(get_db)):
    shooting = db.query(Shootings).get(event_id)
    if not shooting:
        raise HTTPException(status_code=404, detail="Shooting event not found")
    member_id = shooting.shooter_id
    try:
        db.delete(shooting)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    return RedirectResponse(url=f"/members/{member_id}", status_code=303)