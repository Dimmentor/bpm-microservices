import httpx
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from src.db.models import CalendarEvent, UserAvailability, EventStatus
import json
from src.services.rabbitmq import publish_event


async def validate_participants_availability(
        participants: List[int],
        start_at: datetime,
        end_at: datetime,
        db: AsyncSession,
        exclude_event_id: Optional[int] = None
) -> Dict:
    conflicts = []
    unavailable_users = []

    for user_id in participants:

        availability_res = await db.execute(
            select(UserAvailability).where(UserAvailability.user_id == user_id)
        )
        availability = availability_res.scalar_one_or_none()

        if not availability:
            availability = UserAvailability(
                user_id=user_id,
                work_start_time="09:00",
                work_end_time="18:00",
                is_available=True
            )
            db.add(availability)
            await db.commit()
            await db.refresh(availability)

        if not availability.is_available:
            unavailable_users.append({
                "user_id": user_id,
                "reason": "Пользователь отмечен как недоступный"
            })
            continue

        start_time = start_at.strftime("%H:%M")
        end_time = end_at.strftime("%H:%M")

        if (start_time < availability.work_start_time or
                end_time > availability.work_end_time):
            unavailable_users.append({
                "user_id": user_id,
                "reason": f"Вне рабочего времени ({availability.work_start_time}-{availability.work_end_time})"
            })
            continue

        conflicts_query = select(CalendarEvent).where(
            and_(
                CalendarEvent.user_id == user_id,
                CalendarEvent.status != EventStatus.CANCELLED,
                or_(
                    and_(CalendarEvent.start_at < end_at, CalendarEvent.end_at > start_at)
                )
            )
        )

        if exclude_event_id:
            conflicts_query = conflicts_query.where(CalendarEvent.id != exclude_event_id)

        user_conflicts_res = await db.execute(conflicts_query)
        user_conflicts = user_conflicts_res.scalars().all()

        if user_conflicts:
            conflicts.append({
                "user_id": user_id,
                "conflicts": [
                    {
                        "event_id": conflict.id,
                        "title": conflict.title,
                        "start_at": conflict.start_at.isoformat(),
                        "end_at": conflict.end_at.isoformat()
                    }
                    for conflict in user_conflicts
                ]
            })

    is_valid = len(conflicts) == 0 and len(unavailable_users) == 0

    return {
        "is_valid": is_valid,
        "conflicts": conflicts,
        "unavailable_users": unavailable_users,
        "suggested_times": []
    }


async def suggest_alternative_times(
        participants: List[int],
        original_start: datetime,
        original_end: datetime,
        db: AsyncSession,
        max_suggestions: int = 3
) -> List[Dict]:
    duration = original_end - original_start
    suggestions = []

    time_offsets = [1, -1, 2]

    for offset in time_offsets:
        if len(suggestions) >= max_suggestions:
            break

        new_hour = original_start.hour + offset
        if new_hour < 0 or new_hour > 23:
            continue

        new_start = original_start.replace(hour=new_hour)
        new_end = new_start + duration

        validation = await validate_participants_availability(
            participants, new_start, new_end, db
        )

        if validation["is_valid"]:
            suggestions.append({
                "start_at": new_start.isoformat(),
                "end_at": new_end.isoformat(),
                "reason": f"Смещение на {offset} час(а)"
            })

    return suggestions


async def create_meeting_with_validation(
        title: str,
        description: Optional[str],
        user_id: int,
        participants: List[int],
        start_at: datetime,
        end_at: datetime,
        location: Optional[str],
        team_id: Optional[int],
        org_unit_id: Optional[int],
        db: AsyncSession
) -> Dict:
    if start_at >= end_at:
        raise ValueError("Время начала должно быть раньше времени окончания")

    validation = await validate_participants_availability(
        participants, start_at, end_at, db
    )

    if not validation["is_valid"]:
        return {
            "success": False,
            "validation": validation,
            "message": "Не все участники доступны в указанное время"
        }

    event = CalendarEvent(
        user_id=user_id,
        title=title,
        description=description,
        event_type="MEETING",
        start_at=start_at,
        end_at=end_at,
        location=location,
        team_id=team_id,
        org_unit_id=org_unit_id,
        participants=json.dumps(participants) if participants else None
    )

    db.add(event)
    await db.commit()
    await db.refresh(event)

    await publish_event("meeting.scheduled", {
        "event_id": event.id,
        "organizer_id": user_id,
        "participants": participants,
        "start_at": start_at.isoformat(),
        "end_at": end_at.isoformat(),
        "team_id": team_id,
        "org_unit_id": org_unit_id
    })

    return {
        "success": True,
        "event": event,
        "validation": validation
    }


async def check_user_permissions(
        organizer_id: int,
        participants: List[int],
        team_id: Optional[int] = None,
        org_unit_id: Optional[int] = None
) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://team-service:8002/api/org_members/{organizer_id}/hierarchy"
            )
            if response.status_code == 200:
                hierarchy = response.json()
                return True
    except Exception:
        pass

    return True


async def notify_participants(
        event_id: int,
        participants: List[int],
        event_details: Dict
):
    for participant_id in participants:
        await publish_event("meeting.participant_invited", {
            "event_id": event_id,
            "participant_id": participant_id,
            "organizer_id": event_details.get("organizer_id"),
            "title": event_details.get("title"),
            "start_at": event_details.get("start_at"),
            "end_at": event_details.get("end_at"),
            "location": event_details.get("location")
        })
