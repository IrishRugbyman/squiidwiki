"""CRUD operations for sources."""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceUpdate


def create_source(db: Session, source: SourceCreate) -> Source:
    """Create a new source."""
    db_source = Source(**source.model_dump())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source


def get_source(db: Session, source_id: str) -> Optional[Source]:
    """Get a source by ID."""
    return db.query(Source).filter(Source.id == source_id).first()


def get_sources(db: Session, skip: int = 0, limit: int = 100) -> List[Source]:
    """Get all sources with pagination."""
    return db.query(Source).offset(skip).limit(limit).all()


def update_source(db: Session, source_id: str, source: SourceUpdate) -> Optional[Source]:
    """Update a source."""
    db_source = get_source(db, source_id)
    if not db_source:
        return None
    
    for key, value in source.model_dump(exclude_unset=True).items():
        setattr(db_source, key, value)
    
    db.commit()
    db.refresh(db_source)
    return db_source


def delete_source(db: Session, source_id: str) -> bool:
    """Delete a source."""
    db_source = get_source(db, source_id)
    if not db_source:
        return False
    
    db.delete(db_source)
    db.commit()
    return True


def search_sources(db: Session, query: str, skip: int = 0, limit: int = 100) -> List[Source]:
    """Search sources by title, url, or notes."""
    search_pattern = f"%{query}%"
    return db.query(Source).filter(
        or_(
            Source.title.like(search_pattern),
            Source.url.like(search_pattern),
            Source.notes.like(search_pattern)
        )
    ).offset(skip).limit(limit).all()
