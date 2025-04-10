from typing import Optional, List, Any, Dict, Tuple, Union
from fastapi import Request, HTTPException
from backend.config.templates import templates
from sqlalchemy import or_
from sqlalchemy.orm import Session
from datetime import datetime
from backend.database.db_alchemy_models import Members, Murders, Shootings, Assists, Sets
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError

VALID_EVENT_TYPES = {"shootings": "shootings", "murders": "murders", "assists": "assists"}

# -------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------
def normalize_event_type(event_type: str) -> str:
    return event_type.strip().lower()

# --------------------------
# Transaction Management
# --------------------------

@contextmanager
def transaction_scope(db: Session, error_message: str = "Database transaction failed"):
    """Provide a transactional scope around a series of operations."""
    try:
        yield
        db.commit()
    except HTTPException as e:
        db.rollback()
        raise  # Re-raise HTTP exceptions as they are already properly formatted
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"{error_message}: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"{error_message}: {str(e)}")

# -------------------------------------------------------------------
# Member Validation
# -------------------------------------------------------------------
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

# --------------------------
# Date Parsing Functions
# --------------------------

def parse_date(date_precision: str, date_exact: Optional[str], date_year: Optional[str]) -> Tuple[Optional[datetime.date], str]:
    """Parse date based on precision and return (date, approximate_date)."""
    event_date = None
    date_approx = "unknown"
    
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
    elif date_precision == 'keep':
        # Special case for murders keeping victim's death date
        # The actual value is handled by the calling function
        pass
    
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
        # If member is alive but has death_date_approx set to 'unknown', clear it
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