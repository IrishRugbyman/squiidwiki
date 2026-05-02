from typing import Annotated

from fastapi import APIRouter
from pydantic import BaseModel

from app.auth.dependencies import require_global_role
from app.core.database import DbMode, get_db_mode, set_db_mode
from app.core.enums import GlobalRole

router = APIRouter(prefix="/admin", tags=["admin"])

_admin = require_global_role(GlobalRole.ADMIN)


class DbModeResponse(BaseModel):
    mode: DbMode


@router.get("/db-mode", response_model=DbModeResponse)
async def read_db_mode(_: Annotated[None, _admin]) -> DbModeResponse:
    return DbModeResponse(mode=get_db_mode())


@router.post("/db-mode", response_model=DbModeResponse)
async def write_db_mode(mode: DbMode, _: Annotated[None, _admin]) -> DbModeResponse:
    set_db_mode(mode)
    return DbModeResponse(mode=get_db_mode())
