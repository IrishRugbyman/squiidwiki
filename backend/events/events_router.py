from fastapi import APIRouter
from backend.events.subrouters.murders_router import router as murders_router
from backend.events.subrouters.shootings_router import router as shootings_router
from backend.events.subrouters.assists_router import router as assists_router

router = APIRouter()

# Include subrouters with their respective prefixes
router.include_router(murders_router, prefix="/murders")
router.include_router(shootings_router, prefix="/shootings")
router.include_router(assists_router, prefix="/assists")