from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.database import get_db
from src.db.models import Task, TaskComment, TaskEvaluation
from src.api.schemas import TaskCreate, TaskOut, CommentCreate, EvaluationCreate
from src.services.rabbitmq import publish_event
from statistics import mean

router = APIRouter()


@router.post("/tasks", response_model=TaskOut)
async def create_task(payload: TaskCreate, db: AsyncSession = Depends(get_db)):
    task = Task(
        title=payload.title,
        description=payload.description,
        creator_id=payload.creator_id,
        assignee_id=payload.assignee_id,
        team_id=payload.team_id,
        due_at=payload.due_at
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    # publish event
    await publish_event("task.created", {"task_id": task.id, "assignee_id": task.assignee_id})
    return task


@router.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Task).where(Task.id == task_id))
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks/{task_id}/comments")
async def add_comment(task_id: int, payload: CommentCreate, db: AsyncSession = Depends(get_db)):
    comment = TaskComment(task_id=payload.task_id, author_id=payload.author_id, text=payload.text)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return {"id": comment.id}


@router.post("/tasks/{task_id}/evaluate")
async def evaluate(task_id: int, payload: EvaluationCreate, db: AsyncSession = Depends(get_db)):
    # compute simple average score
    scores = list(payload.criteria.values())
    avg = sum(scores) / len(scores) if scores else 0
    eval_obj = TaskEvaluation(task_id=payload.task_id, evaluator_id=payload.evaluator_id, criteria=payload.criteria,
                              score=avg)
    db.add(eval_obj)
    await db.commit()
    await db.refresh(eval_obj)
    await publish_event("task.evaluated",
                        {"task_id": payload.task_id, "score": avg, "evaluator_id": payload.evaluator_id})
    return {"id": eval_obj.id, "score": avg}
