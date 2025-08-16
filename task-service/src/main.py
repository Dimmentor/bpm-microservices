import asyncio
from fastapi import FastAPI
from src.api.endpoints import router
from src.db.database import engine
from src.db.models import Task, TaskComment, TaskEvaluation, UserPerformance
from sqladmin import Admin, ModelView

from src.services.event_consumers import setup_task_consumers

app = FastAPI(title="Task Service", version="1.0.0")
app.include_router(router, prefix="/api")
admin = Admin(app, engine)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(setup_task_consumers())


class TaskAdmin(ModelView, model=Task):
    column_list = [
        Task.id, Task.title, Task.description, Task.creator_id, Task.assignee_id,
        Task.team_id, Task.org_unit_id, Task.status, Task.priority, Task.due_at,
        Task.started_at, Task.completed_at, Task.estimated_hours, Task.actual_hours,
        Task.created_at, Task.updated_at
    ]


class TaskCommentAdmin(ModelView, model=TaskComment):
    column_list = [
        TaskComment.id, TaskComment.task_id, TaskComment.author_id, TaskComment.text,
        TaskComment.is_internal, TaskComment.created_at
    ]


class TaskEvaluationAdmin(ModelView, model=TaskEvaluation):
    column_list = [
        TaskEvaluation.id, TaskEvaluation.task_id, TaskEvaluation.evaluator_id,
        TaskEvaluation.criteria, TaskEvaluation.score, TaskEvaluation.feedback,
        TaskEvaluation.created_at
    ]




class UserPerformanceAdmin(ModelView, model=UserPerformance):
    column_list = [
        UserPerformance.id, UserPerformance.user_id, UserPerformance.period_start,
        UserPerformance.period_end, UserPerformance.metrics, UserPerformance.comparison,
        UserPerformance.created_at, UserPerformance.updated_at
    ]


admin.add_view(TaskAdmin)
admin.add_view(TaskCommentAdmin)
admin.add_view(TaskEvaluationAdmin)
admin.add_view(UserPerformanceAdmin)
