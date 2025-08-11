from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from src.db.database import get_db
from src.db.models import CalendarEvent, UserAvailability, TimeSlot, EventType, EventStatus
from src.api.schemas import (
    CalendarEventCreate, CalendarEventUpdate, CalendarEventOut,
    UserAvailabilityCreate, UserAvailabilityUpdate, UserAvailabilityOut,
    TimeSlotCreate, TimeSlotOut, AvailabilityCheck, AvailabilityResponse, CalendarView
)
from src.services.rabbitmq import publish_event
from typing import List, Optional
from datetime import datetime, date, timedelta
import json

router = APIRouter()


@router.post("/events", response_model=CalendarEventOut)
async def create_event(payload: CalendarEventCreate, db: AsyncSession = Depends(get_db)):
    """Создание события в календаре"""
    if payload.start_at >= payload.end_at:
        raise HTTPException(status_code=400, detail="start_at must be before end_at")

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
        meeting_id=payload.meeting_id,
        team_id=payload.team_id,
        org_unit_id=payload.org_unit_id,
        location=payload.location,
        is_all_day=payload.is_all_day,
        is_recurring=payload.is_recurring,
        recurring_pattern=payload.recurring_pattern,
        recurring_end_date=payload.recurring_end_date,
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
    """Получение списка событий с фильтрацией"""
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
    """Обновление события"""
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
    """Удаление события (отмена)"""
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
    """Создание настроек доступности пользователя"""
    # Проверяем, что настройки еще не существуют
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
    """Получение настроек доступности пользователя"""
    res = await db.execute(select(UserAvailability).where(UserAvailability.user_id == user_id))
    availability = res.scalar_one_or_none()
    if not availability:
        raise HTTPException(status_code=404, detail="Availability settings not found")
    return availability


@router.put("/availability/{user_id}", response_model=UserAvailabilityOut)
async def update_availability(user_id: int, payload: UserAvailabilityUpdate, db: AsyncSession = Depends(get_db)):
    """Обновление настроек доступности"""
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
    """Проверка доступности времени для пользователя"""
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
    """Создание временного слота"""
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
    """Получение временных слотов"""
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
    """Создание события для задачи"""
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
    """Создание события для встречи"""
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
