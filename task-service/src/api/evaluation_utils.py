from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, join
from datetime import datetime
from src.db.models import TaskEvaluation, Task, UserPerformance
from src.services.rabbitmq import publish_event


EVALUATION_CRITERIA = {
    "соблюдение_сроков": "Соблюдение установленных сроков выполнения",
    "полнота_выполнения": "Полнота выполнения поставленной задачи", 
    "качество_работы": "Качество выполненной работы"
}


async def create_task_evaluation(
    task_id: int,
    evaluator_id: int,
    criteria_scores: Dict[str, int],
    feedback: Optional[str],
    db: AsyncSession
) -> TaskEvaluation:

    for criterion in criteria_scores.keys():
        if criterion not in EVALUATION_CRITERIA:
            raise ValueError(f"Неизвестный критерий оценки: {criterion}")
    for score in criteria_scores.values():
        if not isinstance(score, int) or score < 1 or score > 5:
            raise ValueError("Оценки должны быть целыми числами от 1 до 5")

    avg_score = sum(criteria_scores.values()) / len(criteria_scores)
    
    evaluation = TaskEvaluation(
        task_id=task_id,
        evaluator_id=evaluator_id,
        criteria=criteria_scores,
        score=avg_score,
        feedback=feedback
    )
    
    db.add(evaluation)
    await db.commit()
    await db.refresh(evaluation)

    await publish_event("task.evaluated", {
        "task_id": task_id,
        "evaluator_id": evaluator_id,
        "score": avg_score,
        "criteria": criteria_scores
    })
    
    return evaluation


async def get_user_evaluation_matrix(
    user_id: int,
    period_start: str,
    period_end: str,
    db: AsyncSession
) -> Dict:
    evaluations_res = await db.execute(
        select(TaskEvaluation).select_from(
            join(TaskEvaluation, Task, TaskEvaluation.task_id == Task.id)
        ).where(
            Task.assignee_id == user_id,
            TaskEvaluation.created_at >= datetime.fromisoformat(period_start),
            TaskEvaluation.created_at <= datetime.fromisoformat(period_end)
        )
    )
    evaluations = evaluations_res.scalars().all()
    
    if not evaluations:
        return {
            "user_id": user_id,
            "period": {"start": period_start, "end": period_end},
            "evaluations_count": 0,
            "average_scores": {},
            "overall_average": 0.0
        }

    criteria_totals = {}
    criteria_counts = {}
    
    for evaluation in evaluations:
        for criterion, score in evaluation.criteria.items():
            if criterion not in criteria_totals:
                criteria_totals[criterion] = 0
                criteria_counts[criterion] = 0
            criteria_totals[criterion] += score
            criteria_counts[criterion] += 1
    
    average_scores = {}
    for criterion in criteria_totals:
        average_scores[criterion] = round(
            criteria_totals[criterion] / criteria_counts[criterion], 2
        )
    
    overall_average = round(
        sum(average_scores.values()) / len(average_scores), 2
    ) if average_scores else 0.0
    
    return {
        "user_id": user_id,
        "period": {"start": period_start, "end": period_end},
        "evaluations_count": len(evaluations),
        "average_scores": average_scores,
        "overall_average": overall_average,
        "criteria_descriptions": EVALUATION_CRITERIA
    }


async def get_team_average_scores(
    team_id: int,
    period_start: str,
    period_end: str,
    db: AsyncSession
) -> Dict:

    evaluations_res = await db.execute(
        select(TaskEvaluation).select_from(
            join(TaskEvaluation, Task, TaskEvaluation.task_id == Task.id)
        ).where(
            Task.team_id == team_id,
            TaskEvaluation.created_at >= datetime.fromisoformat(period_start),
            TaskEvaluation.created_at <= datetime.fromisoformat(period_end)
        )
    )
    evaluations = evaluations_res.scalars().all()
    
    if not evaluations:
        return {"team_id": team_id, "average_scores": {}, "overall_average": 0.0}

    criteria_totals = {}
    criteria_counts = {}
    
    for evaluation in evaluations:
        for criterion, score in evaluation.criteria.items():
            if criterion not in criteria_totals:
                criteria_totals[criterion] = 0
                criteria_counts[criterion] = 0
            criteria_totals[criterion] += score
            criteria_counts[criterion] += 1
    
    average_scores = {}
    for criterion in criteria_totals:
        average_scores[criterion] = round(
            criteria_totals[criterion] / criteria_counts[criterion], 2
        )
    
    overall_average = round(
        sum(average_scores.values()) / len(average_scores), 2
    ) if average_scores else 0.0
    
    return {
        "team_id": team_id,
        "average_scores": average_scores,
        "overall_average": overall_average
    }


async def get_org_unit_average_scores(
    org_unit_id: int,
    period_start: str,
    period_end: str,
    db: AsyncSession
) -> Dict:

    evaluations_res = await db.execute(
        select(TaskEvaluation).select_from(
            join(TaskEvaluation, Task, TaskEvaluation.task_id == Task.id)
        ).where(
            Task.org_unit_id == org_unit_id,
            TaskEvaluation.created_at >= datetime.fromisoformat(period_start),
            TaskEvaluation.created_at <= datetime.fromisoformat(period_end)
        )
    )
    evaluations = evaluations_res.scalars().all()
    
    if not evaluations:
        return {"org_unit_id": org_unit_id, "average_scores": {}, "overall_average": 0.0}

    criteria_totals = {}
    criteria_counts = {}
    
    for evaluation in evaluations:
        for criterion, score in evaluation.criteria.items():
            if criterion not in criteria_totals:
                criteria_totals[criterion] = 0
                criteria_counts[criterion] = 0
            criteria_totals[criterion] += score
            criteria_counts[criterion] += 1
    
    average_scores = {}
    for criterion in criteria_totals:
        average_scores[criterion] = round(
            criteria_totals[criterion] / criteria_counts[criterion], 2
        )
    
    overall_average = round(
        sum(average_scores.values()) / len(average_scores), 2
    ) if average_scores else 0.0
    
    return {
        "org_unit_id": org_unit_id,
        "average_scores": average_scores,
        "overall_average": overall_average
    }
