from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import User
from api.db import get_session
from api.config import settings

ALGORITHM = "HS256"
COOKIE_NAME = "token"


# === ユーザー登録 ===


def hash_password(password: str) -> str:
    """ユーザー登録時：平文パスワードを bcrypt ハッシュに変換して DB 保存用にする。"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


# === ログイン処理 ===


async def authenticate(
    session: AsyncSession, username: str, password: str
) -> User | None:
    """ログイン処理：DB から有効ユーザーを引いてパスワード照合。失敗は None。"""
    stmt = select(User).where(
        User.username == username,
        User.is_active == True,  # noqa: E712
        User.deleted_at.is_(None),
    )
    user = (await session.execute(stmt)).scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def verify_password(password: str, password_hash: str) -> bool:
    """ログイン時（authenticate 内）：入力された平文と DB のハッシュを照合する。"""
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_token(user: User) -> str:
    """ログイン成功時：user 情報を JWT に詰めて署名する。Cookie にセットする文字列を返す。"""
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "exp": datetime.now(UTC) + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


# === リクエストごとの認証 ===


async def current_user(
    token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    session: AsyncSession = Depends(get_session),
) -> User:
    """認証必須エンドポイント用の依存関数：Cookie の JWT を検証してログイン中のユーザーを返す。"""
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


def decode_token(token: str) -> dict:
    """認証必須リクエスト時（current_user 内）：JWT 文字列を検証して中身（payload）を取り出す。署名 NG / 期限切れは例外。"""
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])


async def require_admin(user: User = Depends(current_user)) -> User:
    """admin 専用エンドポイント用の依存関数：current_user に role チェックを上乗せする。"""
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admin only")
    return user
