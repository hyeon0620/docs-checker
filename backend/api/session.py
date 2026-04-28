from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from api.settings import settings

_engine_kwargs: dict[str, Any] = {"echo": False}
if settings.database_url.startswith("sqlite"):
    _engine_kwargs["poolclass"] = StaticPool
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(settings.database_url, **_engine_kwargs)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
