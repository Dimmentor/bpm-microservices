from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Float, Enum, Boolean
from sqlalchemy.sql import func
from src.db.database import Base
import enum

class TaskStatus(enum.Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskPriority(enum.Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    creator_id = Column(Integer, nullable=False)  # user-service id
    assignee_id = Column(Integer, nullable=True)  # user-service id
    team_id = Column(Integer, nullable=True)
    org_unit_id = Column(Integer, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.CREATED)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    due_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TaskComment(Base):
    __tablename__ = "task_comments"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, nullable=False)
    author_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)  # Внутренний комментарий
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TaskEvaluation(Base):
    __tablename__ = "task_evaluations"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, nullable=False)
    evaluator_id = Column(Integer, nullable=False)
    criteria = Column(JSON, nullable=False)
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    creator_id = Column(Integer, nullable=False)
    team_id = Column(Integer, nullable=True)
    org_unit_id = Column(Integer, nullable=True)
    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True), nullable=False)
    location = Column(String, nullable=True)
    meeting_type = Column(String, default="general")  # general, standup, review, etc.
    is_recurring = Column(Boolean, default=False)
    recurring_pattern = Column(String, nullable=True)  # daily, weekly, monthly
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    status = Column(String, default="pending")  # pending, accepted, declined, attended
    role = Column(String, default="participant")  # participant, organizer, presenter
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserPerformance(Base):
    __tablename__ = "user_performance"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    team_id = Column(Integer, nullable=True)
    org_unit_id = Column(Integer, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=False)  # Начало периода (квартал)
    period_end = Column(DateTime(timezone=True), nullable=False)    # Конец периода
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    total_score = Column(Float, default=0.0)
    evaluations_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
