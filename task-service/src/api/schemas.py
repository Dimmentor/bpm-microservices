from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime


class TaskCreate(BaseModel):
    title: str
    description: Optional[str]
    creator_id: int
    assignee_id: Optional[int]
    team_id: Optional[int]
    due_at: Optional[datetime]


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    creator_id: int
    assignee_id: Optional[int]
    status: str
    due_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


class CommentCreate(BaseModel):
    task_id: int
    author_id: int
    text: str


class EvaluationCreate(BaseModel):
    task_id: int
    evaluator_id: int
    criteria: Dict[str, int]


class MeetingCreate(BaseModel):
    title: str
    creator_id: int
    team_id: Optional[int]
    start_at: datetime
    end_at: datetime
    participants: List[int]
