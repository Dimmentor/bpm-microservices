from functools import partial
from sqlalchemy import update
from src.services.rabbitmq import consume_events
from src.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import User
import logging

logger = logging.getLogger(__name__)


async def handle_team_events(data: dict, db: AsyncSession):
    event_type = data.get("event_type")
    if event_type == "team.user_assigned":
        user_id = data["user_id"]
        team_id = data["team_id"]
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(team_id=team_id)
        )
        await db.commit()
        logger.info(f"User {user_id} assigned to team {team_id}")


async def setup_user_consumers():
    await consume_events(
        queue_name="user_service_queue",
        exchange_name="team_events",
        routing_keys=["team.*"],
        callback=partial(handle_team_events, db=await get_db().__anext__())
    )
