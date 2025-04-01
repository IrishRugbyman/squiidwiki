from fastapi import APIRouter, Request
from backend.database.database import get_total_sets, get_total_members, get_total_alliances
from backend.config.templates import templates


router = APIRouter()

@router.get("/")
async def read_root(request: Request):
    """Homepage with overview/dashboard"""
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "total_sets": get_total_sets(),
            "total_members": get_total_members(),
            "total_alliances": get_total_alliances()
        }
    )