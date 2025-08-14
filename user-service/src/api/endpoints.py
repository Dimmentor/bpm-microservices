from fastapi import APIRouter
from src.api.routes_user import router as user_router


router = APIRouter()
router.include_router(user_router)


@router.get("/")
async def root():
    return {"service": "auth-service"}