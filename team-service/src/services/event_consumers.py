from functools import partial
from sqlalchemy import update
from src.services.rabbitmq import consume_events
from src.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import OrgMember
import logging

logger = logging.getLogger(__name__)


async def handle_user_events(data: dict, db: AsyncSession):
    event_type = data.get("event_type")
    if event_type == "user.status_changed":
        user_id = data["user_id"]
        new_status = data["new_status"]

        await db.execute(
            update(OrgMember)
            .where(OrgMember.user_id == user_id)
            .values(is_active=new_status == "active")
        )
        await db.commit()
        logger.info(f"Updated user {user_id} status in all org units")


async def setup_team_consumers():
    await consume_events(
        queue_name="team_service_queue",
        exchange_name="user_events",
        routing_keys=["user.*"],
        callback=partial(handle_user_events, db=await get_db().__anext__())
    )
