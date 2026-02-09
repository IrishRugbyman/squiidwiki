"""CRUD operations for incidents."""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from app.models.incident import Incident, IncidentParticipant
from app.schemas.incident import IncidentCreate, IncidentUpdate


def create_incident(db: Session, incident: IncidentCreate) -> Incident:
    """Create a new incident with participants."""
    incident_data = incident.model_dump(exclude={'participants'})
    db_incident = Incident(**incident_data)
    db.add(db_incident)
    db.flush()  # Get incident ID before adding participants
    
    # Add participants
    for participant in incident.participants:
        db_participant = IncidentParticipant(
            incident_id=db_incident.id,
            **participant.model_dump()
        )
        db.add(db_participant)
    
    db.commit()
    db.refresh(db_incident)
    return db_incident


def get_incident(db: Session, incident_id: str) -> Optional[Incident]:
    """Get an incident by ID."""
    return db.query(Incident).filter(Incident.id == incident_id).first()


def get_incidents(db: Session, skip: int = 0, limit: int = 100) -> List[Incident]:
    """Get all incidents with pagination."""
    return db.query(Incident).offset(skip).limit(limit).all()


def update_incident(db: Session, incident_id: str, incident: IncidentUpdate) -> Optional[Incident]:
    """Update an incident."""
    db_incident = get_incident(db, incident_id)
    if not db_incident:
        return None
    
    for key, value in incident.model_dump(exclude_unset=True).items():
        setattr(db_incident, key, value)
    
    db.commit()
    db.refresh(db_incident)
    return db_incident


def delete_incident(db: Session, incident_id: str) -> bool:
    """Delete an incident."""
    db_incident = get_incident(db, incident_id)
    if not db_incident:
        return False
    
    db.delete(db_incident)
    db.commit()
    return True


def search_incidents(db: Session, query: str, skip: int = 0, limit: int = 100) -> List[Incident]:
    """Search incidents by location or description."""
    search_pattern = f"%{query}%"
    return db.query(Incident).filter(
        or_(
            Incident.location.like(search_pattern),
            Incident.description.like(search_pattern)
        )
    ).offset(skip).limit(limit).all()
