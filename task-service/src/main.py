from fastapi import FastAPI
from src.api.endpoints import router as api_router
from src.db.database import engine
from sqladmin import Admin, ModelView
from src.db.models import Task, TaskComment, TaskEvaluation, Meeting, MeetingParticipant

app = FastAPI(title="task-service")
app.include_router(api_router, prefix="/api")
admin = Admin(app, engine)


class TaskAdmin(ModelView, model=Task):
    column_list = [
        Task.id,
        Task.title,
        Task.description,
        Task.creator_id,
        Task.assignee_id,
        Task.team_id,
        Task.org_unit_id,
        Task.status,
        Task.priority,
        Task.due_at,
        Task.created_at
    ]


class TaskCommentAdmin(ModelView, model=TaskComment):
    column_list = [
        TaskComment.id,
        TaskComment.task_id,
        TaskComment.author_id,
        TaskComment.text,
        TaskComment.created_at
    ]


class TaskEvaluationAdmin(ModelView, model=TaskEvaluation):
    column_list = [
        TaskEvaluation.id,
        TaskEvaluation.task_id,
        TaskEvaluation.evaluator_id,
        TaskEvaluation.criteria,
        TaskEvaluation.score,
        TaskEvaluation.created_at
    ]


class MeetingAdmin(ModelView, model=Meeting):
    column_list = [
        Meeting.id,
        Meeting.title,
        Meeting.creator_id,
        Meeting.team_id,
        Meeting.start_at,
        Meeting.end_at,
        Meeting.location,
        Meeting.created_at
    ]


class MeetingParticipantAdmin(ModelView, model=MeetingParticipant):
    column_list = [
        MeetingParticipant.id,
        MeetingParticipant.meeting_id,
        MeetingParticipant.user_id,
        MeetingParticipant.status
    ]


admin.add_view(TaskAdmin)
admin.add_view(TaskCommentAdmin)
admin.add_view(TaskEvaluationAdmin)
admin.add_view(MeetingAdmin)
admin.add_view(MeetingParticipantAdmin)
