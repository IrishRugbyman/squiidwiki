from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from backend.database.imports import get_db, Sets, Members, Alliance
from backend.config.templates import templates


router = APIRouter()

@router.get("/")
async def read_root(request: Request, db: Session = Depends(get_db)):
    """Homepage with overview/dashboard"""
    # Count total sets, members, and alliances
    total_sets = db.query(Sets).count()
    total_members = db.query(Members).count()
    total_alliances = db.query(Alliance).count()
    
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "total_sets": total_sets,
            "total_members": total_members,
            "total_alliances": total_alliances
        }
    )