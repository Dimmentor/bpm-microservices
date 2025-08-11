from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Enum
from sqlalchemy.sql import func
from src.db.database import Base
import enum


class EventType(enum.Enum):
    TASK = "task"
    MEETING = "meeting"
    PERSONAL = "personal"
    HOLIDAY = "holiday"
    OTHER = "other"


class EventStatus(enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # Владелец события
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(Enum(EventType), default=EventType.OTHER)
    status = Column(Enum(EventStatus), default=EventStatus.SCHEDULED)

    # Время события
    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True), nullable=False)

    # Связи с другими сервисами
    task_id = Column(Integer, nullable=True)  # Связь с задачей
    meeting_id = Column(Integer, nullable=True)  # Связь со встречей
    team_id = Column(Integer, nullable=True)  # Команда
    org_unit_id = Column(Integer, nullable=True)  # Подразделение

    # Дополнительные поля
    location = Column(String, nullable=True)
    is_all_day = Column(Boolean, default=False)
    is_recurring = Column(Boolean, default=False)
    recurring_pattern = Column(String, nullable=True)  # daily, weekly, monthly
    recurring_end_date = Column(DateTime(timezone=True), nullable=True)

    # Участники (JSON массив user_id)
    participants = Column(String, nullable=True)  # JSON array of user IDs

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class UserAvailability(Base):
    __tablename__ = "user_availability"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)

    # Рабочие часы
    work_start_time = Column(String, default="09:00")  # HH:MM
    work_end_time = Column(String, default="18:00")  # HH:MM

    # Рабочие дни (битовая маска: 1=понедельник, 2=вторник, ..., 64=воскресенье)
    work_days = Column(Integer, default=31)  # 31 = пн-пт (1+2+4+8+16)

    # Перерывы
    lunch_start = Column(String, default="13:00")
    lunch_end = Column(String, default="14:00")

    # Временная зона
    timezone = Column(String, default="UTC")

    # Настройки доступности
    is_available = Column(Boolean, default=True)
    auto_decline_conflicts = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TimeSlot(Base):
    __tablename__ = "time_slots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)  # Дата (без времени)
    start_time = Column(String, nullable=False)  # HH:MM
    end_time = Column(String, nullable=False)  # HH:MM
    is_available = Column(Boolean, default=True)
    event_id = Column(Integer, nullable=True)  # Если занято событием

    created_at = Column(DateTime(timezone=True), server_default=func.now())