from fastapi import APIRouter
from src.api.routes_tasks import router as tasks_router


router = APIRouter()
router.include_router(tasks_router)


@router.get("/")
async def root():
    return {"service": "task-service"}
