import asyncio
from fastapi import FastAPI
from src.api.endpoints import router
from src.db.database import engine
from src.db.models import CalendarEvent, UserAvailability, TimeSlot
from sqladmin import Admin, ModelView
from src.services.event_consumers import setup_calendar_consumers

app = FastAPI(title="Calendar Service", version="1.0.0")
app.include_router(router, prefix="/api")
admin = Admin(app, engine)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(setup_calendar_consumers())


class CalendarEventAdmin(ModelView, model=CalendarEvent):
    column_list = [
        CalendarEvent.id, CalendarEvent.title, CalendarEvent.description,
        CalendarEvent.event_type, CalendarEvent.status,
        CalendarEvent.start_at, CalendarEvent.end_at, CalendarEvent.is_all_day,
        CalendarEvent.is_recurring, CalendarEvent.recurring_pattern, CalendarEvent.user_id,
        CalendarEvent.task_id, CalendarEvent.team_id, CalendarEvent.org_unit_id,
        CalendarEvent.location, CalendarEvent.meeting_type,
        CalendarEvent.participants, CalendarEvent.created_at, CalendarEvent.updated_at
    ]


class UserAvailabilityAdmin(ModelView, model=UserAvailability):
    column_list = [
        UserAvailability.id, UserAvailability.user_id, UserAvailability.work_start_time,
        UserAvailability.work_end_time, UserAvailability.work_days, UserAvailability.lunch_start,
        UserAvailability.lunch_end, UserAvailability.timezone, UserAvailability.is_available,
        UserAvailability.auto_decline_conflicts, UserAvailability.created_at, UserAvailability.updated_at
    ]


class TimeSlotAdmin(ModelView, model=TimeSlot):
    column_list = [
        TimeSlot.id, TimeSlot.user_id, TimeSlot.date, TimeSlot.start_time,
        TimeSlot.end_time, TimeSlot.is_available, TimeSlot.event_id
    ]


admin.add_view(CalendarEventAdmin)
admin.add_view(UserAvailabilityAdmin)
admin.add_view(TimeSlotAdmin)
