from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from src.db.database import get_db
from src.db.models import CalendarEvent, UserAvailability, TimeSlot, EventType, EventStatus
from src.api.schemas import (
    CalendarEventCreate, CalendarEventUpdate, CalendarEventOut,
    UserAvailabilityCreate, UserAvailabilityUpdate, UserAvailabilityOut,
    TimeSlotCreate, TimeSlotOut, AvailabilityCheck, AvailabilityResponse)
from src.api.calendar_utils import (
    validate_participants_availability, create_meeting_with_validation,
    check_user_permissions, notify_participants)
from src.services.rabbitmq import publish_event
from typing import List, Optional
from datetime import datetime, date, timedelta
import json

router = APIRouter()


@router.post("/events", response_model=CalendarEventOut)
async def create_event(payload: CalendarEventCreate, db: AsyncSession = Depends(get_db)):
    if payload.start_at >= payload.end_at:
        raise HTTPException(status_code=400, detail="start_at must be before end_at")

    # Если это встреча с участниками, используем валидацию
    if payload.event_type == EventType.MEETING and payload.participants:
        # Проверка прав на создание встречи
        has_permission = await check_user_permissions(
            organizer_id=payload.user_id,
            participants=payload.participants,
            team_id=payload.team_id,
            org_unit_id=payload.org_unit_id
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=403, 
                detail="Недостаточно прав для создания встречи с указанными участниками"
            )
        
        # Создание встречи с валидацией участников
        result = await create_meeting_with_validation(
            title=payload.title,
            description=payload.description,
            user_id=payload.user_id,
            participants=payload.participants,
            start_at=payload.start_at,
            end_at=payload.end_at,
            location=payload.location,
            team_id=payload.team_id,
            org_unit_id=payload.org_unit_id,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": result["message"],
                    "validation": result["validation"]
                }
            )
        
        # Уведомление участников
        await notify_participants(
            event_id=result["event"].id,
            participants=payload.participants,
            event_details={
                "organizer_id": payload.user_id,
                "title": payload.title,
                "start_at": payload.start_at.isoformat(),
                "end_at": payload.end_at.isoformat(),
                "location": payload.location
            }
        )
        
        return result["event"]
    
    # Обычное создание события (не встреча или без участников)
    conflicts = await db.execute(
        select(CalendarEvent).where(
            and_(
                CalendarEvent.user_id == payload.user_id,
                CalendarEvent.status != EventStatus.CANCELLED,
                or_(
                    and_(CalendarEvent.start_at < payload.end_at, CalendarEvent.end_at > payload.start_at)
                )
            )
        )
    )
    if conflicts.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Time conflict detected")

    event = CalendarEvent(
        user_id=payload.user_id,
        title=payload.title,
        description=payload.description,
        event_type=payload.event_type,
        start_at=payload.start_at,
        end_at=payload.end_at,
        task_id=payload.task_id,
        team_id=payload.team_id,
        org_unit_id=payload.org_unit_id,
        location=payload.location,
        is_all_day=payload.is_all_day,
        is_recurring=payload.is_recurring,
        recurring_pattern=payload.recurring_pattern,
        participants=json.dumps(payload.participants) if payload.participants else None
    )

    db.add(event)
    await db.commit()
    await db.refresh(event)

    await publish_event("calendar_event.created", {
        "event_id": event.id,
        "user_id": event.user_id,
        "title": event.title,
        "start_at": str(event.start_at),
        "end_at": str(event.end_at),
        "event_type": event.event_type.value
    })

    return event


