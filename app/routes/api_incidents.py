"""API routes for incidents."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.incident import IncidentCreate, IncidentUpdate, IncidentRead
from app.crud import incident as crud

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.post("/", response_model=IncidentRead)
def create_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    """Create a new incident."""
    return crud.create_incident(db, incident)


@router.get("/{incident_id}", response_model=IncidentRead)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    """Get an incident by ID."""
    db_incident = crud.get_incident(db, incident_id)
    if not db_incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return db_incident


@router.get("/", response_model=List[IncidentRead])
def list_incidents(skip: int = 0, limit: int = 100, search: str = None, db: Session = Depends(get_db)):
    """List incidents with optional search."""
    if search:
        return crud.search_incidents(db, search, skip, limit)
    return crud.get_incidents(db, skip, limit)


@router.put("/{incident_id}", response_model=IncidentRead)
def update_incident(incident_id: str, incident: IncidentUpdate, db: Session = Depends(get_db)):
    """Update an incident."""
    db_incident = crud.update_incident(db, incident_id, incident)
    if not db_incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return db_incident


@router.delete("/{incident_id}")
def delete_incident(incident_id: str, db: Session = Depends(get_db)):
    """Delete an incident."""
    if not crud.delete_incident(db, incident_id):
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"status": "deleted"}
