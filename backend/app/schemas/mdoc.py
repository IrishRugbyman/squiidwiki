import uuid
from typing import Optional

from pydantic import BaseModel

from app.schemas.common import FuzzyDateField


class MdocLookupRequest(BaseModel):
    url: str


class MdocProfileResponse(BaseModel):
    legal_name: str
    dob: FuzzyDateField
    earliest_release_date: FuzzyDateField = None
    max_discharge_date: FuzzyDateField = None
    facility: Optional[str] = None
    photo_url: Optional[str] = None


class MdocPhotoImportRequest(BaseModel):
    photo_url: str
    member_id: uuid.UUID
    universe_id: uuid.UUID
