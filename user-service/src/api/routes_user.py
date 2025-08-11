from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from src.db.database import get_db
from src.db.models import User, UserStatus, UserRole
from src.api.schemas import UserCreate, UserUpdate, Token, UserOut, UserLogin
from src.api.auth_utils import hash_password, verify_password, create_access_token
from src.services.rabbitmq import publish_event
from typing import List

router = APIRouter()


@router.post("/register", response_model=UserOut)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.email == payload.email))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        name=payload.name,
        hashed_password=hash_password(payload.password),
        role=UserRole.USER,
        status=UserStatus.PENDING if payload.invite_code else UserStatus.ACTIVE,
        invite_code=payload.invite_code,
        phone=payload.phone,
        position=payload.position,
        department=payload.department
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await publish_event("user.created", {
        "user_id": user.id,
        "email": user.email,
        "team_id": user.team_id,
        "invite_code": user.invite_code
    })

    return user


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.email == payload.email))
    user = res.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(status_code=403, detail="User account is suspended")

    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/users", response_model=List[UserOut])
async def get_users(db: AsyncSession = Depends(get_db)):
    """Получение списка всех пользователей"""
    res = await db.execute(select(User))
    users = res.scalars().all()
    return users


@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Получение пользователя по ID"""
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=UserOut)
async def update_user(user_id: int, payload: UserUpdate, db: AsyncSession = Depends(get_db)):
    """Обновление информации о пользователе"""
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = payload.dict(exclude_unset=True)
    if update_data:
        await db.execute(
            update(User).where(User.id == user_id).values(**update_data)
        )
        await db.commit()
        await db.refresh(user)

        await publish_event("user.updated", {
            "user_id": user.id,
            "updated_fields": list(update_data.keys())
        })

    return user


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Удаление пользователя"""
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()

    await publish_event("user.deleted", {
        "user_id": user_id,
        "email": user.email
    })

    return {"message": "User deleted successfully"}


@router.put("/users/{user_id}/status")
async def update_user_status(user_id: int, status: UserStatus, db: AsyncSession = Depends(get_db)):
    """Обновление статуса пользователя"""
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.execute(
        update(User).where(User.id == user_id).values(status=status)
    )
    await db.commit()
    await db.refresh(user)

    await publish_event("user.status_changed", {
        "user_id": user_id,
        "new_status": status.value,
        "team_id": user.team_id
    })

    return {"message": f"User status updated to {status.value}"}


@router.put("/users/{user_id}/team")
async def assign_user_to_team(user_id: int, team_id: int, db: AsyncSession = Depends(get_db)):
    """Назначение пользователя в команду"""
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.execute(
        update(User).where(User.id == user_id).values(team_id=team_id)
    )
    await db.commit()
    await db.refresh(user)

    await publish_event("user.team_assigned", {
        "user_id": user_id,
        "team_id": team_id
    })

    return {"message": f"User assigned to team {team_id}"}
