"""HTML page routes."""
from fastapi import APIRouter, Request, Depends, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import check_auth, create_session_token, verify_password, get_password_hash
from app.config import settings
from app.crud import member as member_crud
from app.crud import set as set_crud
from app.crud import alliance as alliance_crud
from app.crud import incident as incident_crud
from app.crud import source as source_crud

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


# Middleware-like check for auth on protected routes
def require_login(request: Request):
    """Redirect to login if not authenticated."""
    if not check_auth(request):
        return RedirectResponse(url="/login", status_code=302)
    return None


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(request: Request, password: str = Form(...)):
    """Process login."""
    # Simple password check (in production, use proper hashing)
    if password == settings.ADMIN_PASSWORD:
        response = RedirectResponse(url="/dashboard", status_code=302)
        token = create_session_token()
        response.set_cookie(key="session", value=token, httponly=True, max_age=86400 * 30)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid password"})


@router.get("/logout")
async def logout():
    """Logout."""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session")
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Dashboard page."""
    if redirect := require_login(request):
        return redirect
    
    # Get summary stats
    total_members = len(member_crud.get_members(db, limit=10000))
    total_sets = len(set_crud.get_sets(db, limit=10000))
    total_alliances = len(alliance_crud.get_alliances(db, limit=10000))
    total_incidents = len(incident_crud.get_incidents(db, limit=10000))
    
    # Get recent incidents
    recent_incidents = incident_crud.get_incidents(db, limit=10)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total_members": total_members,
        "total_sets": total_sets,
        "total_alliances": total_alliances,
        "total_incidents": total_incidents,
        "recent_incidents": recent_incidents
    })


@router.get("/members", response_class=HTMLResponse)
async def members_list(request: Request, search: str = None, db: Session = Depends(get_db)):
    """Members list page."""
    if redirect := require_login(request):
        return redirect
    
    if search:
        members = member_crud.search_members(db, search)
    else:
        members = member_crud.get_members(db, limit=100)
    
    return templates.TemplateResponse("members/list.html", {
        "request": request,
        "members": members,
        "search": search or ""
    })


@router.get("/members/{member_id}", response_class=HTMLResponse)
async def member_detail(request: Request, member_id: str, db: Session = Depends(get_db)):
    """Member detail page."""
    if redirect := require_login(request):
        return redirect
    
    member = member_crud.get_member(db, member_id)
    if not member:
        return RedirectResponse(url="/members")
    
    stats = member_crud.get_member_stats(db, member_id)
    
    return templates.TemplateResponse("members/detail.html", {
        "request": request,
        "member": member,
        "stats": stats
    })


@router.get("/sets", response_class=HTMLResponse)
async def sets_list(request: Request, search: str = None, db: Session = Depends(get_db)):
    """Sets list page."""
    if redirect := require_login(request):
        return redirect
    
    if search:
        sets = set_crud.search_sets(db, search)
    else:
        sets = set_crud.get_sets(db, limit=100)
    
    return templates.TemplateResponse("sets/list.html", {
        "request": request,
        "sets": sets,
        "search": search or ""
    })


@router.get("/sets/{set_id}", response_class=HTMLResponse)
async def set_detail(request: Request, set_id: str, db: Session = Depends(get_db)):
    """Set detail page."""
    if redirect := require_login(request):
        return redirect
    
    set_obj = set_crud.get_set(db, set_id)
    if not set_obj:
        return RedirectResponse(url="/sets")
    
    return templates.TemplateResponse("sets/detail.html", {
        "request": request,
        "set": set_obj
    })


@router.get("/alliances", response_class=HTMLResponse)
async def alliances_list(request: Request, search: str = None, db: Session = Depends(get_db)):
    """Alliances list page."""
    if redirect := require_login(request):
        return redirect
    
    if search:
        alliances = alliance_crud.search_alliances(db, search)
    else:
        alliances = alliance_crud.get_alliances(db, limit=100)
    
    return templates.TemplateResponse("alliances/list.html", {
        "request": request,
        "alliances": alliances,
        "search": search or ""
    })


@router.get("/alliances/{alliance_id}", response_class=HTMLResponse)
async def alliance_detail(request: Request, alliance_id: str, db: Session = Depends(get_db)):
    """Alliance detail page."""
    if redirect := require_login(request):
        return redirect
    
    alliance = alliance_crud.get_alliance(db, alliance_id)
    if not alliance:
        return RedirectResponse(url="/alliances")
    
    return templates.TemplateResponse("alliances/detail.html", {
        "request": request,
        "alliance": alliance
    })


@router.get("/incidents", response_class=HTMLResponse)
async def incidents_list(request: Request, search: str = None, db: Session = Depends(get_db)):
    """Incidents list page."""
    if redirect := require_login(request):
        return redirect
    
    if search:
        incidents = incident_crud.search_incidents(db, search)
    else:
        incidents = incident_crud.get_incidents(db, limit=100)
    
    return templates.TemplateResponse("incidents/list.html", {
        "request": request,
        "incidents": incidents,
        "search": search or ""
    })


@router.get("/incidents/{incident_id}", response_class=HTMLResponse)
async def incident_detail(request: Request, incident_id: str, db: Session = Depends(get_db)):
    """Incident detail page."""
    if redirect := require_login(request):
        return redirect
    
    incident = incident_crud.get_incident(db, incident_id)
    if not incident:
        return RedirectResponse(url="/incidents")
    
    return templates.TemplateResponse("incidents/detail.html", {
        "request": request,
        "incident": incident
    })


@router.get("/sources", response_class=HTMLResponse)
async def sources_list(request: Request, search: str = None, db: Session = Depends(get_db)):
    """Sources list page."""
    if redirect := require_login(request):
        return redirect
    
    if search:
        sources = source_crud.search_sources(db, search)
    else:
        sources = source_crud.get_sources(db, limit=100)
    
    return templates.TemplateResponse("sources/list.html", {
        "request": request,
        "sources": sources,
        "search": search or ""
    })


@router.get("/sources/{source_id}", response_class=HTMLResponse)
async def source_detail(request: Request, source_id: str, db: Session = Depends(get_db)):
    """Source detail page."""
    if redirect := require_login(request):
        return redirect
    
    source = source_crud.get_source(db, source_id)
    if not source:
        return RedirectResponse(url="/sources")
    
    return templates.TemplateResponse("sources/detail.html", {
        "request": request,
        "source": source
    })


@router.get("/graph", response_class=HTMLResponse)
async def graph_page(request: Request):
    """Network graph visualization page."""
    if redirect := require_login(request):
        return redirect
    
    return templates.TemplateResponse("graph.html", {"request": request})
