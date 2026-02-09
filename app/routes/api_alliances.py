"""API routes for alliances."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.alliance import AllianceCreate, AllianceUpdate, AllianceRead
from app.crud import alliance as crud

router = APIRouter(prefix="/api/alliances", tags=["alliances"])


@router.post("/", response_model=AllianceRead)
def create_alliance(alliance: AllianceCreate, db: Session = Depends(get_db)):
    """Create a new alliance."""
    return crud.create_alliance(db, alliance)


@router.get("/{alliance_id}", response_model=AllianceRead)
def get_alliance(alliance_id: str, db: Session = Depends(get_db)):
    """Get an alliance by ID."""
    db_alliance = crud.get_alliance(db, alliance_id)
    if not db_alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")
    return db_alliance


@router.get("/", response_model=List[AllianceRead])
def list_alliances(skip: int = 0, limit: int = 100, search: str = None, db: Session = Depends(get_db)):
    """List alliances with optional search."""
    if search:
        return crud.search_alliances(db, search, skip, limit)
    return crud.get_alliances(db, skip, limit)


@router.put("/{alliance_id}", response_model=AllianceRead)
def update_alliance(alliance_id: str, alliance: AllianceUpdate, db: Session = Depends(get_db)):
    """Update an alliance."""
    db_alliance = crud.update_alliance(db, alliance_id, alliance)
    if not db_alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")
    return db_alliance


@router.delete("/{alliance_id}")
def delete_alliance(alliance_id: str, db: Session = Depends(get_db)):
    """Delete an alliance."""
    if not crud.delete_alliance(db, alliance_id):
        raise HTTPException(status_code=404, detail="Alliance not found")
    return {"status": "deleted"}
