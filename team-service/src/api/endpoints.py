from fastapi import APIRouter
from src.api.routes_team import router as team_router


router = APIRouter()
router.include_router(team_router, prefix="/team", tags=["team"])


@router.get("/")
async def root():
    return {"service": "team-service"}
