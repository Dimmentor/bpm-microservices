from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from src.db.models import EventType, EventStatus


class CalendarEventCreate(BaseModel):
    user_id: int
    title: str
    description: Optional[str] = None
    event_type: EventType = EventType.OTHER
    start_at: datetime
    end_at: datetime
    task_id: Optional[int] = None
    team_id: Optional[int] = None
    org_unit_id: Optional[int] = None
    location: Optional[str] = None
    is_all_day: bool = False
    is_recurring: bool = False
    recurring_pattern: Optional[str] = None
    participants: Optional[List[int]] = None


class CalendarEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    status: Optional[EventStatus] = None
    location: Optional[str] = None
    is_all_day: Optional[bool] = None
    participants: Optional[List[int]] = None


class CalendarEventOut(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    event_type: EventType
    status: EventStatus
    start_at: datetime
    end_at: datetime
    task_id: Optional[int]
    team_id: Optional[int]
    org_unit_id: Optional[int]
    location: Optional[str]
    is_all_day: bool
    is_recurring: bool
    recurring_pattern: Optional[str]
    participants: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


class UserAvailabilityCreate(BaseModel):
    user_id: int
    work_start_time: str = "09:00"
    work_end_time: str = "18:00"
    work_days: int = 31
    lunch_start: str = "13:00"
    lunch_end: str = "14:00"
    timezone: str = "UTC"
    is_available: bool = True
    auto_decline_conflicts: bool = False


class UserAvailabilityUpdate(BaseModel):
    work_start_time: Optional[str] = None
    work_end_time: Optional[str] = None
    work_days: Optional[int] = None
    lunch_start: Optional[str] = None
    lunch_end: Optional[str] = None
    timezone: Optional[str] = None
    is_available: Optional[bool] = None
    auto_decline_conflicts: Optional[bool] = None


class UserAvailabilityOut(BaseModel):
    id: int
    user_id: int
    work_start_time: str
    work_end_time: str
    work_days: int
    lunch_start: str
    lunch_end: str
    timezone: str
    is_available: bool
    auto_decline_conflicts: bool
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


class TimeSlotCreate(BaseModel):
    user_id: int
    date: date
    start_time: str
    end_time: str
    is_available: bool = True
    event_id: Optional[int] = None


class TimeSlotOut(BaseModel):
    id: int
    user_id: int
    date: datetime
    start_time: str
    end_time: str
    is_available: bool
    event_id: Optional[int]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AvailabilityCheck(BaseModel):
    user_id: int
    start_at: datetime
    end_at: datetime


class AvailabilityResponse(BaseModel):
    is_available: bool
    conflicts: List[CalendarEventOut] = []
    suggested_times: List[dict] = []


class CalendarView(BaseModel):
    user_id: int
    start_date: date
    end_date: date
    include_team_events: bool = False
    team_id: Optional[int] = None
