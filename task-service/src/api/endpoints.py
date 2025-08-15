from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from src.api.utils import update_user_performance, calculate_average_metrics
from src.db.database import get_db
from src.db.models import Task, TaskComment, TaskEvaluation, UserPerformance
from src.api.schemas import TaskCreate, TaskUpdate, TaskOut, CommentCreate, EvaluationCreate, UserPerformanceOut, \
    EvaluationOut
from src.services.rabbitmq import publish_event
from typing import Optional
from datetime import datetime, date
import calendar

router = APIRouter()


@router.post("/tasks", response_model=TaskOut)
async def create_task(payload: TaskCreate, db: AsyncSession = Depends(get_db)):
    task = Task(
        title=payload.title,
        description=payload.description,
        creator_id=payload.creator_id,
        assignee_id=payload.assignee_id,
        team_id=payload.team_id,
        org_unit_id=payload.org_unit_id,
        priority=payload.priority,
        due_at=payload.due_at,
        estimated_hours=payload.estimated_hours
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    await publish_event("task.created", {
        "task_id": task.id,
        "assignee_id": task.assignee_id,
        "team_id": task.team_id,
        "org_unit_id": task.org_unit_id,
        "creator_id": task.creator_id
    })

    return task


@router.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Task).where(Task.id == task_id))
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/tasks/{task_id}", response_model=TaskOut)
async def update_task(task_id: int, payload: TaskUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Task).where(Task.id == task_id))
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = payload.dict(exclude_unset=True)

    if 'status' in update_data:
        if update_data['status'].value == 'in_progress' and not task.started_at:
            update_data['started_at'] = datetime.utcnow()
        elif update_data['status'].value == 'completed' and not task.completed_at:
            update_data['completed_at'] = datetime.utcnow()

    if update_data:
        await db.execute(
            update(Task).where(Task.id == task_id).values(**update_data)
        )
        await db.commit()
        await db.refresh(task)

        await publish_event("task.updated", {
            "task_id": task_id,
            "status": task.status.value,
            "assignee_id": task.assignee_id,
            "team_id": task.team_id
        })

    return task


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Task).where(Task.id == task_id))
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await db.execute(delete(Task).where(Task.id == task_id))
    await db.commit()

    await publish_event("task.deleted", {
        "task_id": task_id,
        "assignee_id": task.assignee_id,
        "team_id": task.team_id
    })

    return {"message": "Task deleted successfully"}


