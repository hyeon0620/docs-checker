from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from api.config import settings

# === エンジンとセッション生成器（モジュール起動時に1回だけ作る） ===

_engine_kwargs: dict[str, Any] = {"echo": False}
if settings.database_url.startswith("sqlite"):
    # テスト用 sqlite では in-memory の同一コネクションを共有する
    _engine_kwargs["poolclass"] = StaticPool
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(settings.database_url, **_engine_kwargs)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


# === 依存関数 ===


async def get_session() -> AsyncGenerator[AsyncSession]:
    """リクエスト処理時：エンドポイントが Depends(get_session) で受け取る AsyncSession。"""
    async with SessionLocal() as session:
        yield session
