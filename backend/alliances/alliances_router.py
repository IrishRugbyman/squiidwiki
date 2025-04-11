from typing import List, Optional
from contextlib import contextmanager

from fastapi import APIRouter, Request, Form, HTTPException, Depends, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.config.templates import templates
from backend.alliances.schemas import AllianceOption, AllianceCreate, AllianceUpdate, AllianceResponse, SetInAlliance
from backend.database.imports import Alliance, AllianceSetsMap, Sets, Members, get_db
from backend.alliances.service.alliance_service import alliance_service

router = APIRouter()

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


@router.get("/", response_class=HTMLResponse)
def read_alliances(request: Request, db: Session = Depends(get_db)):
    alliances = db.query(Alliance).all()
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


@router.post("/add", response_class=HTMLResponse)
def add_alliance(
    request: Request,
    name: str = Form(...),
    description: str = Form(None),
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    with transaction_scope(db) as db:
        try:
            # Validate status
            if status not in ["active", "inactive"]:
                return templates.TemplateResponse(
                    "alliances/add_alliance.html",
                    {
                        "request": request,
                        "error": "Invalid status. Must be 'active' or 'inactive'."
                    }
                )
            
            # Check if alliance with the same name already exists
            existing_alliance = db.query(Alliance).filter(Alliance.name == name).first()
            if existing_alliance:
                return templates.TemplateResponse(
                    "alliances/add_alliance.html",
                    {
                        "request": request,
                        "error": f"Alliance with name '{name}' already exists."
                    }
                )
            
            # Create new alliance
            alliance = Alliance(
                name=name,
                description=description,
                status=status
            )
            db.add(alliance)
            
            # Redirect to the alliances list page
            response = RedirectResponse(url="/alliances", status_code=303)
            return response
        except Exception as e:
            return templates.TemplateResponse(
                "alliances/add_alliance.html",
                {
                    "request": request,
                    "error": f"Failed to add alliance: {str(e)}"
                }
            )


@router.get("/add_set/{alliance_id}", response_class=HTMLResponse)
def add_set_form(request: Request, alliance_id: int, db: Session = Depends(get_db)):
    alliance = db.get(Alliance, alliance_id)
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
        "alliances/add_alliance_set.html",
        {"request": request, "alliance": alliance_data, "available_sets": available_sets_data},
    )


@router.post("/add_set/{alliance_id}")
def add_set(
        alliance_id: int, set_id: int = Form(...), db: Session = Depends(get_db)
):
    set_obj = db.get(Sets, set_id)
    if not set_obj:
        raise HTTPException(status_code=400, detail="Invalid set ID")

    new_mapping = AllianceSetsMap(alliance_id=alliance_id, set_id=set_id)
    db.add(new_mapping)
    db.commit()
    return RedirectResponse(url=f"/alliances/{alliance_id}", status_code=303)


# Alias for backward compatibility
@router.get("/add_member/{alliance_id}", response_class=HTMLResponse)
def add_member_form(request: Request, alliance_id: int, db: Session = Depends(get_db)):
    return add_set_form(request, alliance_id, db)


@router.post("/add_member/{alliance_id}")
def add_member(
        alliance_id: int, set_id: int = Form(...), db: Session = Depends(get_db)
):
    return add_set(alliance_id, set_id, db)


@router.get("/options", response_model=List[AllianceOption])
def get_alliance_options(db: Session = Depends(get_db)):
    """
    Returns a list of active alliances.
    Each alliance is represented as a dictionary with keys 'id' and 'name'.
    """
    alliances = db.query(Alliance).filter(Alliance.status == "active").all()
    return [AllianceOption(id=alliance.id, name=alliance.name) for alliance in alliances]


@router.get("/api/options", response_class=JSONResponse)
def api_get_alliance_options(db: Session = Depends(get_db)):
    """
    API endpoint that returns a list of active alliances.
    Each alliance is represented as a dictionary with keys 'id' and 'name'.
    """
    alliances = db.query(Alliance).filter(Alliance.status == "active").all()
    alliance_options = [{"id": alliance.id, "name": alliance.name} for alliance in alliances]
    return alliance_options


@router.get("/{alliance_id}", response_class=HTMLResponse)
def read_alliance(request: Request, alliance_id: int, db: Session = Depends(get_db)):
    alliance = db.get(Alliance, alliance_id)
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
            "members_count": db.query(Members).filter(Members.set_id == s.id).count()
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
    alliance = db.get(Alliance, alliance_id)
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


