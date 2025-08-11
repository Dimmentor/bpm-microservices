from fastapi import APIRouter
from src.api.routes_calendar import router as calendar_router

router = APIRouter()
router.include_router(calendar_router, prefix="/calendar")


@router.get("/")
async def root():
    return {"service": "calendar-service"}