@router.get("/events", response_model=List[CalendarEventOut])
async def get_events(
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        event_type: Optional[EventType] = None,
        db: AsyncSession = Depends(get_db)
):
    query = select(CalendarEvent).where(CalendarEvent.status != EventStatus.CANCELLED)

    if user_id:
        query = query.where(CalendarEvent.user_id == user_id)
    if team_id:
        query = query.where(CalendarEvent.team_id == team_id)
    if start_date:
        query = query.where(CalendarEvent.start_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.where(CalendarEvent.end_at <= datetime.combine(end_date, datetime.max.time()))
    if event_type:
        query = query.where(CalendarEvent.event_type == event_type)

    res = await db.execute(query.order_by(CalendarEvent.start_at))
    events = res.scalars().all()
    return events


@router.get("/events/{event_id}", response_model=CalendarEventOut)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    """Получение события по ID"""
    res = await db.execute(select(CalendarEvent).where(CalendarEvent.id == event_id))
    event = res.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.put("/events/{event_id}", response_model=CalendarEventOut)
async def update_event(event_id: int, payload: CalendarEventUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(CalendarEvent).where(CalendarEvent.id == event_id))
    event = res.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    update_data = payload.dict(exclude_unset=True)

    if 'start_at' in update_data or 'end_at' in update_data:
        start_at = update_data.get('start_at', event.start_at)
        end_at = update_data.get('end_at', event.end_at)

        if start_at >= end_at:
            raise HTTPException(status_code=400, detail="start_at must be before end_at")

        conflicts = await db.execute(
            select(CalendarEvent).where(
                and_(
                    CalendarEvent.user_id == event.user_id,
                    CalendarEvent.id != event_id,
                    CalendarEvent.status != EventStatus.CANCELLED,
                    or_(
                        and_(CalendarEvent.start_at < end_at, CalendarEvent.end_at > start_at)
                    )
                )
            )
        )
        if conflicts.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Time conflict detected")

    if update_data:
        await db.execute(
            update(CalendarEvent).where(CalendarEvent.id == event_id).values(**update_data)
        )
        await db.commit()
        await db.refresh(event)

        await publish_event("calendar_event.updated", {
            "event_id": event_id,
            "user_id": event.user_id,
            "updated_fields": list(update_data.keys())
        })

    return event


@router.delete("/events/{event_id}")
async def delete_event(event_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(CalendarEvent).where(CalendarEvent.id == event_id))
    event = res.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await db.execute(
        update(CalendarEvent).where(CalendarEvent.id == event_id).values(status=EventStatus.CANCELLED)
    )
    await db.commit()

    await publish_event("calendar_event.cancelled", {
        "event_id": event_id,
        "user_id": event.user_id,
        "title": event.title
    })

    return {"message": "Event cancelled successfully"}


@router.post("/availability", response_model=UserAvailabilityOut)
async def create_availability(payload: UserAvailabilityCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(UserAvailability).where(UserAvailability.user_id == payload.user_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Availability settings already exist for this user")

    availability = UserAvailability(**payload.dict())
    db.add(availability)
    await db.commit()
    await db.refresh(availability)

    await publish_event("user_availability.created", {
        "user_id": availability.user_id,
        "work_start_time": availability.work_start_time,
        "work_end_time": availability.work_end_time
    })

    return availability


@router.get("/availability/{user_id}", response_model=UserAvailabilityOut)
async def get_availability(user_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(UserAvailability).where(UserAvailability.user_id == user_id))
    availability = res.scalar_one_or_none()
    if not availability:
        raise HTTPException(status_code=404, detail="Availability settings not found")
    return availability


@router.put("/availability/{user_id}", response_model=UserAvailabilityOut)
async def update_availability(user_id: int, payload: UserAvailabilityUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(UserAvailability).where(UserAvailability.user_id == user_id))
    availability = res.scalar_one_or_none()
    if not availability:
        raise HTTPException(status_code=404, detail="Availability settings not found")

    update_data = payload.dict(exclude_unset=True)
    if update_data:
        await db.execute(
            update(UserAvailability).where(UserAvailability.user_id == user_id).values(**update_data)
        )
        await db.commit()
        await db.refresh(availability)

        await publish_event("user_availability.updated", {
            "user_id": user_id,
            "updated_fields": list(update_data.keys())
        })

    return availability


@router.post("/availability/check", response_model=AvailabilityResponse)
async def check_availability(payload: AvailabilityCheck, db: AsyncSession = Depends(get_db)):
    availability_res = await db.execute(
        select(UserAvailability).where(UserAvailability.user_id == payload.user_id)
    )
    availability = availability_res.scalar_one_or_none()

    if not availability or not availability.is_available:
        return AvailabilityResponse(is_available=False, conflicts=[], suggested_times=[])

    conflicts_res = await db.execute(
        select(CalendarEvent).where(
            and_(
                CalendarEvent.user_id == payload.user_id,
                CalendarEvent.status != EventStatus.CANCELLED,
                or_(
                    and_(CalendarEvent.start_at < payload.end_at, CalendarEvent.end_at > payload.start_at)
                )
            )
        )
    )
    conflicts = conflicts_res.scalars().all()

    is_available = len(conflicts) == 0

    suggested_times = []
    if not is_available and conflicts:
        suggested_times = [
            {
                "start_at": str(payload.start_at + timedelta(hours=1)),
                "end_at": str(payload.end_at + timedelta(hours=1))
            },
            {
                "start_at": str(payload.start_at - timedelta(hours=1)),
                "end_at": str(payload.end_at - timedelta(hours=1))
            }
        ]

    return AvailabilityResponse(
        is_available=is_available,
        conflicts=[CalendarEventOut.model_validate(conflict) for conflict in conflicts],
        suggested_times=suggested_times
    )


@router.get("/calendar", response_model=List[CalendarEventOut])
async def get_calendar_view(
        user_id: int = Query(..., description="ID пользователя"),
        start_date: date = Query(..., description="Начальная дата"),
        end_date: date = Query(..., description="Конечная дата"),
        include_team_events: bool = Query(False, description="Включить события команды"),
        team_id: Optional[int] = Query(None, description="ID команды"),
        db: AsyncSession = Depends(get_db)
):
    """Получение календаря на период"""
    query = select(CalendarEvent).where(
        and_(
            CalendarEvent.status != EventStatus.CANCELLED,
            CalendarEvent.start_at >= datetime.combine(start_date, datetime.min.time()),
            CalendarEvent.end_at <= datetime.combine(end_date, datetime.max.time())
        )
    )

    if include_team_events and team_id:
        query = query.where(
            or_(
                CalendarEvent.user_id == user_id,
                CalendarEvent.team_id == team_id
            )
        )
    else:
        query = query.where(CalendarEvent.user_id == user_id)

    res = await db.execute(query.order_by(CalendarEvent.start_at))
    events = res.scalars().all()
    return events


@router.post("/timeslots", response_model=TimeSlotOut)
async def create_time_slot(payload: TimeSlotCreate, db: AsyncSession = Depends(get_db)):
    slot = TimeSlot(**payload.dict())
    db.add(slot)
    await db.commit()
    await db.refresh(slot)
    return slot


@router.get("/timeslots", response_model=List[TimeSlotOut])
async def get_time_slots(
        user_id: Optional[int] = None,
        date: Optional[date] = None,
        db: AsyncSession = Depends(get_db)
):
    query = select(TimeSlot)

    if user_id:
        query = query.where(TimeSlot.user_id == user_id)
    if date:
        query = query.where(func.date(TimeSlot.date) == date)

    res = await db.execute(query.order_by(TimeSlot.start_time))
    slots = res.scalars().all()
    return slots


@router.post("/events/task/{task_id}")
async def create_task_event(task_id: int, user_id: int, start_at: datetime, end_at: datetime,
                            db: AsyncSession = Depends(get_db)):
    event = CalendarEvent(
        user_id=user_id,
        title=f"Task #{task_id}",
        event_type=EventType.TASK,
        start_at=start_at,
        end_at=end_at,
        task_id=task_id
    )

    db.add(event)
    await db.commit()
    await db.refresh(event)

    await publish_event("calendar_event.task_created", {
        "event_id": event.id,
        "task_id": task_id,
        "user_id": user_id
    })

    return event


@router.post("/events/meeting/{meeting_id}")
async def create_meeting_event(meeting_id: int, user_id: int, start_at: datetime, end_at: datetime,
                               db: AsyncSession = Depends(get_db)):
    event = CalendarEvent(
        user_id=user_id,
        title=f"Meeting #{meeting_id}",
        event_type=EventType.MEETING,
        start_at=start_at,
        end_at=end_at,
        meeting_id=meeting_id
    )

    db.add(event)
    await db.commit()
    await db.refresh(event)

    await publish_event("calendar_event.meeting_created", {
        "event_id": event.id,
        "meeting_id": meeting_id,
        "user_id": user_id
    })

    return event


@router.post("/events/validate")
async def validate_event_time(
        payload: dict = Body(...),
        db: AsyncSession = Depends(get_db)
):
    if not all(k in payload for k in ["participants", "start_at", "end_at"]):
        raise HTTPException(status_code=422, detail="Missing required fields")

    try:
        start_at = datetime.fromisoformat(payload["start_at"])
        end_at = datetime.fromisoformat(payload["end_at"])
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="Invalid datetime format")

    conflicts = []
    for user_id in payload["participants"]:
        res = await db.execute(
            select(CalendarEvent).where(
                and_(
                    CalendarEvent.user_id == user_id,
                    CalendarEvent.start_at < end_at,
                    CalendarEvent.end_at > start_at,
                    CalendarEvent.status != EventStatus.CANCELLED
                )
            )
        )
        events = res.scalars().all()
        if events:
            conflicts.append({
                "user_id": user_id,
                "conflicts": [{
                    "id": e.id,
                    "title": e.title,
                    "start_at": e.start_at.isoformat(),
                    "end_at": e.end_at.isoformat()
                } for e in events]
            })

    return {"is_valid": len(conflicts) == 0, "conflicts": conflicts}
