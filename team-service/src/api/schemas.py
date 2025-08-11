from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None
    owner_id: Optional[int] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class TeamOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: Optional[int]
    invite_code: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


class OrgUnitCreate(BaseModel):
    team_id: int
    name: str
    parent_id: Optional[int] = None
    description: Optional[str] = None
    level: Optional[int] = 1


class OrgUnitUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    level: Optional[int] = None
    is_active: Optional[bool] = None


class OrgUnitOut(BaseModel):
    id: int
    team_id: int
    name: str
    parent_id: Optional[int]
    description: Optional[str]
    level: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


class OrgMemberCreate(BaseModel):
    user_id: int
    org_unit_id: int
    position: Optional[str] = None
    manager_id: Optional[int] = None


class OrgMemberUpdate(BaseModel):
    position: Optional[str] = None
    manager_id: Optional[int] = None
    is_active: Optional[bool] = None
    end_date: Optional[datetime] = None


class OrgMemberOut(BaseModel):
    id: int
    user_id: int
    org_unit_id: int
    position: Optional[str]
    manager_id: Optional[int]
    is_active: bool
    start_date: datetime
    end_date: Optional[datetime]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TeamNewsCreate(BaseModel):
    team_id: int
    author_id: int
    title: str
    content: str
    is_published: Optional[bool] = True


class TeamNewsUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_published: Optional[bool] = None


class TeamNewsOut(BaseModel):
    id: int
    team_id: int
    author_id: int
    title: str
    content: str
    is_published: bool
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)
