from sqlalchemy import Column, Integer, String, DateTime, Date, Text, JSON, Float, Enum, Boolean
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
    creator_id = Column(Integer, nullable=False)
    assignee_id = Column(Integer, nullable=True)
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
    is_internal = Column(Boolean, default=False)
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




class UserPerformance(Base):
    __tablename__ = "user_performance"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Основные метрики
    metrics = Column(JSON, nullable=False, default={
        "total_tasks": 0,
        "completed_tasks": 0,
        "average_scores": {
            "timeliness": 0.0,
            "quality": 0.0,
            "communication": 0.0
        },
        "total_score": 0.0
    })

    comparison = Column(JSON, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
