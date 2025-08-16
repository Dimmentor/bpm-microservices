from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import OrgMember, OrgUnit


async def get_managers_chain(manager_id: Optional[int], db: AsyncSession) -> list:
    if not manager_id:
        return []

    member_res = await db.execute(
        select(OrgMember).where(
            and_(
                OrgMember.user_id == manager_id,
                OrgMember.is_active == True
            )
        )
    )
    manager = member_res.scalar_one_or_none()

    if not manager:
        return []

    chain = [{
        "user_id": manager.user_id,
        "position": manager.position,
        "org_unit_id": manager.org_unit_id
    }]

    if manager.manager_id:
        chain.extend(await get_managers_chain(manager.manager_id, db))

    return chain


async def get_subordinates(user_id: int, db: AsyncSession) -> list:
    subs_res = await db.execute(
        select(OrgMember).where(
            and_(
                OrgMember.manager_id == user_id,
                OrgMember.is_active == True
            )
        )
    )
    subordinates = subs_res.scalars().all()

    result = []
    for sub in subordinates:
        sub_data = {
            "user_id": sub.user_id,
            "position": sub.position,
            "org_unit_id": sub.org_unit_id,
            "subordinates": await get_subordinates(sub.user_id, db)
        }
        result.append(sub_data)

    return result


async def build_unit_tree(unit: OrgUnit, all_units: list, max_depth: int, db: AsyncSession,
                          current_depth: int = 1) -> dict:
    if current_depth > max_depth:
        return None

    members_res = await db.execute(
        select(OrgMember).where(
            and_(
                OrgMember.org_unit_id == unit.id,
                OrgMember.is_active == True
            )
        )
    )
    members = members_res.scalars().all()

    children = [u for u in all_units if u.parent_id == unit.id]

    unit_data = {
        "id": unit.id,
        "name": unit.name,
        "level": unit.level,
        "description": unit.description,
        "members": [
            {
                "user_id": m.user_id,
                "position": m.position,
                "manager_id": m.manager_id,
                "start_date": m.start_date
            } for m in members
        ],
        "children": []
    }

    for child in children:
        child_tree = await build_unit_tree(
            child, all_units, max_depth, db, current_depth + 1
        )
        if child_tree:
            unit_data["children"].append(child_tree)

    return unit_data
