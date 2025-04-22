from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Request, Form, HTTPException, Depends, Body, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from backend.config.templates import templates

# Import your SQLAlchemy ORM models.
from backend.database.imports import Members, Sets, Alliance as Alliances, Shootings, Murders, Assists, get_db

# Import your Pydantic models.
from backend.members.schemas import MemberBase, MemberCreate, MemberResponse as Member
from backend.events.schemas import ShootingResponse as Shooting, MurderResponse as Murder, AssistResponse as Assist
from backend.members.service.member_service import format_activity

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
    elif status != 'locked_up':
        # Clear release date fields if status is not locked_up
        release_date = None
        release_date_approx = None

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
    elif status != 'dead':
        # Clear death date fields if status is not dead
        death_date = None
        death_date_approx = None

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
    elif status != 'locked_up':
        # Clear release date fields if status is not locked_up
        release_date = None
        release_date_approx = None

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
    elif status != 'dead':
        # Clear death date fields if status is not dead
        death_date = None
        death_date_approx = None

    # Process alliance ID
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
# Display the Delete Member Confirmation
# -------------------------------------------------------------------
@router.get("/delete/{member_id}", response_class=HTMLResponse)
def delete_member_confirmation(request: Request, member_id: int, db: Session = Depends(get_db)):
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
    
    # Get counts of activities associated with this member
    shootings_count = db.query(Shootings).filter(
        or_(Shootings.shooter_id == member_id, Shootings.victim_id == member_id)
    ).count()
    murders_count = db.query(Murders).filter(
        or_(Murders.shooter_id == member_id, Murders.victim_id == member_id)
    ).count()
    assists_count = db.query(Assists).filter(
        or_(Assists.shooter_id == member_id, Assists.victim_id == member_id)
    ).count()
    total_activity_count = shootings_count + murders_count + assists_count

    return templates.TemplateResponse(
        "members/delete_member.html",
        {
            "request": request,
            "member": member_data,
            "set_name": set_name,
            "total_activity_count": total_activity_count
        }
    )

# -------------------------------------------------------------------
# Process Deleting a Member
# -------------------------------------------------------------------
@router.post("/delete/{member_id}", response_class=RedirectResponse)
def delete_member(member_id: int, db: Session = Depends(get_db)):
    member_obj = db.get(Members, member_id)
    if not member_obj:
        raise HTTPException(status_code=404, detail="Member not found")
    
    set_id = member_obj.set_id
    
    # Delete member and associated records
    # For Shootings, we need to delete both where member is shooter or victim
    db.query(Shootings).filter(Shootings.shooter_id == member_id).delete()
    db.query(Shootings).filter(Shootings.victim_id == member_id).delete()
    
    # For Murders, we need to delete both where member is shooter or victim
    db.query(Murders).filter(Murders.shooter_id == member_id).delete()
    db.query(Murders).filter(Murders.victim_id == member_id).delete()
    
    # For Assists, we need to delete both where member is shooter or victim
    db.query(Assists).filter(Assists.shooter_id == member_id).delete()
    db.query(Assists).filter(Assists.victim_id == member_id).delete()
    
    db.delete(member_obj)
    db.commit()
    
    return RedirectResponse(url=f"/sets/{set_id}" if set_id else "/members/", status_code=303)

