"""CRUD operations for alliances."""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from app.models.alliance import Alliance
from app.schemas.alliance import AllianceCreate, AllianceUpdate


def create_alliance(db: Session, alliance: AllianceCreate) -> Alliance:
    """Create a new alliance."""
    db_alliance = Alliance(**alliance.model_dump())
    db.add(db_alliance)
    db.commit()
    db.refresh(db_alliance)
    return db_alliance


def get_alliance(db: Session, alliance_id: str) -> Optional[Alliance]:
    """Get an alliance by ID."""
    return db.query(Alliance).filter(Alliance.id == alliance_id).first()


def get_alliances(db: Session, skip: int = 0, limit: int = 100) -> List[Alliance]:
    """Get all alliances with pagination."""
    return db.query(Alliance).offset(skip).limit(limit).all()


def update_alliance(db: Session, alliance_id: str, alliance: AllianceUpdate) -> Optional[Alliance]:
    """Update an alliance."""
    db_alliance = get_alliance(db, alliance_id)
    if not db_alliance:
        return None
    
    for key, value in alliance.model_dump(exclude_unset=True).items():
        setattr(db_alliance, key, value)
    
    db.commit()
    db.refresh(db_alliance)
    return db_alliance


def delete_alliance(db: Session, alliance_id: str) -> bool:
    """Delete an alliance."""
    db_alliance = get_alliance(db, alliance_id)
    if not db_alliance:
        return False
    
    db.delete(db_alliance)
    db.commit()
    return True


def search_alliances(db: Session, query: str, skip: int = 0, limit: int = 100) -> List[Alliance]:
    """Search alliances by name or bio."""
    search_pattern = f"%{query}%"
    return db.query(Alliance).filter(
        or_(
            Alliance.name.like(search_pattern),
            Alliance.bio.like(search_pattern)
        )
    ).offset(skip).limit(limit).all()
