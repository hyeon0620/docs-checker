"""POST /api/correct のテスト。

実 Gemini を呼ばず、`get_corrector` の依存を `dependency_overrides` で
フェイク関数に差し替える。API キー無しで高速に検証できる。
"""

import pytest
import pytest_asyncio

from api.ai import get_corrector
from api.auth import hash_password
from api.main import app
from api.models import User
from api.schemas import CorrectOut, IssueItem

# === フェイクの校正関数とフィクスチャ ===


async def _fake_corrector(text: str) -> CorrectOut:
    """テスト用の固定レスポンス。"""
    if text == "":
        return CorrectOut(corrected="", score=100, issues=[])
    return CorrectOut(
        corrected="修正後テキスト",
        score=85,
        issues=[
            IssueItem(
                category="typo",
                span="誤字",
                suggestion="正字",
                reason="誤字を修正しました",
            )
        ],
    )


@pytest_asyncio.fixture
async def override_corrector():
    """テスト用：get_corrector を _fake_corrector に差し替える。"""
    app.dependency_overrides[get_corrector] = lambda: _fake_corrector
    yield
    app.dependency_overrides.pop(get_corrector, None)


async def _login_as_taro(client, session) -> None:
    user = User(
        username="taro",
        password_hash=hash_password("taro1234"),
        role="user",
    )
    session.add(user)
    await session.commit()
    res = await client.post("/api/login", json={"username": "taro", "password": "taro1234"})
    assert res.status_code == 200


# === テスト ===


@pytest.mark.asyncio
async def test_correct_requires_auth(client) -> None:
    res = await client.post("/api/correct", json={"original": "テスト"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_correct_success(client, session, override_corrector) -> None:
    await _login_as_taro(client, session)

    res = await client.post("/api/correct", json={"original": "テストです。"})
    assert res.status_code == 200
    body = res.json()
    assert body["corrected"] == "修正後テキスト"
    assert body["score"] == 85
    assert len(body["issues"]) == 1
    assert body["issues"][0]["category"] == "typo"


@pytest.mark.asyncio
async def test_correct_empty_text(client, session, override_corrector) -> None:
    await _login_as_taro(client, session)

    res = await client.post("/api/correct", json={"original": ""})
    assert res.status_code == 200
    body = res.json()
    assert body["score"] == 100
    assert body["issues"] == []
