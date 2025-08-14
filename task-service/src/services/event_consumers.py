from functools import partial
from sqlalchemy import update
from src.services.rabbitmq import consume_events
from src.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import Task
import logging

logger = logging.getLogger(__name__)


async def handle_team_events(data: dict, db: AsyncSession):
    event_type = data.get("event_type")
    if event_type == "team.deactivated":
        team_id = data["team_id"]

        await db.execute(
            update(Task)
            .where(Task.team_id == team_id)
            .values(status="cancelled")
        )
        await db.commit()
        logger.info(f"Cancelled all tasks for team {team_id}")


async def setup_task_consumers():
    await consume_events(
        queue_name="task_service_queue",
        exchange_name="team_events",
        routing_keys=["team.*"],
        callback=partial(handle_team_events, db=await get_db().__anext__())
    )
