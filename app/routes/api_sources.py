"""API routes for sources."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.source import SourceCreate, SourceUpdate, SourceRead
from app.crud import source as crud

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.post("/", response_model=SourceRead)
def create_source(source: SourceCreate, db: Session = Depends(get_db)):
    """Create a new source."""
    return crud.create_source(db, source)


@router.get("/{source_id}", response_model=SourceRead)
def get_source(source_id: str, db: Session = Depends(get_db)):
    """Get a source by ID."""
    db_source = crud.get_source(db, source_id)
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")
    return db_source


@router.get("/", response_model=List[SourceRead])
def list_sources(skip: int = 0, limit: int = 100, search: str = None, db: Session = Depends(get_db)):
    """List sources with optional search."""
    if search:
        return crud.search_sources(db, search, skip, limit)
    return crud.get_sources(db, skip, limit)


@router.put("/{source_id}", response_model=SourceRead)
def update_source(source_id: str, source: SourceUpdate, db: Session = Depends(get_db)):
    """Update a source."""
    db_source = crud.update_source(db, source_id, source)
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")
    return db_source


@router.delete("/{source_id}")
def delete_source(source_id: str, db: Session = Depends(get_db)):
    """Delete a source."""
    if not crud.delete_source(db, source_id):
        raise HTTPException(status_code=404, detail="Source not found")
    return {"status": "deleted"}
