"""API routes for sets."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.set import SetCreate, SetUpdate, SetRead
from app.crud import set as crud

router = APIRouter(prefix="/api/sets", tags=["sets"])


@router.post("/", response_model=SetRead)
def create_set(set_data: SetCreate, db: Session = Depends(get_db)):
    """Create a new set."""
    return crud.create_set(db, set_data)


@router.get("/{set_id}", response_model=SetRead)
def get_set(set_id: str, db: Session = Depends(get_db)):
    """Get a set by ID."""
    db_set = crud.get_set(db, set_id)
    if not db_set:
        raise HTTPException(status_code=404, detail="Set not found")
    return db_set


@router.get("/", response_model=List[SetRead])
def list_sets(skip: int = 0, limit: int = 100, search: str = None, db: Session = Depends(get_db)):
    """List sets with optional search."""
    if search:
        return crud.search_sets(db, search, skip, limit)
    return crud.get_sets(db, skip, limit)


@router.put("/{set_id}", response_model=SetRead)
def update_set(set_id: str, set_data: SetUpdate, db: Session = Depends(get_db)):
    """Update a set."""
    db_set = crud.update_set(db, set_id, set_data)
    if not db_set:
        raise HTTPException(status_code=404, detail="Set not found")
    return db_set


@router.delete("/{set_id}")
def delete_set(set_id: str, db: Session = Depends(get_db)):
    """Delete a set."""
    if not crud.delete_set(db, set_id):
        raise HTTPException(status_code=404, detail="Set not found")
    return {"status": "deleted"}


@router.post("/{set_id}/allies/{ally_id}")
def add_ally(set_id: str, ally_id: str, db: Session = Depends(get_db)):
    """Add an ally relationship."""
    if not crud.add_ally(db, set_id, ally_id):
        raise HTTPException(status_code=400, detail="Cannot add ally (conflict or same set)")
    return {"status": "ally added"}


@router.delete("/{set_id}/allies/{ally_id}")
def remove_ally(set_id: str, ally_id: str, db: Session = Depends(get_db)):
    """Remove an ally relationship."""
    if not crud.remove_ally(db, set_id, ally_id):
        raise HTTPException(status_code=404, detail="Ally relationship not found")
    return {"status": "ally removed"}


@router.post("/{set_id}/enemies/{enemy_id}")
def add_enemy(set_id: str, enemy_id: str, db: Session = Depends(get_db)):
    """Add an enemy relationship."""
    if not crud.add_enemy(db, set_id, enemy_id):
        raise HTTPException(status_code=400, detail="Cannot add enemy (conflict or same set)")
    return {"status": "enemy added"}


@router.delete("/{set_id}/enemies/{enemy_id}")
def remove_enemy(set_id: str, enemy_id: str, db: Session = Depends(get_db)):
    """Remove an enemy relationship."""
    if not crud.remove_enemy(db, set_id, enemy_id):
        raise HTTPException(status_code=404, detail="Enemy relationship not found")
    return {"status": "enemy removed"}
