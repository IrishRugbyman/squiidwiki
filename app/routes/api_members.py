"""API routes for members."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.member import MemberCreate, MemberUpdate, MemberRead
from app.crud import member as crud

router = APIRouter(prefix="/api/members", tags=["members"])


@router.post("/", response_model=MemberRead)
def create_member(member: MemberCreate, db: Session = Depends(get_db)):
    """Create a new member."""
    return crud.create_member(db, member)


@router.get("/{member_id}", response_model=MemberRead)
def get_member(member_id: str, db: Session = Depends(get_db)):
    """Get a member by ID."""
    db_member = crud.get_member(db, member_id)
    if not db_member:
        raise HTTPException(status_code=404, detail="Member not found")
    return db_member


@router.get("/", response_model=List[MemberRead])
def list_members(skip: int = 0, limit: int = 100, search: str = None, db: Session = Depends(get_db)):
    """List members with optional search."""
    if search:
        return crud.search_members(db, search, skip, limit)
    return crud.get_members(db, skip, limit)


@router.put("/{member_id}", response_model=MemberRead)
def update_member(member_id: str, member: MemberUpdate, db: Session = Depends(get_db)):
    """Update a member."""
    db_member = crud.update_member(db, member_id, member)
    if not db_member:
        raise HTTPException(status_code=404, detail="Member not found")
    return db_member


@router.delete("/{member_id}")
def delete_member(member_id: str, db: Session = Depends(get_db)):
    """Delete a member."""
    if not crud.delete_member(db, member_id):
        raise HTTPException(status_code=404, detail="Member not found")
    return {"status": "deleted"}


@router.get("/{member_id}/stats")
def get_member_stats(member_id: str, db: Session = Depends(get_db)):
    """Get member statistics."""
    db_member = crud.get_member(db, member_id)
    if not db_member:
        raise HTTPException(status_code=404, detail="Member not found")
    return crud.get_member_stats(db, member_id)
