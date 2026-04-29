from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.ai import Corrector, get_corrector
from api.auth import (
    COOKIE_NAME,
    authenticate,
    create_token,
    current_user,
    hash_password,
    require_admin,
)
from api.config import settings
from api.db import SessionLocal, engine, get_session
from api.initial_admin import ensure_initial_admin
from api.models import Base, User
from api.schemas import (
    AdminUserCreateIn,
    AdminUserOut,
    CorrectIn,
    CorrectOut,
    LoginIn,
    UserOut,
)

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

# CORS：フロント（別ポート）から Cookie 付きで叩けるようにする。
# allow_credentials=True を有効にする時、allow_origins に "*" は使えない。
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


# === 管理者エンドポイント ===


@app.get("/api/admin/users", response_model=list[AdminUserOut])
async def admin_list_users(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[User]:
    """admin による一覧取得：deleted_at が null のユーザーを返す。"""
    stmt = select(User).where(User.deleted_at.is_(None)).order_by(User.id)
    return list((await session.execute(stmt)).scalars().all())


@app.post("/api/admin/user", response_model=AdminUserOut)
async def admin_create_user(
    body: AdminUserCreateIn,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> User:
    """admin によるユーザー登録：username が重複してたら 409。"""
    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        role="user",
        is_active=True,
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "username already exists") from e
    await session.refresh(user)
    return user


@app.patch("/api/admin/user/{user_id}/deactivate", response_model=AdminUserOut)
async def admin_deactivate_user(
    user_id: int,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> User:
    """admin によるユーザー無効化：is_active=False にしてソフトデリート。自分自身は無効化できない。"""
    if user_id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "cannot deactivate yourself")
    user = await session.get(User, user_id)
    if user is None or user.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    user.is_active = False
    await session.commit()
    await session.refresh(user)
    return user