# -------------------------------------------------------------------
# Display Member Details
# -------------------------------------------------------------------
@router.get("/{member_id}", response_class=HTMLResponse)
def member_details(request: Request, member_id: int, db: Session = Depends(get_db)):
    # Fetch member
    member_obj = db.query(Members).filter(Members.id == member_id).first()
    if not member_obj:
        raise HTTPException(status_code=404, detail="Member not found")
    
    try:
        # Try the newer Pydantic v2 method first
        member_data = Member.model_validate(member_obj).model_dump()
    except AttributeError:
        # Fall back to older Pydantic v1 method
        member_data = Member.from_orm(member_obj).dict()
    
    # Get set information
    set_data = None
    set_name = "Unknown Set"
    if member_obj.set_id:
        set_obj = db.get(Sets, member_obj.set_id)
        if set_obj:
            set_data = {
                "id": set_obj.id,
                "name": set_obj.name,
                "description": set_obj.description,
                "type": set_obj.type
            }
            set_name = set_obj.name
    
    # Get alliance information 
    alliance_data = None
    alliance_name = None
    if member_obj.alliance_id:
        alliance_obj = db.get(Alliances, member_obj.alliance_id)
        if alliance_obj:
            alliance_data = {
                "id": alliance_obj.id,
                "name": alliance_obj.name,
                "description": alliance_obj.description
            }
            alliance_name = alliance_obj.name
    
    # Get activity history for this member
    # Shootings
    shootings = db.query(Shootings).filter(
        or_(Shootings.shooter_id == member_id, Shootings.victim_id == member_id)
    ).order_by(Shootings.date.desc()).all()
    shootings_data = [format_activity(db, shooting, Shooting) for shooting in shootings]
    
    # Murders
    murders = db.query(Murders).filter(
        Murders.shooter_id == member_id  # Only include murders where this member is the shooter
    ).order_by(Murders.date.desc()).all()
    murders_data = [format_activity(db, murder, Murder) for murder in murders]
    
    # Assists
    assists = db.query(Assists).filter(
        or_(Assists.shooter_id == member_id, Assists.victim_id == member_id)
    ).order_by(Assists.date.desc()).all()
    assists_data = [format_activity(db, assist, Assist) for assist in assists]
    
    # Get total counts
    total_shootings = len(shootings_data)
    total_murders = len(murders_data)
    total_assists = len(assists_data)
    total_events = total_shootings + total_murders + total_assists
    
    # Group activities data into a single dictionary for the template
    activities_data = {
        "shootings": shootings_data,
        "murders": murders_data,
        "assists": assists_data
    }
    
    # Get all member and set information needed for the activities
    member_ids = set()
    for activity_list in [shootings_data, murders_data, assists_data]:
        for activity in activity_list:
            if 'victim_id' in activity:
                member_ids.add(activity['victim_id'])
            if 'shooter_id' in activity:
                member_ids.add(activity['shooter_id'])
    
    # Create dictionaries for member names and their sets
    member_names = {}
    victim_sets = {}
    if member_ids:
        members_info = db.query(Members).filter(Members.id.in_(member_ids)).all()
        for m in members_info:
            member_names[m.id] = m.name
            if m.set_id:
                set_obj = db.get(Sets, m.set_id)
                if set_obj:
                    victim_sets[m.id] = set_obj.name
                else:
                    victim_sets[m.id] = "Unknown Set"
            else:
                victim_sets[m.id] = "Unknown Set"
    
    # Add victim_set_id to each activity for proper linking
    for activity_list in [shootings_data, murders_data, assists_data]:
        for activity in activity_list:
            if 'victim_id' in activity and activity['victim_id'] in member_ids:
                victim_id = activity['victim_id']
                victim_member = db.query(Members).filter(Members.id == victim_id).first()
                if victim_member and victim_member.set_id:
                    activity['victim_set_id'] = victim_member.set_id
                else:
                    # Default to an unknown set if needed
                    activity['victim_set_id'] = None
    
    return templates.TemplateResponse(
        "members/member_details.html",
        {
            "request": request,
            "member": member_data,
            "set": set_data,
            "set_name": set_name,
            "alliance": alliance_data,
            "alliance_name": alliance_name,
            "total_events": total_events,
            "total_shootings": total_shootings,
            "total_murders": total_murders,
            "total_assists": total_assists,
            "activities": activities_data,
            "member_names": member_names,
            "victim_sets": victim_sets
        }
    )

# -------------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------------
@router.get("/api", response_class=JSONResponse)
def api_list_members(db: Session = Depends(get_db), set_id: Optional[int] = None, status: Optional[str] = None):
    query = db.query(Members)
    
    # Apply filters if provided
    if set_id:
        query = query.filter(Members.set_id == set_id)
    
    if status:
        query = query.filter(Members.status == status)
    
    members = query.all()
    
    # Convert to Pydantic models for JSON serialization
    try:
        # Try newer Pydantic v2 method first
        results = [Member.model_validate(m).model_dump() for m in members]
    except AttributeError:
        # Fall back to older Pydantic v1 method
        results = [Member.from_orm(m).dict() for m in members]
        
    # Add extra information like set name
    for i, member in enumerate(members):
        if member.set_id:
            set_obj = db.get(Sets, member.set_id)
            if set_obj:
                results[i]["set_name"] = set_obj.name
    
    return {"members": results}

