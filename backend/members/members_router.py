from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Request, Form, HTTPException, Depends, Body, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session, joinedload
# from backend.database.database import get_db
from backend.config.templates import templates

# Import your SQLAlchemy ORM models.
from backend.database.db_alchemy_models import (
    Members, Sets, Alliances,
    Shootings, Murders, Assists, get_db
)

# Import your Pydantic models.
from backend.database.models import Member, MemberCreate, Shooting, Murder, Assist

router = APIRouter()

# -------------------------------------------------------------------
# List Members
# -------------------------------------------------------------------
@router.get("/", response_class=HTMLResponse)
def list_members(request: Request, db: Session = Depends(get_db)):
    # Query members with their related set and alliance (using joinedload for efficiency)
    members = db.query(Members).options(
        joinedload(Members.set)
    ).all()
    
    members_data = []
    for member in members:
        # Convert to a Pydantic model then to a dict
        try:
            # Try the newer Pydantic v2 method first
            member_data = Member.model_validate(member).model_dump()
        except AttributeError:
            # Fall back to older Pydantic v1 method
            member_data = Member.from_orm(member).dict()
            
        # Add the set name (if available)
        member_data["set_name"] = member.set.name if member.set else "Unknown Set"
        
        # Add alliance information if available
        if member.alliance_id:
            alliance = db.get(Alliances, member.alliance_id)
            if alliance:
                member_data["alliance_name"] = alliance.name
        
        members_data.append(member_data)
    
    # Get all sets for the filter dropdown
    sets = db.query(Sets).order_by(Sets.name).all()
    sets_data = [{"id": s.id, "name": s.name} for s in sets]
    
    # Sort case–insensitively by name
    members_data = sorted(members_data, key=lambda m: m["name"].lower())
    return templates.TemplateResponse("members/index.html", {
        "request": request,
        "members": members_data,
        "sets": sets_data
    })

# -------------------------------------------------------------------
# Display the Add Member Form
# -------------------------------------------------------------------
@router.get("/add/{set_id}", response_class=HTMLResponse)
def add_member_form(request: Request, set_id: int, db: Session = Depends(get_db)):
    set_obj = db.get(Sets, set_id)
    if not set_obj:
        raise HTTPException(status_code=404, detail="Set not found")
    return templates.TemplateResponse("members/add_member.html", {
        "request": request,
        "set_id": set_id,
        "set_name": set_obj.name,
        "current_year": datetime.now().year
    })

# -------------------------------------------------------------------
# Process Adding a New Member
# -------------------------------------------------------------------
@router.post("/add/{set_id}", response_class=RedirectResponse)
def add_member(
    set_id: int,
    name: str = Form(...),
    description: str = Form(None),
    status: str = Form(...),
    # For "locked_up" status
    release_date_precision: str = Form(None),  # 'exact', 'year', or 'life'
    release_date_exact: str = Form(None),
    release_date_year: str = Form(None),
    # For "dead" status
    death_date_exact: str = Form(None),
    death_date_year: str = Form(None),
    alliance_id: str = Form(None),
    db: Session = Depends(get_db)
):
    valid_statuses = {'alive', 'locked_up', 'dead', 'unknown'}
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status value")

    # Process release date values for "locked_up" status
    release_date = None
    release_date_approx = None
    if status == 'locked_up':
        if release_date_precision == 'life':
            release_date_approx = "life"
        elif release_date_precision == 'year' and release_date_year:
            if not release_date_year.isdigit() or len(release_date_year) != 4:
                raise HTTPException(400, "Invalid release year format (must be YYYY)")
            release_date_approx = release_date_year
        elif release_date_precision == 'exact' and release_date_exact:
            try:
                parsed_date = datetime.strptime(release_date_exact, "%Y-%m-%d").date()
                release_date = parsed_date
                release_date_approx = parsed_date.strftime("%Y")
            except ValueError:
                raise HTTPException(400, "Invalid release date format (must be YYYY-MM-DD)")
        else:
            release_date_approx = 'unknown'

    # Process death date values for "dead" status
    death_date = None
    death_date_approx = None
    if status == "dead":
        if death_date_year:
            if not death_date_year.isdigit() or len(death_date_year) != 4:
                raise HTTPException(400, "Invalid death year format (must be YYYY)")
            death_date_approx = death_date_year
        elif death_date_exact:
            try:
                parsed_date = datetime.strptime(death_date_exact, "%Y-%m-%d").date()
                death_date = parsed_date
                death_date_approx = parsed_date.strftime("%Y")
            except ValueError:
                raise HTTPException(400, "Invalid death date format (must be YYYY-MM-DD)")
        else:
            death_date_approx = 'unknown'

    alliance_id_int = int(alliance_id) if alliance_id and alliance_id.strip() else None

    # Validate and build a new member using your Pydantic schema.
    new_member = MemberCreate(
        name=name,
        description=description,
        status=status,
        release_date=release_date,
        release_date_approx=release_date_approx,
        death_date=death_date,
        death_date_approx=death_date_approx,
        set_id=set_id,
        alliance_id=alliance_id_int
    )
    
    # Get data as dict using either v1 or v2 method
    try:
        # Try newer Pydantic v2 method first
        data = new_member.model_dump()
    except AttributeError:
        # Fall back to older Pydantic v1 method
        data = new_member.dict()
        
    # Create and persist a new ORM instance
    member_obj = Members(**data)
    db.add(member_obj)
    db.commit()
    db.refresh(member_obj)
    return RedirectResponse(url=f"/sets/{set_id}", status_code=303)

