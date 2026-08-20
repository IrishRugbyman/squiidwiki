import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.core.enums import BusinessRole, BusinessStatus, BusinessType
from app.schemas.common import FuzzyDateField


class BusinessMemberIn(BaseModel):
    member_id: uuid.UUID
    role: BusinessRole


class BusinessMemberOut(BaseModel):
    member_id: uuid.UUID
    member_name: Optional[str] = None
    member_slug: Optional[str] = None
    role: BusinessRole


class BusinessCreate(BaseModel):
    universe_id: uuid.UUID
    name: str
    aliases: Optional[list[str]] = None
    business_type: BusinessType
    description: Optional[str] = None
    status: BusinessStatus = BusinessStatus.ACTIVE
    municipality_id: Optional[uuid.UUID] = None
    founded_at: FuzzyDateField = None
    ended_at: FuzzyDateField = None
    members: list[BusinessMemberIn] = []
    set_ids: list[uuid.UUID] = []
    source_ids: list[uuid.UUID] = []


class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    aliases: Optional[list[str]] = None
    business_type: Optional[BusinessType] = None
    description: Optional[str] = None
    status: Optional[BusinessStatus] = None
    municipality_id: Optional[uuid.UUID] = None
    founded_at: FuzzyDateField = None
    ended_at: FuzzyDateField = None
    members: Optional[list[BusinessMemberIn]] = None
    set_ids: Optional[list[uuid.UUID]] = None
    source_ids: Optional[list[uuid.UUID]] = None


class BusinessRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    universe_id: uuid.UUID
    name: str
    slug: Optional[str] = None
    aliases: Optional[list[str]] = None
    business_type: BusinessType
    description: Optional[str] = None
    status: BusinessStatus
    municipality_id: Optional[uuid.UUID] = None
    founded_at: FuzzyDateField = None
    ended_at: FuzzyDateField = None
    created_at: datetime
    updated_at: datetime


class BusinessReadDetail(BusinessRead):
    municipality_name: Optional[str] = None
    municipality_slug: Optional[str] = None
    members: list[BusinessMemberOut] = []
    set_ids: list[uuid.UUID] = []
    source_ids: list[uuid.UUID] = []


class BusinessListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: Optional[str] = None
    aliases: Optional[list[str]] = None
    business_type: BusinessType
    status: BusinessStatus
    universe_id: uuid.UUID
    municipality_id: Optional[uuid.UUID] = None
    municipality_name: Optional[str] = None
    member_count: int = 0
