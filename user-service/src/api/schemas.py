from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime
from src.db.models import UserStatus, UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    invite_code: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    status: Optional[UserStatus] = None
    role: Optional[UserRole] = None


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str]
    role: UserRole
    status: UserStatus
    team_id: Optional[int]
    phone: Optional[str]
    position: Optional[str]
    department: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserLogin(BaseModel):
    email: EmailStr
    password: str
