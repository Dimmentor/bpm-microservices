import asyncio
from sqlalchemy import update, select
from src.services.rabbitmq import consume_events
from src.db.database import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import Task, TaskStatus
import logging
import json

logger = logging.getLogger(__name__)


async def handle_user_events(data: dict):
    async with AsyncSessionLocal() as db:
        try:
            event_type = data.get("event_type", "")

            if event_type == "user.status_changed":
                user_id = data.get("user_id")
                new_status = data.get("new_status")

                if new_status in ["suspended", "inactive"]:
                    await db.execute(
                        update(Task)
                        .where(Task.assignee_id == user_id)
                        .where(Task.status.in_([TaskStatus.CREATED, TaskStatus.IN_PROGRESS]))
                        .values(status=TaskStatus.CANCELLED)
                    )
                    await db.commit()
                    logger.info(f"Cancelled tasks for user {user_id} due to status change to {new_status}")

            elif event_type == "user.team_assigned":
                user_id = data.get("user_id")
                team_id = data.get("team_id")

                await db.execute(
                    update(Task)
                    .where(Task.assignee_id == user_id)
                    .where(Task.team_id.is_(None))
                    .values(team_id=team_id)
                )
                await db.commit()
                logger.info(f"Updated team_id for user {user_id} tasks to {team_id}")

        except Exception as e:
            logger.error(f"Error handling user event: {e}")
            await db.rollback()


async def handle_team_events(data: dict):
    """Обработка событий команд"""
    async with AsyncSessionLocal() as db:
        try:
            event_type = data.get("event_type", "")

            if event_type == "team.deactivated":
                team_id = data.get("team_id")

                await db.execute(
                    update(Task)
                    .where(Task.team_id == team_id)
                    .where(Task.status.in_([TaskStatus.CREATED, TaskStatus.IN_PROGRESS]))
                    .values(status=TaskStatus.CANCELLED)
                )
                await db.commit()
                logger.info(f"Cancelled all active tasks for team {team_id}")

            elif event_type == "org_unit.deactivated":
                org_unit_id = data.get("unit_id")

                await db.execute(
                    update(Task)
                    .where(Task.org_unit_id == org_unit_id)
                    .where(Task.status.in_([TaskStatus.CREATED, TaskStatus.IN_PROGRESS]))
                    .values(status=TaskStatus.CANCELLED)
                )
                await db.commit()
                logger.info(f"Cancelled all active tasks for org unit {org_unit_id}")

        except Exception as e:
            logger.error(f"Error handling team event: {e}")
            await db.rollback()


async def handle_calendar_events(data: dict):
    async with AsyncSessionLocal() as db:
        try:
            event_type = data.get("event_type", "")

            if event_type == "calendar_event.task_created":
                task_id = data.get("task_id")
                event_id = data.get("event_id")

                logger.info(f"Calendar event {event_id} created for task {task_id}")

        except Exception as e:
            logger.error(f"Error handling calendar event: {e}")


async def setup_task_consumers():
    asyncio.create_task(
        consume_events(
            queue_name="task_user_events",
            exchange_name="user_events",
            routing_keys=["user.status_changed", "user.team_assigned", "user.deleted"],
            callback=handle_user_events
        )
    )

    asyncio.create_task(
        consume_events(
            queue_name="task_team_events",
            exchange_name="team_events",
            routing_keys=["team.deactivated", "org_unit.deactivated"],
            callback=handle_team_events
        )
    )

    asyncio.create_task(
        consume_events(
            queue_name="task_calendar_events",
            exchange_name="calendar_events",
            routing_keys=["calendar_event.task_created"],
            callback=handle_calendar_events
        )
    )

    logger.info("Task service event consumers started")
