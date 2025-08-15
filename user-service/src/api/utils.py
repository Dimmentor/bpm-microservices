import logging
from datetime import datetime, timedelta
import httpx
from fastapi import HTTPException
from jose import jwt
from passlib.context import CryptContext
from src.config import JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, settings

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def validate_invite_code(code: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.TEAM_SERVICE_URL}/api/team/invites/validate",
                params={"code": code},
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json()
            return None
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.error(f"Team service connection error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Team service unavailable"
        )