@router.get("/api/{member_id}", response_class=JSONResponse)
def api_get_member(member_id: int, db: Session = Depends(get_db)):
    member = db.get(Members, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Convert to Pydantic model
    try:
        # Try newer Pydantic v2 method first
        member_data = Member.model_validate(member).model_dump()
    except AttributeError:
        # Fall back to older Pydantic v1 method
        member_data = Member.from_orm(member).dict()
    
    # Add additional information
    if member.set_id:
        set_obj = db.get(Sets, member.set_id)
        if set_obj:
            member_data["set_name"] = set_obj.name
    
    if member.alliance_id:
        alliance_obj = db.get(Alliances, member.alliance_id)
        if alliance_obj:
            member_data["alliance_name"] = alliance_obj.name
    
    # Add activity counts
    member_data["shootings_count"] = db.query(Shootings).filter(
        or_(Shootings.shooter_id == member_id, Shootings.victim_id == member_id)
    ).count()
    member_data["murders_count"] = db.query(Murders).filter(
        or_(Murders.shooter_id == member_id, Murders.victim_id == member_id)
    ).count()
    member_data["assists_count"] = db.query(Assists).filter(
        or_(Assists.shooter_id == member_id, Assists.victim_id == member_id)
    ).count()
    
    return member_data

@router.post("/api", response_class=JSONResponse)
def api_create_member(
    member_data: dict = Body(...),
    db: Session = Depends(get_db)
):
    # Validate required fields
    required_fields = ["name", "status", "set_id"]
    for field in required_fields:
        if field not in member_data:
            raise HTTPException(status_code=400, detail=f"Field '{field}' is required")
    
    # Validate status value
    valid_statuses = {'alive', 'locked_up', 'dead', 'unknown'}
    if member_data.get("status") not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status value")
    
    # Process dates according to status
    status = member_data.get("status")
    
    # For locked_up status
    if status == "locked_up":
        if "release_date" in member_data and member_data["release_date"]:
            try:
                # Parse the date string to a date object
                release_date = datetime.strptime(member_data["release_date"], "%Y-%m-%d").date()
                member_data["release_date"] = release_date
                # Set approximate year from the exact date
                member_data["release_date_approx"] = release_date.strftime("%Y")
            except ValueError:
                raise HTTPException(400, "Invalid release date format (must be YYYY-MM-DD)")
        elif "release_date_approx" in member_data and member_data["release_date_approx"]:
            # Ensure the approximate date is valid (a year or "life")
            approx = member_data["release_date_approx"]
            if approx != "life" and not (approx.isdigit() and len(approx) == 4):
                raise HTTPException(400, "Invalid release year format (must be YYYY or 'life')")
    elif status != "locked_up":
        # Clear release date fields for non-locked_up statuses
        member_data["release_date"] = None
        member_data["release_date_approx"] = None
    
    # For dead status
    if status == "dead":
        if "death_date" in member_data and member_data["death_date"]:
            try:
                # Parse the date string to a date object
                death_date = datetime.strptime(member_data["death_date"], "%Y-%m-%d").date()
                member_data["death_date"] = death_date
                # Set approximate year from the exact date
                member_data["death_date_approx"] = death_date.strftime("%Y")
            except ValueError:
                raise HTTPException(400, "Invalid death date format (must be YYYY-MM-DD)")
        elif "death_date_approx" in member_data and member_data["death_date_approx"]:
            # Ensure the approximate date is a valid year
            approx = member_data["death_date_approx"]
            if not (approx.isdigit() and len(approx) == 4):
                raise HTTPException(400, "Invalid death year format (must be YYYY)")
    elif status != "dead":
        # Clear death date fields for non-dead statuses
        member_data["death_date"] = None
        member_data["death_date_approx"] = None
    
    # Create a new member instance
    new_member = Members(**member_data)
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    
    # Return the created member
    try:
        # Try newer Pydantic v2 method first
        result = Member.model_validate(new_member).model_dump()
    except AttributeError:
        # Fall back to older Pydantic v1 method
        result = Member.from_orm(new_member).dict()
        
    return result

@router.put("/api/{member_id}", response_class=JSONResponse)
def api_update_member(
    member_id: int, 
    member_data: dict = Body(...),
    db: Session = Depends(get_db)
):
    # Find the member
    member = db.get(Members, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Validate status if provided
    if "status" in member_data:
        valid_statuses = {'alive', 'locked_up', 'dead', 'unknown'}
        if member_data["status"] not in valid_statuses:
            raise HTTPException(status_code=400, detail="Invalid status value")
    
    # Get current status or new status
    status = member_data.get("status", member.status)
    
    # Process dates according to status
    # For locked_up status
    if status == "locked_up":
        if "release_date" in member_data and member_data["release_date"]:
            try:
                # Parse the date string to a date object if it's a string
                if isinstance(member_data["release_date"], str):
                    release_date = datetime.strptime(member_data["release_date"], "%Y-%m-%d").date()
                    member_data["release_date"] = release_date
                    # Set approximate year from the exact date
                    member_data["release_date_approx"] = release_date.strftime("%Y")
            except ValueError:
                raise HTTPException(400, "Invalid release date format (must be YYYY-MM-DD)")
        elif "release_date_approx" in member_data and member_data["release_date_approx"]:
            # Ensure the approximate date is valid (a year or "life")
            approx = member_data["release_date_approx"]
            if approx != "life" and not (approx.isdigit() and len(approx) == 4):
                raise HTTPException(400, "Invalid release year format (must be YYYY or 'life')")
    elif status != "locked_up" and "status" in member_data:
        # Clear release date fields for non-locked_up statuses when status changes
        member_data["release_date"] = None
        member_data["release_date_approx"] = None
    
    # For dead status
    if status == "dead":
        if "death_date" in member_data and member_data["death_date"]:
            try:
                # Parse the date string to a date object if it's a string
                if isinstance(member_data["death_date"], str):
                    death_date = datetime.strptime(member_data["death_date"], "%Y-%m-%d").date()
                    member_data["death_date"] = death_date
                    # Set approximate year from the exact date
                    member_data["death_date_approx"] = death_date.strftime("%Y")
            except ValueError:
                raise HTTPException(400, "Invalid death date format (must be YYYY-MM-DD)")
        elif "death_date_approx" in member_data and member_data["death_date_approx"]:
            # Ensure the approximate date is a valid year
            approx = member_data["death_date_approx"]
            if not (approx.isdigit() and len(approx) == 4):
                raise HTTPException(400, "Invalid death year format (must be YYYY)")
    elif status != "dead" and "status" in member_data:
        # Clear death date fields for non-dead statuses when status changes
        member_data["death_date"] = None
        member_data["death_date_approx"] = None
    
    # Update the member attributes
    for key, value in member_data.items():
        # Skip unsupported attributes
        if hasattr(member, key):
            setattr(member, key, value)
    
    db.commit()
    db.refresh(member)
    
    # Return the updated member
    try:
        # Try newer Pydantic v2 method first
        result = Member.model_validate(member).model_dump()
    except AttributeError:
        # Fall back to older Pydantic v1 method
        result = Member.from_orm(member).dict()
        
    return result

@router.delete("/api/{member_id}", response_class=JSONResponse)
def api_delete_member(member_id: int, db: Session = Depends(get_db)):
    # Find the member
    member = db.get(Members, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Delete associated records
    # For Shootings, we need to delete both where member is shooter or victim
    db.query(Shootings).filter(Shootings.shooter_id == member_id).delete()
    db.query(Shootings).filter(Shootings.victim_id == member_id).delete()
    
    # For Murders, we need to delete both where member is shooter or victim
    db.query(Murders).filter(Murders.shooter_id == member_id).delete()
    db.query(Murders).filter(Murders.victim_id == member_id).delete()
    
    # For Assists, we need to delete both where member is shooter or victim
    db.query(Assists).filter(Assists.shooter_id == member_id).delete()
    db.query(Assists).filter(Assists.victim_id == member_id).delete()
    
    # Delete member
    db.delete(member)
    db.commit()
    
    return {"detail": "Member deleted successfully"}
