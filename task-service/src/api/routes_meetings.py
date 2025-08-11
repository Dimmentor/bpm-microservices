from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.database import get_db
from src.db.models import Meeting, MeetingParticipant
from src.api.schemas import MeetingCreate
from src.services.rabbitmq import publish_event

router = APIRouter()


@router.post("/meetings")
async def create_meeting(payload: MeetingCreate, db: AsyncSession = Depends(get_db)):
    if payload.start_at >= payload.end_at:
        raise HTTPException(status_code=400, detail="start_at must be before end_at")
    meeting = Meeting(title=payload.title, creator_id=payload.creator_id, team_id=payload.team_id,
                      start_at=payload.start_at, end_at=payload.end_at)
    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)

    for user_id in payload.participants:
        mp = MeetingParticipant(meeting_id=meeting.id, user_id=user_id, status="pending")
        db.add(mp)
    await db.commit()
    await publish_event("meeting.scheduled", {"meeting_id": meeting.id, "start_at": str(payload.start_at),
                                              "participants": payload.participants})
    return {"id": meeting.id}
