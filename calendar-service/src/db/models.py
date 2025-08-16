from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum, JSON
from sqlalchemy.sql import func
from src.db.database import Base
import enum


class EventType(enum.Enum):
    TASK = "TASK"
    MEETING = "MEETING"
    PERSONAL = "PERSONAL"
    HOLIDAY = "HOLIDAY"
    OTHER = "OTHER"


class EventStatus(enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(Enum(EventType), nullable=False)
    status = Column(Enum(EventStatus), default=EventStatus.SCHEDULED)

    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True), nullable=False)
    is_all_day = Column(Boolean, default=False)
    is_recurring = Column(Boolean, default=False)
    recurring_pattern = Column(String, nullable=True)

    user_id = Column(Integer, nullable=False)  # Владелец события
    task_id = Column(Integer, nullable=True)  # Для событий-задач
    team_id = Column(Integer, nullable=True)  # Команда
    org_unit_id = Column(Integer, nullable=True)  # Подразделение

    location = Column(String, nullable=True)
    meeting_type = Column(String, nullable=True, default="general")
    participants = Column(JSON, nullable=True)  # Список ID участников

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class UserAvailability(Base):
    __tablename__ = "user_availability"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)

    work_start_time = Column(String, default="09:00")
    work_end_time = Column(String, default="18:00")

    work_days = Column(Integer, default=31)

    # Перерывы
    lunch_start = Column(String, default="13:00")
    lunch_end = Column(String, default="14:00")

    timezone = Column(String, default="UTC")

    is_available = Column(Boolean, default=True)
    auto_decline_conflicts = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TimeSlot(Base):
    __tablename__ = "time_slots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    is_available = Column(Boolean, default=True)
    event_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