@router.post("/edit/{alliance_id}", response_class=HTMLResponse)
def edit_alliance(
    request: Request,
    alliance_id: int,
    name: str = Form(...),
    status: str = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    with transaction_scope(db) as db:
        try:
            # Validate status
            if status not in ["active", "inactive"]:
                return templates.TemplateResponse(
                    "alliances/edit_alliance.html",
                    {
                        "request": request,
                        "alliance": db.query(Alliance).filter(Alliance.id == alliance_id).first(),
                        "error": "Status must be either 'active' or 'inactive'"
                    }
                )
            
            # Check if alliance exists
            alliance = db.query(Alliance).filter(Alliance.id == alliance_id).first()
            if not alliance:
                return templates.TemplateResponse(
                    "alliances/index.html",
                    {
                        "request": request,
                        "alliances": db.query(Alliance).all(),
                        "error": f"Alliance with ID {alliance_id} not found."
                    }
                )
            
            # Check if name already exists for another alliance
            existing_alliance = db.query(Alliance).filter(
                Alliance.name == name,
                Alliance.id != alliance_id
            ).first()
            
            if existing_alliance:
                return templates.TemplateResponse(
                    "alliances/edit_alliance.html",
                    {
                        "request": request,
                        "alliance": alliance,
                        "error": "An alliance with this name already exists."
                    }
                )
            
            # Update alliance details
            alliance.name = name
            alliance.status = status
            alliance.description = description
            
            # Redirect to alliance list
            response = RedirectResponse(url="/alliances", status_code=303)
            return response
        except Exception as e:
            # Handle any exceptions and return error
            return templates.TemplateResponse(
                "alliances/edit_alliance.html",
                {
                    "request": request,
                    "alliance": alliance,
                    "error": f"Failed to update alliance: {str(e)}"
                }
            )


@router.post("/delete/{alliance_id}", response_class=HTMLResponse)
def delete_alliance(
    request: Request,
    alliance_id: int,
    db: Session = Depends(get_db)
):
    with transaction_scope(db) as db:
        try:
            # Find the alliance
            alliance = db.query(Alliance).filter(Alliance.id == alliance_id).first()
            if not alliance:
                # Alliance not found, redirect to alliances list with an error
                return templates.TemplateResponse(
                    "alliances/index.html",
                    {
                        "request": request,
                        "alliances": db.query(Alliance).all(),
                        "error": f"Alliance with ID {alliance_id} not found."
                    }
                )
            
            # First delete alliance-set mappings
            db.query(AllianceSetsMap).filter(AllianceSetsMap.alliance_id == alliance_id).delete()
            
            # Delete the alliance
            db.query(Alliance).filter(Alliance.id == alliance_id).delete()
            
            # Redirect to alliance list
            response = RedirectResponse(url="/alliances", status_code=303)
            return response
        except Exception as e:
            # Handle any exceptions and return error
            alliances = db.query(Alliance).all()
            return templates.TemplateResponse(
                "alliances/index.html",
                {
                    "request": request,
                    "alliances": alliances,
                    "error": f"Failed to delete alliance: {str(e)}"
                }
            )


@router.get("/delete/{alliance_id}", response_class=HTMLResponse)
def delete_alliance_confirmation(
    request: Request,
    alliance_id: int,
    db: Session = Depends(get_db)
):
    try:
        alliance = db.query(Alliance).filter(Alliance.id == alliance_id).first()
        if not alliance:
            return templates.TemplateResponse(
                "alliances/delete_alliance.html",
                {
                    "request": request,
                    "error": "Alliance not found"
                }
            )
        
        # Count members in this alliance
        member_sets_count = db.query(AllianceSetsMap).filter(AllianceSetsMap.alliance_id == alliance_id).count()
        
        return templates.TemplateResponse(
            "alliances/delete_alliance.html",
            {
                "request": request,
                "alliance": alliance,
                "member_sets_count": member_sets_count
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "alliances/delete_alliance.html",
            {
                "request": request,
                "error": str(e)
            }
        )


@router.post("/remove_set", response_class=JSONResponse)
def remove_alliance_set(
    alliance_id: int = Body(...), 
    set_id: int = Body(...),
    db: Session = Depends(get_db)
):
    # Find the mapping entry
    mapping = db.query(AllianceSetsMap).filter(
        AllianceSetsMap.alliance_id == alliance_id,
        AllianceSetsMap.set_id == set_id
    ).first()
    
    if not mapping:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Association not found"}
        )
    
    db.delete(mapping)
    db.commit()

    return JSONResponse(
        content={"success": True, "message": "Set removed from alliance successfully"}
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
        raise HTTPException(status_code=404, detail="Alliance-set association not found")
    
    db.delete(mapping)
    db.commit()
    
    return RedirectResponse(url=f"/alliances/{alliance_id}", status_code=303)


# API Endpoints for AJAX operations

@router.delete("/{alliance_id}", response_class=JSONResponse)
def api_delete_alliance(alliance_id: int, db: Session = Depends(get_db)):
    alliance = db.get(Alliance, alliance_id)
    if not alliance:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Alliance not found"}
        )
    
    # Delete alliance
    db.delete(alliance)
    db.commit()
    
    return JSONResponse(
        content={"success": True, "message": "Alliance deleted successfully"}
    )


@router.get("/api/activity", response_class=JSONResponse)
def get_recent_activity(db: Session = Depends(get_db)):
    # This is a placeholder for actual activity data
    # In a real implementation, you would query from an activity log table
    return JSONResponse(content={
        "success": True,
        "activities": [
            {
                "type": "alliance_created",
                "entity_id": 1,
                "entity_name": "Sample Alliance",
                "timestamp": "2023-04-01T12:30:00Z",
                "actor": "Admin"
            },
            {
                "type": "set_added",
                "entity_id": 2,
                "entity_name": "Sample Set",
                "timestamp": "2023-04-01T12:35:00Z",
                "actor": "Admin"
            }
        ]
    })


# API Endpoints for Alliances
@router.get("/api/alliances", response_model=List[AllianceResponse])
def api_get_alliances(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """API endpoint to get all alliances with pagination"""
    alliances = alliance_service.get_multi(db, skip=skip, limit=limit)
    return alliances


@router.get("/api/alliances/{alliance_id}", response_model=AllianceResponse)
def api_get_alliance(alliance_id: int, db: Session = Depends(get_db)):
    """API endpoint to get an alliance by ID"""
    alliance = alliance_service.get(db, alliance_id)
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")
    return alliance


@router.post("/api/alliances", response_model=AllianceResponse)
def api_create_alliance(alliance: AllianceCreate, db: Session = Depends(get_db)):
    """API endpoint to create a new alliance"""
    return alliance_service.create_alliance(db, alliance)


@router.put("/api/alliances/{alliance_id}", response_model=AllianceResponse)
def api_update_alliance(
    alliance_id: int, 
    alliance: AllianceUpdate, 
    db: Session = Depends(get_db)
):
    """API endpoint to update an alliance"""
    updated_alliance = alliance_service.update_alliance(db, alliance_id, alliance)
    if not updated_alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")
    return updated_alliance


@router.delete("/api/alliances/{alliance_id}", response_model=bool)
def api_delete_alliance(alliance_id: int, db: Session = Depends(get_db)):
    """API endpoint to delete an alliance"""
    success = alliance_service.remove(db, id=alliance_id)
    return True


@router.post("/api/alliances/{alliance_id}/sets/{set_id}", response_model=AllianceResponse)
def api_add_set_to_alliance(
    alliance_id: int, 
    set_id: int, 
    db: Session = Depends(get_db)
):
    """API endpoint to add a set to an alliance"""
    updated_alliance = alliance_service.add_set_to_alliance(db, alliance_id, set_id)
    return updated_alliance


@router.delete("/api/alliances/{alliance_id}/sets/{set_id}", response_model=AllianceResponse)
def api_remove_set_from_alliance(
    alliance_id: int, 
    set_id: int, 
    db: Session = Depends(get_db)
):
    """API endpoint to remove a set from an alliance"""
    updated_alliance = alliance_service.remove_set_from_alliance(db, alliance_id, set_id)
    return updated_alliance


@router.get("/api/alliances/{alliance_id}/sets", response_model=List[SetInAlliance])
def api_get_alliance_sets(alliance_id: int, db: Session = Depends(get_db)):
    """API endpoint to get all sets in an alliance"""
    sets = alliance_service.get_sets_in_alliance(db, alliance_id)
    if sets == []:
        raise HTTPException(status_code=404, detail="Alliance not found")
    return sets


@router.get("/api/alliances/{alliance_id}/available-sets", response_model=List[SetInAlliance])
def api_get_available_sets(alliance_id: int, db: Session = Depends(get_db)):
    """API endpoint to get sets not in an alliance"""
    sets = alliance_service.get_available_sets_for_alliance(db, alliance_id)
    if sets == []:
        raise HTTPException(status_code=404, detail="Alliance not found")
    return sets
