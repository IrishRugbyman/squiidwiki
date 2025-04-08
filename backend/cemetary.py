from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.config.templates import templates
from backend.database.models import Member

# Import your ORM models
from backend.database.db_alchemy_models import Members, Sets, Shootings, Murders, Assists, get_db

router = APIRouter()

VALID_EVENT_TYPES = {"shootings": "shootings", "murders": "murders", "assists": "assists"}

# -------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------
def normalize_event_type(event_type: str) -> str:
    return event_type.strip().lower()


def validate_member(
        db: Session,
        member_id: int,
        event_date: Optional[str] = None,
        event_date_approx: Optional[str] = None,
        check_alive: bool = False
) -> Members:
    member = db.get(Members, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if check_alive and member.status == 'dead':
        death_dt = member.death_date
        death_approx = member.death_date_approx

        if event_date:
            try:
                event_dt = datetime.strptime(event_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format, use YYYY-MM-DD")

            if death_dt and event_dt > death_dt:
                raise HTTPException(
                    status_code=400,
                    detail=f"Member died on {death_dt.strftime('%Y-%m-%d')}, cannot participate in event on {event_date}"
                )
            elif not death_dt and death_approx and death_approx != "unknown" and event_date >= death_approx:
                raise HTTPException(
                    status_code=400,
                    detail=f"Member died approximately in {death_approx}, cannot participate in event on {event_date}"
                )
        elif event_date_approx and event_date_approx != "unknown":
            if death_dt and int(event_date_approx) > death_dt.year:
                raise HTTPException(
                    status_code=400,
                    detail=f"Member died on {death_dt.strftime('%Y-%m-%d')}, cannot participate in event in {event_date_approx}"
                )
            elif not death_dt and death_approx and death_approx != "unknown" and int(event_date_approx) >= int(
                    death_approx):
                raise HTTPException(
                    status_code=400,
                    detail=f"Member died approximately in {death_approx}, cannot participate in event in {event_date_approx}"
                )
    return member

def get_events_by_type(db: Session, member_id: int, event_type: str) -> List[Any]:
    event_type = normalize_event_type(event_type)
    if event_type not in VALID_EVENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid event type")
    if event_type == "shootings":
        events = db.query(Shootings).filter(
            or_(Shootings.shooter_id == member_id, Shootings.victim_id == member_id)
        ).order_by(Shootings.date.desc()).all()
    elif event_type == "murders":
        events = db.query(Murders).filter(
            or_(Murders.shooter_id == member_id, Murders.victim_id == member_id)
        ).order_by(Murders.date.desc()).all()
    elif event_type == "assists":
        events = db.query(Assists).filter(
            or_(Assists.shooter_id == member_id, Assists.victim_id == member_id)
        ).order_by(Assists.date.desc()).all()
    else:
        events = []
    return events

def get_victim_info(db: Session, events: List[Any]) -> Dict[str, Any]:
    # Gather unique victim IDs from events (skip None)
    victim_ids = {event.victim_id for event in events if event.victim_id is not None}
    member_names: Dict[int, str] = {}
    victim_set_ids: Dict[int, int] = {}

    if victim_ids:
        victims: List[Members] = db.query(Members).filter(Members.id.in_(victim_ids)).all()
        member_names = {m.id: m.name for m in victims}
        victim_set_ids = {m.id: m.set_id for m in victims}

    sets_dict: Dict[int, str] = {}
    if victim_set_ids:
        set_ids = list(victim_set_ids.values())
        sets_objs: List[Sets] = db.query(Sets).filter(Sets.id.in_(set_ids)).all()
        sets_dict = {s.id: s.name for s in sets_objs}

    victim_sets = {vid: sets_dict.get(sid, 'Unknown Set') for vid, sid in victim_set_ids.items()}

    return {
        "member_names": member_names,
        "victim_sets": victim_sets,
        "victim_set_ids": victim_set_ids
    }

def parse_date(date_precision: str, date_exact: Optional[str], date_year: Optional[str]):
    event_date = None
    date_approx = None
    try:
        if date_precision == "exact" and date_exact:
            try:
                parsed_date = datetime.strptime(date_exact, "%Y-%m-%d").date()
                event_date = parsed_date
                date_approx = parsed_date.strftime("%Y")
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid date format. Please use the format YYYY-MM-DD (e.g., 2023-05-15)."
                )
        elif date_precision == "year" and date_year:
            if not date_year.isdigit() or len(date_year) != 4:
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid year format. Please enter a 4-digit year (e.g., 2023)."
                )
            date_approx = date_year
        elif date_precision == "unknown":
            date_approx = "unknown"
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid date precision: '{date_precision}'. Please select from 'exact', 'year', or 'unknown'."
            )
    except Exception as e:
        # Catch any other unexpected errors to prevent app crashes
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=400,
            detail=f"Error processing date: {str(e)}. Please check your input and try again."
        )
    return event_date, date_approx

