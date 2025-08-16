import calendar
from datetime import datetime, date
from typing import Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import UserPerformance, Task, TaskStatus, TaskEvaluation


async def update_user_performance(user_id: int, team_id: Optional[int], org_unit_id: Optional[int],
                                  db: AsyncSession, period_start: Optional[date] = None,
                                  period_end: Optional[date] = None) -> UserPerformance:
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
        performance = UserPerformance(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end
        )
        db.add(performance)

    total_tasks_res = await db.execute(
        select(func.count(Task.id)).where(
            and_(
                Task.assignee_id == user_id,
                Task.created_at >= datetime.combine(period_start, datetime.min.time()),
                Task.created_at <= datetime.combine(period_end, datetime.max.time())
            )
        )
    )
    total_tasks = total_tasks_res.scalar() or 0

    completed_tasks_res = await db.execute(
        select(func.count(Task.id)).where(
            and_(
                Task.assignee_id == user_id,
                Task.status == TaskStatus.COMPLETED,
                Task.completed_at >= datetime.combine(period_start, datetime.min.time()),
                Task.completed_at <= datetime.combine(period_end, datetime.max.time())
            )
        )
    )
    completed_tasks = completed_tasks_res.scalar() or 0

    avg_score_res = await db.execute(
        select(func.avg(TaskEvaluation.score)).where(
            and_(
                TaskEvaluation.task_id.in_(
                    select(Task.id).where(
                        and_(
                            Task.assignee_id == user_id,
                            TaskEvaluation.created_at >= datetime.combine(period_start, datetime.min.time()),
                            TaskEvaluation.created_at <= datetime.combine(period_end, datetime.max.time())
                        )
                    )
                )
            )
        )
    )
    average_score = avg_score_res.scalar() or 0.0

    eval_count_res = await db.execute(
        select(func.count(TaskEvaluation.id)).where(
            and_(
                TaskEvaluation.task_id.in_(
                    select(Task.id).where(Task.assignee_id == user_id)
                ),
                TaskEvaluation.created_at >= datetime.combine(period_start, datetime.min.time()),
                TaskEvaluation.created_at <= datetime.combine(period_end, datetime.max.time())
            )
        )
    )
    evaluations_count = eval_count_res.scalar() or 0

    performance.total_tasks = total_tasks
    performance.completed_tasks = completed_tasks
    performance.average_score = average_score
    performance.evaluations_count = evaluations_count
    performance.total_score = average_score * evaluations_count

    await db.commit()
    await db.refresh(performance)

    return performance


async def calculate_average_metrics(
        team_or_unit_id: Optional[int],
        period_start: date,
        period_end: date,
        db: AsyncSession,
        by_unit: bool = False
):
    if not team_or_unit_id:
        return None

    query = select(UserPerformance).where(
        and_(
            UserPerformance.period_start == period_start,
            UserPerformance.period_end == period_end,
            UserPerformance.metrics["team_id"].astext == str(team_or_unit_id)
            if not by_unit else
            UserPerformance.metrics["org_unit_id"].astext == str(team_or_unit_id)
        )
    )

    result = await db.execute(query)
    performances = result.scalars().all()

    if not performances:
        return None

    avg_metrics = {
        "total_tasks": 0,
        "completed_tasks": 0,
        "average_scores": {
            "timeliness": 0.0,
            "quality": 0.0,
            "communication": 0.0
        },
        "total_score": 0.0,
        "user_count": len(performances)
    }

    for perf in performances:
        metrics = perf.metrics
        avg_metrics["total_tasks"] += metrics.get("total_tasks", 0)
        avg_metrics["completed_tasks"] += metrics.get("completed_tasks", 0)
        avg_metrics["total_score"] += metrics.get("total_score", 0.0)

        for score_type in ["timeliness", "quality", "communication"]:
            avg_metrics["average_scores"][score_type] += \
                metrics.get("average_scores", {}).get(score_type, 0.0)

    avg_metrics["total_tasks"] = round(avg_metrics["total_tasks"] / len(performances))
    avg_metrics["completed_tasks"] = round(avg_metrics["completed_tasks"] / len(performances))
    avg_metrics["total_score"] = round(avg_metrics["total_score"] / len(performances), 2)

    for score_type in avg_metrics["average_scores"]:
        avg_metrics["average_scores"][score_type] = round(
            avg_metrics["average_scores"][score_type] / len(performances), 2
        )

    return avg_metrics
