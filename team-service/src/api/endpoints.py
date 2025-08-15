from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from src.api.utils import get_managers_chain, get_subordinates, build_unit_tree
from src.db.database import get_db
from src.db.models import Team, OrgUnit, OrgMember, TeamNews
from src.api.schemas import (
    TeamCreate, TeamUpdate, TeamOut,
    OrgUnitCreate, OrgUnitUpdate, OrgUnitOut,
    OrgMemberCreate, OrgMemberUpdate, OrgMemberOut,
    TeamNewsCreate, TeamNewsUpdate, TeamNewsOut
)
from src.services.rabbitmq import publish_event
import secrets
from typing import List, Optional

router = APIRouter()


@router.post("/teams", response_model=TeamOut)
async def create_team(payload: TeamCreate, db: AsyncSession = Depends(get_db)):
    invite_code = secrets.token_urlsafe(8)
    team = Team(
        name=payload.name,
        description=payload.description,
        owner_id=payload.owner_id,
        invite_code=invite_code
    )
    db.add(team)
    await db.commit()
    await db.refresh(team)

    await publish_event("team.created", {
        "team_id": team.id,
        "name": team.name,
        "owner_id": team.owner_id,
        "invite_code": team.invite_code
    })

    return team


@router.get("/teams", response_model=List[TeamOut])
async def get_teams(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Team).where(Team.is_active == True))
    teams = res.scalars().all()
    return teams


@router.get("/teams/{team_id}", response_model=TeamOut)
async def get_team(team_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Team).where(Team.id == team_id))
    team = res.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.put("/teams/{team_id}", response_model=TeamOut)
async def update_team(team_id: int, payload: TeamUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Team).where(Team.id == team_id))
    team = res.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    update_data = payload.dict(exclude_unset=True)
    if update_data:
        await db.execute(
            update(Team).where(Team.id == team_id).values(**update_data)
        )
        await db.commit()
        await db.refresh(team)

        await publish_event("team.updated", {
            "team_id": team_id,
            "updated_fields": list(update_data.keys())
        })

    return team


@router.delete("/teams/{team_id}")
async def delete_team(team_id: int, db: AsyncSession = Depends(get_db)):
    """Удаление команды (деактивация)"""
    res = await db.execute(select(Team).where(Team.id == team_id))
    team = res.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    await db.execute(
        update(Team).where(Team.id == team_id).values(is_active=False)
    )
    await db.commit()

    await publish_event("team.deactivated", {
        "team_id": team_id,
        "name": team.name
    })

    return {"message": "Team deactivated successfully"}


@router.post("/org_units", response_model=OrgUnitOut)
async def create_org_unit(payload: OrgUnitCreate, db: AsyncSession = Depends(get_db)):
    team_res = await db.execute(select(Team).where(Team.id == payload.team_id))
    if not team_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Team not found")

    if payload.parent_id:
        parent_res = await db.execute(select(OrgUnit).where(OrgUnit.id == payload.parent_id))
        parent = parent_res.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent unit not found")
        level = parent.level + 1
    else:
        level = 1

    unit = OrgUnit(
        team_id=payload.team_id,
        name=payload.name,
        parent_id=payload.parent_id,
        description=payload.description,
        level=level
    )
    db.add(unit)
    await db.commit()
    await db.refresh(unit)

    await publish_event("org_unit.created", {
        "unit_id": unit.id,
        "team_id": unit.team_id,
        "name": unit.name,
        "level": unit.level
    })

    return unit


