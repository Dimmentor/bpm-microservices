from fastapi import FastAPI
from src.api.endpoints import router as api_router
from src.db.database import engine
from sqladmin import Admin, ModelView
from src.db.models import Task, TaskComment, TaskEvaluation, Meeting, MeetingParticipant, UserPerformance

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
        Task.started_at,
        Task.completed_at,
        Task.estimated_hours,
        Task.actual_hours,
        Task.created_at,
        Task.updated_at
    ]


class TaskCommentAdmin(ModelView, model=TaskComment):
    column_list = [
        TaskComment.id,
        TaskComment.task_id,
        TaskComment.author_id,
        TaskComment.text,
        TaskComment.is_internal,
        TaskComment.created_at
    ]


class TaskEvaluationAdmin(ModelView, model=TaskEvaluation):
    column_list = [
        TaskEvaluation.id,
        TaskEvaluation.task_id,
        TaskEvaluation.evaluator_id,
        TaskEvaluation.criteria,
        TaskEvaluation.score,
        TaskEvaluation.feedback,
        TaskEvaluation.created_at
    ]


class MeetingAdmin(ModelView, model=Meeting):
    column_list = [
        Meeting.id,
        Meeting.title,
        Meeting.description,
        Meeting.creator_id,
        Meeting.team_id,
        Meeting.org_unit_id,
        Meeting.start_at,
        Meeting.end_at,
        Meeting.location,
        Meeting.meeting_type,
        Meeting.is_recurring,
        Meeting.recurring_pattern,
        Meeting.created_at,
        Meeting.updated_at
    ]


class MeetingParticipantAdmin(ModelView, model=MeetingParticipant):
    column_list = [
        MeetingParticipant.id,
        MeetingParticipant.meeting_id,
        MeetingParticipant.user_id,
        MeetingParticipant.status,
        MeetingParticipant.role,
        MeetingParticipant.created_at
    ]


class UserPerformanceAdmin(ModelView, model=UserPerformance):
    column_list = [
        UserPerformance.id,
        UserPerformance.user_id,
        UserPerformance.team_id,
        UserPerformance.org_unit_id,
        UserPerformance.period_start,
        UserPerformance.period_end,
        UserPerformance.total_tasks,
        UserPerformance.completed_tasks,
        UserPerformance.average_score,
        UserPerformance.total_score,
        UserPerformance.evaluations_count,
        UserPerformance.created_at,
        UserPerformance.updated_at
    ]


admin.add_view(TaskAdmin)
admin.add_view(TaskCommentAdmin)
admin.add_view(TaskEvaluationAdmin)
admin.add_view(MeetingAdmin)
admin.add_view(MeetingParticipantAdmin)
admin.add_view(UserPerformanceAdmin)
