from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from src.db.database import get_db
from src.db.models import Team, OrgUnit, OrgMember
from src.api.schemas import TeamCreate, TeamOut, OrgUnitCreate, OrgMemberCreate
import secrets

router = APIRouter()


@router.post("/teams", response_model=TeamOut)
async def create_team(payload: TeamCreate, db: AsyncSession = Depends(get_db)):
    invite_code = secrets.token_urlsafe(8)
    team = Team(name=payload.name, invite_code=invite_code)
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return team


@router.get("/teams/{team_id}", response_model=TeamOut)
async def get_team(team_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Team).where(Team.id == team_id))
    team = res.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.post("/org_units")
async def create_org_unit(payload: OrgUnitCreate, db: AsyncSession = Depends(get_db)):
    unit = OrgUnit(team_id=payload.team_id, name=payload.name, parent_id=payload.parent_id,
                   description=payload.description)
    db.add(unit)
    await db.commit()
    await db.refresh(unit)
    return {"id": unit.id, "name": unit.name}


@router.post("/org_members")
async def add_member(payload: OrgMemberCreate, db: AsyncSession = Depends(get_db)):
    member = OrgMember(user_id=payload.user_id, org_unit_id=payload.org_unit_id, position=payload.position,
                       manager_id=payload.manager_id)
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return {"id": member.id}
