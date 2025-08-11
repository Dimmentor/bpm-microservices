from pydantic import BaseModel, ConfigDict
from typing import Optional


class TeamCreate(BaseModel):
    name: str


class TeamOut(BaseModel):
    id: int
    name: str
    invite_code: Optional[str]
    model_config = ConfigDict(from_attributes=True)


class OrgUnitCreate(BaseModel):
    team_id: int
    name: str
    parent_id: Optional[int] = None
    description: Optional[str] = None


class OrgMemberCreate(BaseModel):
    user_id: int
    org_unit_id: int
    position: Optional[str]
    manager_id: Optional[int]
