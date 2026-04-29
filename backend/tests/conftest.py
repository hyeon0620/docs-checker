"""テスト用 fixtures。

api 配下のモジュールをインポートする前に環境変数を設定し、
全テストで sqlite (in-memory, StaticPool 共有) を使う。
"""

import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-32-bytes-do-not-use-in-prod-XX"
os.environ["INITIAL_ADMIN_PASSWORD"] = ""

from collections.abc import AsyncGenerator  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from api.db import SessionLocal, engine  # noqa: E402
from api.main import app  # noqa: E402
from api.models import Base  # noqa: E402

# === バックエンド指定 ===


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """anyio 互換テストで使う非同期バックエンドの指定（asyncio に固定）。"""
    return "asyncio"


# === テストごとの fixtures ===


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    """テスト時：ASGI 経由で叩く HTTP クライアント。前後でテーブルを drop_all + create_all して状態をリセット。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def session() -> AsyncGenerator:
    """テスト時：HTTP を経由せず直接 DB に書き込み/読み取りしたい時に使う AsyncSession。"""
    async with SessionLocal() as s:
        yield s
