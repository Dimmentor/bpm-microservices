from functools import partial
from src.services.rabbitmq import consume_events
from src.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import CalendarEvent
import logging

logger = logging.getLogger(__name__)


async def handle_task_events(data: dict, db: AsyncSession):
    event_type = data.get("event_type")
    if event_type == "task.created":
        event = CalendarEvent(
            user_id=data["assignee_id"],
            title=f"Task: {data.get('title', '')}",
            event_type="task",
            start_at=data["due_at"],
            end_at=data["due_at"],
            task_id=data["task_id"],
            team_id=data.get("team_id")
        )
        db.add(event)
        await db.commit()
        logger.info(f"Created calendar event for task {data['task_id']}")


async def setup_calendar_consumers():
    await consume_events(
        queue_name="calendar_service_queue",
        exchange_name="task_events",
        routing_keys=["task.*"],
        callback=partial(handle_task_events, db=await get_db().__anext__())
    )
