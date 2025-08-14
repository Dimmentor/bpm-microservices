from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime
from src.db.models import TaskStatus, TaskPriority


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    creator_id: int
    assignee_id: Optional[int] = None
    team_id: Optional[int] = None
    org_unit_id: Optional[int] = None
    priority: Optional[TaskPriority] = TaskPriority.MEDIUM
    due_at: Optional[datetime] = None
    estimated_hours: Optional[float] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_at: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    creator_id: int
    assignee_id: Optional[int]
    team_id: Optional[int]
    org_unit_id: Optional[int]
    status: TaskStatus
    priority: TaskPriority
    due_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


class CommentCreate(BaseModel):
    task_id: int
    author_id: int
    text: str
    is_internal: Optional[bool] = False


class CommentOut(BaseModel):
    id: int
    task_id: int
    author_id: int
    text: str
    is_internal: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EvaluationCreate(BaseModel):
    evaluator_id: int
    criteria: Dict[str, int]
    feedback: Optional[str] = None


class EvaluationOut(BaseModel):
    id: int
    task_id: int
    evaluator_id: int
    criteria: Dict[str, int]
    score: Optional[float]
    feedback: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MeetingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    creator_id: int
    team_id: Optional[int] = None
    org_unit_id: Optional[int] = None
    start_at: datetime
    end_at: datetime
    location: Optional[str] = None
    meeting_type: Optional[str] = "general"
    is_recurring: Optional[bool] = False
    recurring_pattern: Optional[str] = None
    participants: List[int]


class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    location: Optional[str] = None
    meeting_type: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurring_pattern: Optional[str] = None


class MeetingOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    creator_id: int
    team_id: Optional[int]
    org_unit_id: Optional[int]
    start_at: datetime
    end_at: datetime
    location: Optional[str]
    meeting_type: str
    is_recurring: bool
    recurring_pattern: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


class UserPerformanceOut(BaseModel):
    id: int
    user_id: int
    team_id: Optional[int]
    org_unit_id: Optional[int]
    period_start: datetime
    period_end: datetime
    total_tasks: int
    completed_tasks: int
    average_score: float
    total_score: float
    evaluations_count: int
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


class TaskStatusUpdate(BaseModel):
    status: TaskStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    actual_hours: Optional[float] = None