@router.post("/tasks/{task_id}/comments")
async def add_comment(task_id: int, payload: CommentCreate, db: AsyncSession = Depends(get_db)):
    comment = TaskComment(
        task_id=payload.task_id,
        author_id=payload.author_id,
        text=payload.text,
        is_internal=payload.is_internal
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    await publish_event("task.comment_added", {
        "task_id": task_id,
        "comment_id": comment.id,
        "author_id": payload.author_id
    })

    return {"id": comment.id}


@router.post("/tasks/{task_id}/evaluate", response_model=EvaluationOut)
async def evaluate_task(
        task_id: int,
        payload: EvaluationCreate,
        db: AsyncSession = Depends(get_db)
):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    scores = list(payload.criteria.values())
    avg_score = sum(scores) / len(scores) if scores else 0

    eval_obj = TaskEvaluation(
        task_id=payload.task_id,
        evaluator_id=payload.evaluator_id,
        criteria=payload.criteria,
        score=avg_score,
        feedback=payload.feedback
    )
    db.add(eval_obj)
    await db.commit()
    await db.refresh(eval_obj)

    await update_user_performance(task.assignee_id, task.team_id, task.org_unit_id, db)

    await publish_event("task.evaluated", {
        "task_id": payload.task_id,
        "score": avg_score,
        "evaluator_id": payload.evaluator_id,
        "assignee_id": task.assignee_id
    })

    return {"id": eval_obj.id, "score": avg_score}


# ==================== PERFORMANCE ENDPOINTS ====================

@router.get("/performance/user/{user_id}", response_model=UserPerformanceOut)
async def get_user_performance(
        user_id: int,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        db: AsyncSession = Depends(get_db)
):
    if not period_start:
        today = date.today()
        quarter_start_month = 3 * ((today.month - 1) // 3)
        period_start = date(today.year, quarter_start_month + 1, 1)
        period_end = date(today.year, quarter_start_month + 3,
                          calendar.monthrange(today.year, quarter_start_month + 3)[1])

    perf_res = await db.execute(
        select(UserPerformance).where(
            and_(
                UserPerformance.user_id == user_id,
                UserPerformance.period_start == period_start,
                UserPerformance.period_end == period_end
            )
        )
    )
    performance = perf_res.scalar_one_or_none()

    if not performance:
        performance = await update_user_performance(user_id, None, None, db, period_start, period_end)

    return performance


@router.get("/performance/team/{team_id}")
async def get_team_performance(
        team_id: int,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        db: AsyncSession = Depends(get_db)
):
    if not period_start:
        today = date.today()
        quarter_start_month = 3 * ((today.month - 1) // 3)
        period_start = date(today.year, quarter_start_month + 1, 1)
        period_end = date(today.year, quarter_start_month + 3,
                          calendar.monthrange(today.year, quarter_start_month + 3)[1])

    team_perf_res = await db.execute(
        select(UserPerformance).where(
            and_(
                UserPerformance.team_id == team_id,
                UserPerformance.period_start == period_start,
                UserPerformance.period_end == period_end
            )
        )
    )
    team_performances = team_perf_res.scalars().all()

    if not team_performances:
        return {
            "team_id": team_id,
            "period_start": period_start,
            "period_end": period_end,
            "total_users": 0,
            "average_score": 0.0,
            "total_tasks": 0,
            "completed_tasks": 0
        }

    total_users = len(team_performances)
    total_score = sum(p.average_score for p in team_performances)
    total_tasks = sum(p.total_tasks for p in team_performances)
    completed_tasks = sum(p.completed_tasks for p in team_performances)

    return {
        "team_id": team_id,
        "period_start": period_start,
        "period_end": period_end,
        "total_users": total_users,
        "average_score": total_score / total_users if total_users > 0 else 0.0,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0,
        "user_performances": [
            {
                "user_id": p.user_id,
                "average_score": p.average_score,
                "total_tasks": p.total_tasks,
                "completed_tasks": p.completed_tasks
            } for p in team_performances
        ]
    }


@router.get("/performance/org_unit/{org_unit_id}")
async def get_org_unit_performance(
        org_unit_id: int,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        db: AsyncSession = Depends(get_db)
):
    if not period_start:
        today = date.today()
        quarter_start_month = 3 * ((today.month - 1) // 3)
        period_start = date(today.year, quarter_start_month + 1, 1)
        period_end = date(today.year, quarter_start_month + 3,
                          calendar.monthrange(today.year, quarter_start_month + 3)[1])

    unit_perf_res = await db.execute(
        select(UserPerformance).where(
            and_(
                UserPerformance.org_unit_id == org_unit_id,
                UserPerformance.period_start == period_start,
                UserPerformance.period_end == period_end
            )
        )
    )
    unit_performances = unit_perf_res.scalars().all()

    if not unit_performances:
        return {
            "org_unit_id": org_unit_id,
            "period_start": period_start,
            "period_end": period_end,
            "total_users": 0,
            "average_score": 0.0,
            "total_tasks": 0,
            "completed_tasks": 0
        }

    total_users = len(unit_performances)
    total_score = sum(p.average_score for p in unit_performances)
    total_tasks = sum(p.total_tasks for p in unit_performances)
    completed_tasks = sum(p.completed_tasks for p in unit_performances)

    return {
        "org_unit_id": org_unit_id,
        "period_start": period_start,
        "period_end": period_end,
        "total_users": total_users,
        "average_score": total_score / total_users if total_users > 0 else 0.0,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0,
        "user_performances": [
            {
                "user_id": p.user_id,
                "average_score": p.average_score,
                "total_tasks": p.total_tasks,
                "completed_tasks": p.completed_tasks
            } for p in unit_performances
        ]
    }


@router.get("/performance/{user_id}/matrix")
async def get_performance_matrix(
        user_id: int,
        period: str = "quarter",
        db: AsyncSession = Depends(get_db)
):
    today = date.today()
    if period == "quarter":
        quarter = (today.month - 1) // 3 + 1
        period_start = date(today.year, 3 * quarter - 2, 1)
        period_end = date(today.year, 3 * quarter,
                          calendar.monthrange(today.year, 3 * quarter)[1])
    elif period == "year":
        period_start = date(today.year, 1, 1)
        period_end = date(today.year, 12, 31)
    else:
        period_start = date(today.year, today.month, 1)
        period_end = date(today.year, today.month,
                          calendar.monthrange(today.year, today.month)[1])

    perf = await db.execute(
        select(UserPerformance).where(
            and_(
                UserPerformance.user_id == user_id,
                UserPerformance.period_start == period_start,
                UserPerformance.period_end == period_end
            )
        )
    )
    user_perf = perf.scalar_one_or_none()

    if not user_perf:
        raise HTTPException(status_code=404, detail="Performance data not found")

    team_avg = await calculate_average_metrics(
        user_perf.metrics.get("team_id"),
        period_start,
        period_end,
        db
    )

    unit_avg = await calculate_average_metrics(
        user_perf.metrics.get("org_unit_id"),
        period_start,
        period_end,
        db,
        by_unit=True
    )

    return {
        "user_metrics": user_perf.metrics,
        "comparison": {
            "team_avg": team_avg,
            "org_unit_avg": unit_avg
        },
        "period": {
            "start": period_start,
            "end": period_end,
            "type": period
        }
    }
