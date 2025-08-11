from fastapi import FastAPI
from src.api.endpoints import router as api_router
from src.db.database import engine
from src.db.models import CalendarEvent, UserAvailability, TimeSlot
from sqladmin import Admin, ModelView

app = FastAPI(title="Calendar Service")
app.include_router(api_router, prefix="/api")
admin = Admin(app, engine)


class CalendarEventAdmin(ModelView, model=CalendarEvent):
    column_list = [
        CalendarEvent.id,
        CalendarEvent.user_id,
        CalendarEvent.title,
        CalendarEvent.description,
        CalendarEvent.event_type,
        CalendarEvent.status,
        CalendarEvent.start_at,
        CalendarEvent.end_at,
        CalendarEvent.task_id,
        CalendarEvent.meeting_id,
        CalendarEvent.team_id,
        CalendarEvent.org_unit_id,
        CalendarEvent.location,
        CalendarEvent.is_all_day,
        CalendarEvent.is_recurring,
        CalendarEvent.recurring_pattern,
        CalendarEvent.recurring_end_date,
        CalendarEvent.participants,
        CalendarEvent.created_at,
        CalendarEvent.updated_at,
    ]


class UserAvailabilityAdmin(ModelView, model=UserAvailability):
    column_list = [
        UserAvailability.id,
        UserAvailability.user_id,
        UserAvailability.work_start_time,
        UserAvailability.work_end_time,
        UserAvailability.work_days,
        UserAvailability.lunch_start,
        UserAvailability.lunch_end,
        UserAvailability.timezone,
        UserAvailability.is_available,
        UserAvailability.auto_decline_conflicts,
        UserAvailability.created_at,
        UserAvailability.updated_at
    ]


class TimeSlotAdmin(ModelView, model=TimeSlot):
    column_list = [
        TimeSlot.id,
        TimeSlot.user_id,
        TimeSlot.date,
        TimeSlot.start_time,
        TimeSlot.end_time,
        TimeSlot.is_available,
        TimeSlot.event_id
    ]


admin.add_view(CalendarEventAdmin)
admin.add_view(UserAvailabilityAdmin)
admin.add_view(TimeSlotAdmin)
