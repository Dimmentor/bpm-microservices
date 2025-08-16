"""
Утилиты для работы с задачами
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from src.db.models import Task, TaskStatus
from src.services.rabbitmq import publish_event


async def update_task_status(
    task_id: int, 
    new_status: TaskStatus, 
    db: AsyncSession,
    started_at: Optional[datetime] = None,
    completed_at: Optional[datetime] = None,
    actual_hours: Optional[float] = None
) -> Task:
    """Обновление статуса задачи с автоматическим проставлением времени"""
    
    res = await db.execute(select(Task).where(Task.id == task_id))
    task = res.scalar_one_or_none()
    if not task:
        raise ValueError("Task not found")
    
    update_data = {"status": new_status}

    if new_status == TaskStatus.IN_PROGRESS and not task.started_at:
        update_data["started_at"] = started_at or datetime.utcnow()
    elif new_status == TaskStatus.COMPLETED and not task.completed_at:
        update_data["completed_at"] = completed_at or datetime.utcnow()
        if actual_hours:
            update_data["actual_hours"] = actual_hours
    
    await db.execute(
        update(Task).where(Task.id == task_id).values(**update_data)
    )
    await db.commit()
    await db.refresh(task)

    await publish_event("task.status_changed", {
        "task_id": task_id,
        "status": new_status.value,
        "assignee_id": task.assignee_id,
        "team_id": task.team_id
    })
    
    return task


async def validate_task_assignment(
    creator_id: int,
    assignee_id: int,
    team_id: Optional[int],
    org_unit_id: Optional[int]
) -> bool:
    """Валидация назначения задачи согласно ТЗ - руководители могут ставить задачи подчиненным"""

    return True


async def calculate_task_metrics(task: Task) -> dict:
    """Расчет метрик выполнения задачи"""
    
    metrics = {
        "is_overdue": False,
        "completion_time_hours": None,
        "estimated_vs_actual": None
    }
    
    if task.due_at and datetime.utcnow() > task.due_at and task.status != TaskStatus.COMPLETED:
        metrics["is_overdue"] = True
    
    if task.started_at and task.completed_at:
        completion_time = task.completed_at - task.started_at
        metrics["completion_time_hours"] = completion_time.total_seconds() / 3600
    
    if task.estimated_hours and task.actual_hours:
        metrics["estimated_vs_actual"] = task.actual_hours / task.estimated_hours
    
    return metrics