def handle_error(
    request: Request,
    db: Session,
    member_id: int,
    event_type: str,
    victim_id: int,
    date_precision: Optional[str],
    date_exact: Optional[str],
    date_year: Optional[str],
    error: Exception
):
    """
    Handles errors during event creation or editing by rendering the form again with the error message.
    Also preserves the user's input to avoid data loss.
    """
    all_members = db.query(Members).filter(Members.id != member_id).order_by(Members.name).all()
    member = db.get(Members, member_id)
    
    # Create a list of dictionaries with member data, including death dates if available
    all_members_data = []
    duplicate_names = set()
    name_counts = {}
    
    for m in all_members:
        name_counts[m.name] = name_counts.get(m.name, 0) + 1
    
    for name, count in name_counts.items():
        if count > 1:
            duplicate_names.add(name)
    
    for m in all_members:
        all_members_data.append({
            "id": m.id, 
            "name": m.name,
            "set_name": m.set_name,
            "death_date": m.death_date,
            "death_date_approx": m.death_date_approx
        })
    
    # Extract error detail
    error_message = str(error)
    if hasattr(error, 'detail'):
        error_message = error.detail
    
    # Get the status code, default to 400 if not available
    status_code = 400
    if hasattr(error, 'status_code'):
        status_code = error.status_code
    
    # Determine template based on event type
    template_name = f"events/{event_type}/add_{event_type[:-1]}.html"
    if event_type == "murders":
        template_name = "events/murders/add_murder.html"
    elif event_type == "shootings":
        template_name = "events/shootings/add_shooting.html"
    elif event_type == "assists":
        template_name = "events/assists/add_assist.html"
    
    return templates.TemplateResponse(template_name, {
        "request": request,
        "member_id": member_id,
        "member_name": member.name if member else "Unknown Member",
        "all_members": all_members_data,
        "duplicate_names": duplicate_names,
        "error_message": error_message,
        "form_data": {
            "victim_id": victim_id,
            "date_precision": date_precision,
            "date_exact": date_exact,
            "date_year": date_year
        }
    }, status_code=status_code)

# -------------------------------------------------------------------
# Endpoints to List Events for a Member
# -------------------------------------------------------------------
@router.get("/shootings/{member_id}", response_class=HTMLResponse)
async def get_shootings(request: Request, member_id: int, db: Session = Depends(get_db)):
    validate_member(db, member_id)
    shootings = get_events_by_type(db, member_id, "shootings")
    victim_info = get_victim_info(db, shootings)
    # Get all members (excluding the current member)
    all_members = [{"id": m.id, "name": m.name} for m in db.query(Members).filter(Members.id != member_id).all()]
    return templates.TemplateResponse("events/add_event.html", {
        "request": request,
        "events": shootings,
        "event_type": "shooting",
        "member_id": member_id,
        "all_members": all_members,
        **victim_info
    })

@router.get("/murders/{member_id}", response_class=HTMLResponse)
async def get_murders(request: Request, member_id: int, db: Session = Depends(get_db)):
    validate_member(db, member_id)
    murders = get_events_by_type(db, member_id, "murders")
    victim_info = get_victim_info(db, murders)
    all_members = [{"id": m.id, "name": m.name} for m in db.query(Members).filter(Members.id != member_id).all()]
    return templates.TemplateResponse("events/add_event.html", {
        "request": request,
        "events": murders,
        "event_type": "murder",
        "member_id": member_id,
        "all_members": all_members,
        **victim_info
    })

@router.get("/assists/{member_id}", response_class=HTMLResponse)
async def get_assists(request: Request, member_id: int, db: Session = Depends(get_db)):
    validate_member(db, member_id)
    assists = get_events_by_type(db, member_id, "assists")
    victim_info = get_victim_info(db, assists)
    all_members = [{"id": m.id, "name": m.name} for m in db.query(Members).filter(Members.id != member_id).all()]
    return templates.TemplateResponse("events/add_event.html", {
        "request": request,
        "events": assists,
        "event_type": "assist",
        "member_id": member_id,
        "all_members": all_members,
        **victim_info
    })

# -------------------------------------------------------------------
# Form to Add an Event
# -------------------------------------------------------------------
@router.get("/add/{event_type}/{member_id}", response_class=HTMLResponse)
async def show_add_event_form(
    request: Request,
    member_id: int,
    event_type: str,
    db: Session = Depends(get_db)
):
    event_type = normalize_event_type(event_type)
    if event_type == "assists":
        # For assists, only show dead members
        all_members = db.query(Members).filter(Members.id != member_id, Members.status == 'dead').all()
        template_name = "events/add_assist.html"
    elif event_type == "murders":
        # For murders, show members that do not already have a murder record as victim
        # Using an outer join to filter out members with an existing murder record.
        all_members = db.query(Members).outerjoin(Murders, Members.id == Murders.victim_id).filter(
            Members.id != member_id, Murders.id == None
        ).all()
        template_name = "events/add_murder.html"
    else:
        # For shootings, show all members except the shooter
        all_members = db.query(Members).filter(Members.id != member_id).all()
        template_name = "events/add_shooting.html"
    all_members_data = [
        {
            "id": m.id,
            "name": m.name,
            "status": m.status,
            "death_date": m.death_date,
            "death_date_approx": m.death_date_approx
        } for m in all_members
    ]
    return templates.TemplateResponse(template_name, {
        "request": request,
        "event_type": event_type,
        "member_id": member_id,
        "all_members": all_members_data
    })

