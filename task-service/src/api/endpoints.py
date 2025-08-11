from fastapi import APIRouter
from src.api.routes_tasks import router as tasks_router
from src.api.routes_meetings import router as meetings_router


router = APIRouter()
router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
router.include_router(meetings_router, prefix="/meetings", tags=["meetings"])


@router.get("/")
async def root():
    return {"service": "task-service"}
