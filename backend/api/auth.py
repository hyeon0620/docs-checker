from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import User
from api.session import get_session
from api.settings import settings

ALGORITHM = "HS256"
COOKIE_NAME = "token"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "exp": datetime.now(UTC) + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])


async def current_user(
    token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    session: AsyncSession = Depends(get_session),
) -> User:
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated")
    try:
        payload = decode_token(token)
    except jwt.PyJWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token") from e

    user_id = int(payload["sub"])
    user = await session.get(User, user_id)
    if user is None or not user.is_active or user.deleted_at is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found")
    return user


async def require_admin(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admin only")
    return user


async def authenticate(
    session: AsyncSession, username: str, password: str
) -> User | None:
    stmt = select(User).where(
        User.username == username,
        User.is_active == True,  # noqa: E712
        User.deleted_at.is_(None),
    )
    user = (await session.execute(stmt)).scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user