@router.get("/org_units", response_model=List[OrgUnitOut])
async def get_org_units(team_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    query = select(OrgUnit).where(OrgUnit.is_active == True)
    if team_id:
        query = query.where(OrgUnit.team_id == team_id)

    res = await db.execute(query)
    units = res.scalars().all()
    return units


@router.get("/org_units/{unit_id}", response_model=OrgUnitOut)
async def get_org_unit(unit_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(OrgUnit).where(OrgUnit.id == unit_id))
    unit = res.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Organizational unit not found")
    return unit


@router.put("/org_units/{unit_id}", response_model=OrgUnitOut)
async def update_org_unit(unit_id: int, payload: OrgUnitUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(OrgUnit).where(OrgUnit.id == unit_id))
    unit = res.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Organizational unit not found")

    update_data = payload.dict(exclude_unset=True)
    if update_data:
        await db.execute(
            update(OrgUnit).where(OrgUnit.id == unit_id).values(**update_data)
        )
        await db.commit()
        await db.refresh(unit)

        await publish_event("org_unit.updated", {
            "unit_id": unit_id,
            "team_id": unit.team_id,
            "updated_fields": list(update_data.keys())
        })

    return unit


@router.delete("/org_units/{unit_id}")
async def delete_org_unit(unit_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(OrgUnit).where(OrgUnit.id == unit_id))
    unit = res.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Organizational unit not found")

    await db.execute(
        update(OrgUnit).where(OrgUnit.id == unit_id).values(is_active=False)
    )
    await db.commit()

    await publish_event("org_unit.deactivated", {
        "unit_id": unit_id,
        "team_id": unit.team_id
    })

    return {"message": "Organizational unit deactivated successfully"}


@router.post("/org_members", response_model=OrgMemberOut)
async def add_member(payload: OrgMemberCreate, db: AsyncSession = Depends(get_db)):
    unit_res = await db.execute(select(OrgUnit).where(OrgUnit.id == payload.org_unit_id))
    unit = unit_res.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Organizational unit not found")

    existing_res = await db.execute(
        select(OrgMember).where(
            OrgMember.user_id == payload.user_id,
            OrgMember.org_unit_id == payload.org_unit_id,
            OrgMember.is_active == True
        )
    )
    if existing_res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already in this unit")

    member = OrgMember(
        user_id=payload.user_id,
        org_unit_id=payload.org_unit_id,
        position=payload.position,
        manager_id=payload.manager_id
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)

    await publish_event("org_member.added", {
        "member_id": member.id,
        "user_id": member.user_id,
        "org_unit_id": member.org_unit_id,
        "team_id": unit.team_id
    })

    return member


@router.get("/org_members", response_model=List[OrgMemberOut])
async def get_members(org_unit_id: Optional[int] = None, team_id: Optional[int] = None,
                      db: AsyncSession = Depends(get_db)):
    query = select(OrgMember).where(OrgMember.is_active == True)
    if org_unit_id:
        query = query.where(OrgMember.org_unit_id == org_unit_id)
    elif team_id:
        unit_ids = await db.execute(
            select(OrgUnit.id).where(OrgUnit.team_id == team_id, OrgUnit.is_active == True)
        )
        unit_ids = unit_ids.scalars().all()
        if unit_ids:
            query = query.where(OrgMember.org_unit_id.in_(unit_ids))

    res = await db.execute(query)
    members = res.scalars().all()
    return members


@router.put("/org_members/{member_id}", response_model=OrgMemberOut)
async def update_member(member_id: int, payload: OrgMemberUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(OrgMember).where(OrgMember.id == member_id))
    member = res.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    update_data = payload.dict(exclude_unset=True)
    if update_data:
        await db.execute(
            update(OrgMember).where(OrgMember.id == member_id).values(**update_data)
        )
        await db.commit()
        await db.refresh(member)

        await publish_event("org_member.updated", {
            "member_id": member_id,
            "user_id": member.user_id,
            "updated_fields": list(update_data.keys())
        })

    return member


@router.delete("/org_members/{member_id}")
async def remove_member(member_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(OrgMember).where(OrgMember.id == member_id))
    member = res.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    await db.execute(
        update(OrgMember).where(OrgMember.id == member_id).values(
            is_active=False,
            end_date=func.now()
        )
    )
    await db.commit()

    await publish_event("org_member.removed", {
        "member_id": member_id,
        "user_id": member.user_id,
        "org_unit_id": member.org_unit_id
    })

    return {"message": "Member removed successfully"}


@router.post("/news", response_model=TeamNewsOut)
async def create_news(payload: TeamNewsCreate, db: AsyncSession = Depends(get_db)):
    team_res = await db.execute(select(Team).where(Team.id == payload.team_id))
    if not team_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Team not found")

    news = TeamNews(
        team_id=payload.team_id,
        author_id=payload.author_id,
        title=payload.title,
        content=payload.content,
        is_published=payload.is_published
    )
    db.add(news)
    await db.commit()
    await db.refresh(news)

    await publish_event("team_news.created", {
        "news_id": news.id,
        "team_id": news.team_id,
        "author_id": news.author_id,
        "title": news.title
    })

    return news


@router.get("/news", response_model=List[TeamNewsOut])
async def get_news(team_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    """Получение списка новостей"""
    query = select(TeamNews).where(TeamNews.is_published == True)
    if team_id:
        query = query.where(TeamNews.team_id == team_id)

    res = await db.execute(query.order_by(TeamNews.created_at.desc()))
    news_list = res.scalars().all()
    return news_list


@router.get("/news/{news_id}", response_model=TeamNewsOut)
async def get_news_item(news_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(TeamNews).where(TeamNews.id == news_id))
    news = res.scalar_one_or_none()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return news


@router.put("/news/{news_id}", response_model=TeamNewsOut)
async def update_news(news_id: int, payload: TeamNewsUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(TeamNews).where(TeamNews.id == news_id))
    news = res.scalar_one_or_none()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    update_data = payload.dict(exclude_unset=True)
    if update_data:
        await db.execute(
            update(TeamNews).where(TeamNews.id == news_id).values(**update_data)
        )
        await db.commit()
        await db.refresh(news)

        # Публикуем событие обновления новости
        await publish_event("team_news.updated", {
            "news_id": news_id,
            "team_id": news.team_id,
            "updated_fields": list(update_data.keys())
        })

    return news


@router.delete("/news/{news_id}")
async def delete_news(news_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(TeamNews).where(TeamNews.id == news_id))
    news = res.scalar_one_or_none()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    await db.execute(delete(TeamNews).where(TeamNews.id == news_id))
    await db.commit()

    # Публикуем событие удаления новости
    await publish_event("team_news.deleted", {
        "news_id": news_id,
        "team_id": news.team_id
    })

    return {"message": "News deleted successfully"}


@router.get("/org_structure/{team_id}")
async def get_org_structure(
        team_id: int,
        depth: int = 3,
        db: AsyncSession = Depends(get_db)
):
    units_res = await db.execute(
        select(OrgUnit).where(
            and_(
                OrgUnit.team_id == team_id,
                OrgUnit.is_active == True
            )
        ).order_by(OrgUnit.level)
    )
    units = units_res.scalars().all()

    if not units:
        raise HTTPException(status_code=404, detail="No organizational units found")

    root_units = [u for u in units if u.level == 1]
    org_tree = []

    for unit in root_units:
        org_tree.append(await build_unit_tree(unit, units, depth, db))

    return org_tree


@router.get("/org_members/{user_id}/hierarchy")
async def get_user_hierarchy(
        user_id: int,
        db: AsyncSession = Depends(get_db)
):
    member_res = await db.execute(
        select(OrgMember).where(
            and_(
                OrgMember.user_id == user_id,
                OrgMember.is_active == True
            )
        )
    )
    member = member_res.scalar_one_or_none()

    if not member:
        raise HTTPException(status_code=404, detail="User not found in any org unit")

    managers = await get_managers_chain(member.manager_id, db)

    subordinates = await get_subordinates(user_id, db)

    return {
        "managers": managers,
        "subordinates": subordinates,
        "current_position": {
            "org_unit_id": member.org_unit_id,
            "position": member.position,
            "manager_id": member.manager_id
        }
    }


@router.get("/team/invites/validate")
async def validate_invite(
        code: str = Query(..., description="Invite code"),
        db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(Team).where(
            and_(
                Team.invite_code == code,
                Team.is_active == True
            )
        )
    )
    team = res.scalar_one_or_none()

    if not team:
        raise HTTPException(status_code=404, detail="Invalid invite code")

    return {"team_id": team.id, "team_name": team.name}