# -------------------------------------------------------------------
# Handlers to Add Events
# -------------------------------------------------------------------
async def add_shooting(
        request: Request,
        member_id: int,
        victim_id: int,
        date_precision: str,
        date_exact: Optional[str],
        date_year: Optional[str],
        db: Session
):
    event_date, date_approx = parse_date(date_precision, date_exact, date_year)

    # Validate shooter and victim status at event time
    validate_member(db, member_id, date_exact if event_date else None, date_approx, check_alive=True)
    validate_member(db, victim_id, date_exact if event_date else None, date_approx, check_alive=True)

    new_event = Shootings(
        shooter_id=member_id,
        victim_id=victim_id,
        date=event_date,
        date_approx=date_approx
    )
    try:
        db.add(new_event)
        db.commit()
        return RedirectResponse(url=f"/members/{member_id}", status_code=303)
    except HTTPException as e:
        db.rollback()
        return handle_error(request, db, member_id, "shootings", victim_id, date_precision, date_exact, date_year, e)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


async def add_murder(
        request: Request,
        member_id: int,
        victim_id: int,
        date_precision: str = 'keep',
        date_exact: Optional[str] = None,
        date_year: Optional[str] = None,
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
        if victim.death_date and event_date and event_date > victim.death_date:
            raise HTTPException(
                status_code=400,
                detail=f"Victim died on {victim.death_date}, cannot be murdered on {event_date}"
            )
        elif (victim.death_date_approx and victim.death_date_approx != "unknown" and
              date_approx and date_approx != "unknown" and
              int(date_approx) > int(victim.death_date_approx)):
            raise HTTPException(
                status_code=400,
                detail=f"Victim died approximately in {victim.death_date_approx}, cannot be murdered in {date_approx}"
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


async def add_assist(
        request: Request,
        member_id: int,
        victim_id: int,
        db: Session
):
    shooter = validate_member(db, member_id)
    victim = validate_member(db, victim_id)

    if victim.status != "dead" or (not victim.death_date and not victim.death_date_approx):
        raise HTTPException(status_code=400, detail="Victim must be dead with a known death date")

    # Validate shooter was alive at victim's death time
    if shooter.status == 'dead':
        if victim.death_date and shooter.death_date and victim.death_date > shooter.death_date:
            raise HTTPException(
                status_code=400,
                detail=f"Assistant died on {shooter.death_date}, cannot assist in murder on {victim.death_date}"
            )
        elif (shooter.death_date_approx != "unknown" and victim.death_date_approx != "unknown" and
              int(victim.death_date_approx) > int(shooter.death_date_approx)):
            raise HTTPException(
                status_code=400,
                detail=f"Assistant died approximately in {shooter.death_date_approx}, cannot assist in murder in {victim.death_date_approx}"
            )

    new_assist = Assists(
        shooter_id=member_id,
        victim_id=victim_id,
        date=victim.death_date,
        date_approx=victim.death_date_approx
    )
    try:
        db.add(new_assist)
        db.commit()
        return RedirectResponse(url=f"/members/{member_id}", status_code=303)
    except HTTPException as e:
        db.rollback()
        return handle_error(request, db, member_id, "assists", victim_id, None, None, None, e)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------------
# Main Endpoint to Add an Event
# -------------------------------------------------------------------
@router.post("/add/{event_type}/{member_id}", response_class=RedirectResponse)
async def add_event(
        request: Request,
        event_type: str,
        member_id: int,
        victim_id: int = Form(...),
        date_precision: str = Form(None),
        date_exact: Optional[str] = Form(None),
        date_year: Optional[str] = Form(None),
        db: Session = Depends(get_db)
):
    event_type = normalize_event_type(event_type)
    if event_type not in VALID_EVENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid event type")

    if member_id == victim_id:
        raise HTTPException(status_code=400, detail="Shooter and victim cannot be the same")

    if event_type == "shootings":
        return await add_shooting(request, member_id, victim_id, date_precision, date_exact, date_year, db)
    elif event_type == "murders":
        return await add_murder(request, member_id, victim_id, date_precision, date_exact, date_year, db)
    elif event_type == "assists":
        return await add_assist(request, member_id, victim_id, db)

# -------------------------------------------------------------------
# Endpoint to Delete an Event
# -------------------------------------------------------------------
@router.post("/delete/{event_type}/{event_id}", response_class=RedirectResponse)
async def delete_event(event_type: str, event_id: int, db: Session = Depends(get_db)):
    # Map singular event type to ORM model
    model_mapping = {
        "shooting": Shootings,
        "murder": Murders,
        "assist": Assists
    }
    if event_type not in model_mapping:
        raise HTTPException(status_code=400, detail="Invalid event type")
    EventModel = model_mapping[event_type]
    event = db.query(EventModel).get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    member_id = event.shooter_id
    try:
        db.delete(event)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    return RedirectResponse(url=f"/members/{member_id}", status_code=303)