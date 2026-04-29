from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.ai import Corrector, get_corrector
from api.auth import (
    COOKIE_NAME,
    authenticate,
    create_token,
    current_user,
)
from api.db import SessionLocal, engine, get_session
from api.initial_admin import ensure_initial_admin
from api.models import Base, User
from api.schemas import CorrectIn, CorrectOut, LoginIn, UserOut


# === 起動時セットアップ ===


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """サーバー起動時：DB テーブル作成 + 初期 admin の自動作成。終了時：エンジンを片付け。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        await ensure_initial_admin(session)
    yield
    await engine.dispose()


app = FastAPI(title="Docs Checker API", lifespan=lifespan)


# === ヘルスチェック ===


@app.get("/health")
def health() -> dict[str, str]:
    """疎通確認用：ロードバランサ・監視からのヘルスチェックに応える。認証不要。"""
    return {"status": "ok"}


# === 認証エンドポイント ===


@app.post("/api/login", response_model=UserOut)
async def login(
    body: LoginIn,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> User:
    """ログイン時：認証 → JWT 発行 → Cookie にセット。失敗時は 401。"""
    user = await authenticate(session, body.username, body.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    response.set_cookie(
        key=COOKIE_NAME,
        value=create_token(user),
        httponly=True,
        samesite="lax",
        secure=False,
    )
    return user


@app.post("/api/logout")
async def logout(response: Response) -> dict[str, str]:
    """ログアウト時：Cookie を削除。発行済み JWT は exp(24h) まで有効（許容）。"""
    response.delete_cookie(COOKIE_NAME)
    return {"status": "ok"}


@app.get("/api/me", response_model=UserOut)
async def me(user: User = Depends(current_user)) -> User:
    """認証必須の疎通確認用：current_user を通って現在のログインユーザー情報を返す。"""
    return user


# === 校正エンドポイント ===


@app.post("/api/correct", response_model=CorrectOut)
async def correct(
    body: CorrectIn,
    user: User = Depends(current_user),
    corrector: Corrector = Depends(get_corrector),
) -> CorrectOut:
    """校正リクエスト時：認証済みユーザーのテキストを Gemini で校正して返す。永続化しない。"""
    return await corrector(body.original)