# -------------------------------------------------------------------
# Display the Edit Member Form
# -------------------------------------------------------------------
@router.get("/edit/{member_id}", response_class=HTMLResponse)
def edit_member_form(request: Request, member_id: int, db: Session = Depends(get_db)):
    member_obj = db.get(Members, member_id)
    if not member_obj:
        raise HTTPException(status_code=404, detail="Member not found")

    try:
        # Try the newer Pydantic v2 method first
        member_data = Member.model_validate(member_obj).model_dump()
    except AttributeError:
        # Fall back to older Pydantic v1 method
        member_data = Member.from_orm(member_obj).dict()
        
    set_name = member_obj.set.name if member_obj.set else "Unknown Set"

    return templates.TemplateResponse(
        "members/edit_member.html",
        {
            "request": request,
            "member": member_data,
            "set_name": set_name
        }
    )

# -------------------------------------------------------------------
# Process Editing an Existing Member
# -------------------------------------------------------------------
@router.post("/edit/{member_id}", response_class=RedirectResponse)
def edit_member(
    member_id: int,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    status: str = Form(...),
    # For "locked_up" status
    release_date_precision: Optional[str] = Form(None),
    release_date_exact: Optional[str] = Form(None),
    release_date_year: Optional[str] = Form(None),
    # For "dead" status
    death_date_exact: Optional[str] = Form(None),
    death_date_year: Optional[str] = Form(None),
    alliance_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    member_obj = db.get(Members, member_id)
    if not member_obj:
        raise HTTPException(status_code=404, detail="Member not found")

    valid_statuses = {'alive', 'locked_up', 'dead', 'unknown'}
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status value")

    # Process release date values for "locked_up" status
    release_date = None
    release_date_approx = None
    if status == 'locked_up':
        if release_date_precision == 'life':
            release_date_approx = "life"
        elif release_date_precision == 'year' and release_date_year:
            if not release_date_year.isdigit() or len(release_date_year) != 4:
                raise HTTPException(400, "Invalid release year format (must be YYYY)")
            release_date_approx = release_date_year
        elif release_date_precision == 'exact' and release_date_exact:
            try:
                parsed_date = datetime.strptime(release_date_exact, "%Y-%m-%d").date()
                release_date = parsed_date
                release_date_approx = parsed_date.strftime("%Y")
            except ValueError:
                raise HTTPException(400, "Invalid release date format (must be YYYY-MM-DD)")
        else:
            release_date_approx = 'unknown'

    # Process death date values for "dead" status
    death_date = None
    death_date_approx = None
    if status == "dead":
        if death_date_year:
            if not death_date_year.isdigit() or len(death_date_year) != 4:
                raise HTTPException(400, "Invalid death year format (must be YYYY)")
            death_date_approx = death_date_year
        elif death_date_exact:
            try:
                parsed_date = datetime.strptime(death_date_exact, "%Y-%m-%d").date()
                death_date = parsed_date
                death_date_approx = parsed_date.strftime("%Y")
            except ValueError:
                raise HTTPException(400, "Invalid death date format (must be YYYY-MM-DD)")
        else:
            death_date_approx = 'unknown'

    alliance_id_int = int(alliance_id) if alliance_id and alliance_id.strip() else None

    # Update member fields
    member_obj.name = name
    member_obj.description = description
    member_obj.status = status
    member_obj.release_date = release_date
    member_obj.release_date_approx = release_date_approx
    member_obj.death_date = death_date
    member_obj.death_date_approx = death_date_approx
    member_obj.alliance_id = alliance_id_int

    db.commit()
    return RedirectResponse(url=f"/members/{member_id}", status_code=303)

# -------------------------------------------------------------------
# Confirm Deletion of a Member
# -------------------------------------------------------------------
@router.get("/delete/{member_id}", response_class=HTMLResponse)
def delete_member_confirmation(request: Request, member_id: int, db: Session = Depends(get_db)):
    member_obj = db.get(Members, member_id)
    if not member_obj:
        raise HTTPException(status_code=404, detail="Member not found")

    # Convert to dict using Pydantic v2/v1 compatibility approach
    try:
        # Try newer Pydantic v2 method first
        member_data = Member.model_validate(member_obj).model_dump()
    except AttributeError:
        # Fall back to older Pydantic v1 method
        member_data = Member.from_orm(member_obj).dict()
        
    set_name = member_obj.set.name if member_obj.set else "Unknown Set"

    # Get related events count
    shootings_count = db.query(Shootings).filter(
        (Shootings.shooter_id == member_id) | (Shootings.victim_id == member_id)
    ).count()
    murders_count = db.query(Murders).filter(
        (Murders.shooter_id == member_id) | (Murders.victim_id == member_id)
    ).count()
    assists_count = db.query(Assists).filter(
        (Assists.shooter_id == member_id) | (Assists.victim_id == member_id)
    ).count()

    return templates.TemplateResponse(
        "members/delete_member.html",
        {
            "request": request,
            "member": member_data,
            "set_name": set_name,
            "shootings_count": shootings_count,
            "murders_count": murders_count,
            "assists_count": assists_count
        }
    )

# -------------------------------------------------------------------
# Process Deleting a Member (and Related Events)
# -------------------------------------------------------------------
@router.post("/delete/{member_id}", response_class=RedirectResponse)
def delete_member(member_id: int, db: Session = Depends(get_db)):
    member_obj = db.get(Members, member_id)
    if not member_obj:
        raise HTTPException(status_code=404, detail="Member not found")
    set_id = member_obj.set_id

    # Delete related events first.
    db.query(Shootings).filter(
        (Shootings.shooter_id == member_id) | (Shootings.victim_id == member_id)
    ).delete(synchronize_session=False)
    db.query(Murders).filter(
        (Murders.shooter_id == member_id) | (Murders.victim_id == member_id)
    ).delete(synchronize_session=False)
    db.query(Assists).filter(
        (Assists.shooter_id == member_id) | (Assists.victim_id == member_id)
    ).delete(synchronize_session=False)

    # Delete the member.
    db.delete(member_obj)
    db.commit()

    redirect_url = f"/sets/{set_id}" if set_id is not None else "/"
    return RedirectResponse(url=redirect_url, status_code=303)

# -------------------------------------------------------------------
# Display Member Details with Activities
# -------------------------------------------------------------------
@router.get("/{member_id}", response_class=HTMLResponse)
def member_details(request: Request, member_id: int, db: Session = Depends(get_db)):
    # Fetch member
    member_obj = db.get(Members, member_id)
    if not member_obj:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Convert to dict using Pydantic v2/v1 compatibility approach
    try:
        # Try newer Pydantic v2 method first
        member_data = Member.model_validate(member_obj).model_dump()
    except AttributeError:
        # Fall back to older Pydantic v1 method
        member_data = Member.from_orm(member_obj).dict()

    # Get set name
    set_name = member_obj.set.name if member_obj.set else "Unknown Set"

    # Fetch alliance name (if applicable)
    alliance_name = None
    if member_obj.alliance_id:
        alliance_obj = db.get(Alliances, member_obj.alliance_id)
        alliance_name = alliance_obj.name if alliance_obj else None

    # Retrieve related activities
    shootings = db.query(Shootings).filter(Shootings.shooter_id == member_id).all()
    murders = db.query(Murders).filter(Murders.shooter_id == member_id).all()
    assists = db.query(Assists).filter(Assists.shooter_id == member_id).all()

    # Include victim_set_id in event data
    shootings_data = []
    for s in shootings:
        try:
            # Try Pydantic v2 method
            shooting_dict = Shooting.model_validate(s).model_dump()
        except AttributeError:
            # Fall back to v1 method
            shooting_dict = Shooting.from_orm(s).dict()
            
        # Add victim set info
        victim = db.get(Members, s.victim_id)
        victim_set_id = victim.set_id if victim and hasattr(victim, 'set_id') else None
        shooting_dict["victim_set_id"] = victim_set_id
        shootings_data.append(shooting_dict)
    
    murders_data = []
    for m in murders:
        try:
            # Try Pydantic v2 method
            murder_dict = Murder.model_validate(m).model_dump()
        except AttributeError:
            # Fall back to v1 method
            murder_dict = Murder.from_orm(m).dict()
            
        # Add victim set info
        victim = db.get(Members, m.victim_id)
        victim_set_id = victim.set_id if victim and hasattr(victim, 'set_id') else None
        murder_dict["victim_set_id"] = victim_set_id
        murders_data.append(murder_dict)
    
    assists_data = []
    for a in assists:
        try:
            # Try Pydantic v2 method
            assist_dict = Assist.model_validate(a).model_dump()
        except AttributeError:
            # Fall back to v1 method
            assist_dict = Assist.from_orm(a).dict()
            
        # Add victim set info
        victim = db.get(Members, a.victim_id)
        victim_set_id = victim.set_id if victim and hasattr(victim, 'set_id') else None
        assist_dict["victim_set_id"] = victim_set_id
        assists_data.append(assist_dict)

    # Gather victim IDs from all events
    victim_ids = {event["victim_id"] for event in shootings_data + murders_data + assists_data if event.get("victim_id")}

    # Fetch victim details
    member_names = {}
    victim_sets = {}
    if victim_ids:
        victims = db.query(Members).filter(Members.id.in_(victim_ids)).all()
        member_names = {v.id: v.name for v in victims}
        victim_sets = {v.id: (v.set.name if v.set else "Unknown Set") for v in victims}

    return templates.TemplateResponse("members/member_details.html", {
        "request": request,
        "member": member_data,
        "set_name": set_name,
        "alliance_name": alliance_name,
        "member_names": member_names,
        "victim_sets": victim_sets,
        "activities": {
            "shootings": shootings_data,
            "murders": murders_data,
            "assists": assists_data
        }
    })

# -------------------------------------------------------------------
# API Endpoints for JSON responses
# -------------------------------------------------------------------

@router.get("/api", response_class=JSONResponse)
def api_list_members(db: Session = Depends(get_db), set_id: Optional[int] = None, status: Optional[str] = None):
    """List members, optionally filtered by set_id or status"""
    query = db.query(Members).options(joinedload(Members.set))
    
    # Apply filters if provided
    if set_id:
        query = query.filter(Members.set_id == set_id)
    if status:
        query = query.filter(Members.status == status)
    
    members = query.all()
    
    members_data = []
    for member in members:
        try:
            # Try the newer Pydantic v2 method first
            member_data = Member.model_validate(member).model_dump()
        except AttributeError:
            # Fall back to older Pydantic v1 method
            member_data = Member.from_orm(member).dict()
            
        # Add the set name (if available)
        member_data["set_name"] = member.set.name if member.set else "Unknown Set"
        
        # Add alliance information if available
        if member.alliance_id:
            alliance = db.get(Alliances, member.alliance_id)
            if alliance:
                member_data["alliance_name"] = alliance.name
        
        members_data.append(member_data)
    
    # Sort case–insensitively by name
    members_data = sorted(members_data, key=lambda m: m["name"].lower())
    return {"members": members_data}

@router.get("/api/{member_id}", response_class=JSONResponse)
def api_get_member(member_id: int, db: Session = Depends(get_db)):
    """Get details for a specific member"""
    member_obj = db.get(Members, member_id)
    if not member_obj:
        raise HTTPException(status_code=404, detail="Member not found")
    
    try:
        # Try newer Pydantic v2 method first
        member_data = Member.model_validate(member_obj).model_dump()
    except AttributeError:
        # Fall back to older Pydantic v1 method
        member_data = Member.from_orm(member_obj).dict()

    # Get set name
    set_name = member_obj.set.name if member_obj.set else "Unknown Set"
    member_data["set_name"] = set_name

    # Fetch alliance name (if applicable)
    alliance_name = None
    if member_obj.alliance_id:
        alliance_obj = db.get(Alliances, member_obj.alliance_id)
        alliance_name = alliance_obj.name if alliance_obj else None
    member_data["alliance_name"] = alliance_name

    # Retrieve related activities
    shootings = db.query(Shootings).filter(Shootings.shooter_id == member_id).all()
    murders = db.query(Murders).filter(Murders.shooter_id == member_id).all()
    assists = db.query(Assists).filter(Assists.shooter_id == member_id).all()

    # Format activity data
    activities = {
        "shootings": [_format_activity(db, s, Shooting) for s in shootings],
        "murders": [_format_activity(db, m, Murder) for m in murders],
        "assists": [_format_activity(db, a, Assist) for a in assists]
    }
    
    member_data["activities"] = activities
    
    return member_data

def _format_activity(db, event, model_class):
    """Helper function to format activity data with victim information"""
    try:
        # Try Pydantic v2 method
        event_dict = model_class.model_validate(event).model_dump()
    except AttributeError:
        # Fall back to v1 method
        event_dict = model_class.from_orm(event).dict()
        
    # Add victim info
    victim = db.get(Members, event.victim_id)
    if victim:
        event_dict["victim_name"] = victim.name
        event_dict["victim_set_id"] = victim.set_id
        event_dict["victim_set_name"] = victim.set.name if victim.set else "Unknown Set"
    
    return event_dict

@router.post("/api", response_class=JSONResponse)
def api_create_member(
    member_data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """Create a new member"""
    # Extract and validate data
    set_id = member_data.get('set_id')
    if not set_id:
        raise HTTPException(status_code=400, detail="set_id is required")
    
    name = member_data.get('name')
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    
    status = member_data.get('status')
    if not status or status not in {'alive', 'locked_up', 'dead', 'unknown'}:
        raise HTTPException(status_code=400, detail="Valid status is required")
    
    # Process release date for locked_up status
    release_date = None
    release_date_approx = None
    if status == 'locked_up':
        release_date_precision = member_data.get('release_date_precision')
        if release_date_precision == 'life':
            release_date_approx = "life"
        elif release_date_precision == 'year' and member_data.get('release_date_year'):
            release_date_year = member_data.get('release_date_year')
            if not str(release_date_year).isdigit() or len(str(release_date_year)) != 4:
                raise HTTPException(400, "Invalid release year format (must be YYYY)")
            release_date_approx = str(release_date_year)
        elif release_date_precision == 'exact' and member_data.get('release_date_exact'):
            try:
                parsed_date = datetime.strptime(member_data.get('release_date_exact'), "%Y-%m-%d").date()
                release_date = parsed_date
                release_date_approx = parsed_date.strftime("%Y")
            except ValueError:
                raise HTTPException(400, "Invalid release date format (must be YYYY-MM-DD)")
        else:
            release_date_approx = 'unknown'

    # Process death date for dead status
    death_date = None
    death_date_approx = None
    if status == "dead":
        if member_data.get('death_date_year'):
            death_date_year = member_data.get('death_date_year')
            if not str(death_date_year).isdigit() or len(str(death_date_year)) != 4:
                raise HTTPException(400, "Invalid death year format (must be YYYY)")
            death_date_approx = str(death_date_year)
        elif member_data.get('death_date_exact'):
            try:
                parsed_date = datetime.strptime(member_data.get('death_date_exact'), "%Y-%m-%d").date()
                death_date = parsed_date
                death_date_approx = parsed_date.strftime("%Y")
            except ValueError:
                raise HTTPException(400, "Invalid death date format (must be YYYY-MM-DD)")
        else:
            death_date_approx = 'unknown'

    alliance_id = member_data.get('alliance_id')
    alliance_id_int = int(alliance_id) if alliance_id and str(alliance_id).strip() else None

    # Create the new member
    new_member = MemberCreate(
        name=name,
        description=member_data.get('description'),
        status=status,
        release_date=release_date,
        release_date_approx=release_date_approx,
        death_date=death_date,
        death_date_approx=death_date_approx,
        set_id=set_id,
        alliance_id=alliance_id_int
    )
    
    # Get data as dict using either v1 or v2 method
    try:
        # Try newer Pydantic v2 method first
        data = new_member.model_dump()
    except AttributeError:
        # Fall back to older Pydantic v1 method
        data = new_member.dict()
        
    # Create and persist a new ORM instance
    member_obj = Members(**data)
    db.add(member_obj)
    db.commit()
    db.refresh(member_obj)
    
    # Return the created member
    try:
        return Member.model_validate(member_obj).model_dump()
    except AttributeError:
        return Member.from_orm(member_obj).dict()

@router.put("/api/{member_id}", response_class=JSONResponse)
def api_update_member(
    member_id: int, 
    member_data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """Update an existing member"""
    # Check if member exists
    member_obj = db.get(Members, member_id)
    if not member_obj:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Validate status if provided
    status = member_data.get('status', member_obj.status)
    if status not in {'alive', 'locked_up', 'dead', 'unknown'}:
        raise HTTPException(status_code=400, detail="Invalid status value")

    # Process release date values for "locked_up" status
    release_date = member_obj.release_date
    release_date_approx = member_obj.release_date_approx
    
    if status == 'locked_up':
        release_date_precision = member_data.get('release_date_precision')
        if release_date_precision == 'life':
            release_date_approx = "life"
        elif release_date_precision == 'year' and member_data.get('release_date_year'):
            release_date_year = member_data.get('release_date_year')
            if not str(release_date_year).isdigit() or len(str(release_date_year)) != 4:
                raise HTTPException(400, "Invalid release year format (must be YYYY)")
            release_date_approx = str(release_date_year)
        elif release_date_precision == 'exact' and member_data.get('release_date_exact'):
            try:
                parsed_date = datetime.strptime(member_data.get('release_date_exact'), "%Y-%m-%d").date()
                release_date = parsed_date
                release_date_approx = parsed_date.strftime("%Y")
            except ValueError:
                raise HTTPException(400, "Invalid release date format (must be YYYY-MM-DD)")

    # Process death date values for "dead" status
    death_date = member_obj.death_date
    death_date_approx = member_obj.death_date_approx
    
    if status == "dead":
        if member_data.get('death_date_year'):
            death_date_year = member_data.get('death_date_year')
            if not str(death_date_year).isdigit() or len(str(death_date_year)) != 4:
                raise HTTPException(400, "Invalid death year format (must be YYYY)")
            death_date_approx = str(death_date_year)
        elif member_data.get('death_date_exact'):
            try:
                parsed_date = datetime.strptime(member_data.get('death_date_exact'), "%Y-%m-%d").date()
                death_date = parsed_date
                death_date_approx = parsed_date.strftime("%Y")
            except ValueError:
                raise HTTPException(400, "Invalid death date format (must be YYYY-MM-DD)")

    # Process alliance ID
    alliance_id = member_data.get('alliance_id', member_obj.alliance_id)
    alliance_id_int = int(alliance_id) if alliance_id and str(alliance_id).strip() else None

    # Update member fields
    member_obj.name = member_data.get('name', member_obj.name)
    member_obj.description = member_data.get('description', member_obj.description)
    member_obj.status = status
    member_obj.release_date = release_date
    member_obj.release_date_approx = release_date_approx
    member_obj.death_date = death_date
    member_obj.death_date_approx = death_date_approx
    member_obj.set_id = member_data.get('set_id', member_obj.set_id)
    member_obj.alliance_id = alliance_id_int

    db.commit()
    db.refresh(member_obj)
    
    # Return the updated member
    try:
        return Member.model_validate(member_obj).model_dump()
    except AttributeError:
        return Member.from_orm(member_obj).dict()

@router.delete("/api/{member_id}", response_class=JSONResponse)
def api_delete_member(member_id: int, db: Session = Depends(get_db)):
    """Delete a member and related events"""
    member_obj = db.get(Members, member_id)
    if not member_obj:
        raise HTTPException(status_code=404, detail="Member not found")

    # Delete related events first
    db.query(Shootings).filter(
        (Shootings.shooter_id == member_id) | (Shootings.victim_id == member_id)
    ).delete(synchronize_session=False)
    db.query(Murders).filter(
        (Murders.shooter_id == member_id) | (Murders.victim_id == member_id)
    ).delete(synchronize_session=False)
    db.query(Assists).filter(
        (Assists.shooter_id == member_id) | (Assists.victim_id == member_id)
    ).delete(synchronize_session=False)

    # Store member details before deletion for return value
    member_data = {"id": member_obj.id, "name": member_obj.name}
    
    # Delete the member
    db.delete(member_obj)
    db.commit()

    return {"success": True, "deleted": member_data, "message": "Member deleted successfully"}
