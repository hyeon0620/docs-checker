import pytest

from api.auth import hash_password
from api.models import User


async def _create_user(
    session, *, username: str = "taro", password: str = "taro1234", role: str = "user"
) -> User:
    user = User(username=username, password_hash=hash_password(password), role=role)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_login_success_sets_cookie(client, session) -> None:
    await _create_user(session)
    res = await client.post(
        "/api/login", json={"username": "taro", "password": "taro1234"}
    )
    assert res.status_code == 200
    assert res.json()["username"] == "taro"
    assert "token" in res.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client, session) -> None:
    await _create_user(session)
    res = await client.post(
        "/api/login", json={"username": "taro", "password": "wrong"}
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_user(client) -> None:
    res = await client.post(
        "/api/login", json={"username": "ghost", "password": "x"}
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_cookie(client) -> None:
    res = await client.get("/api/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_me_with_cookie_returns_user(client, session) -> None:
    await _create_user(session)
    login = await client.post(
        "/api/login", json={"username": "taro", "password": "taro1234"}
    )
    assert login.status_code == 200

    me = await client.get("/api/me")
    assert me.status_code == 200
    assert me.json()["username"] == "taro"
    assert me.json()["role"] == "user"


@pytest.mark.asyncio
async def test_logout_clears_cookie(client, session) -> None:
    await _create_user(session)
    await client.post(
        "/api/login", json={"username": "taro", "password": "taro1234"}
    )

    res = await client.post("/api/logout")
    assert res.status_code == 200

    me = await client.get("/api/me")
    assert me.status_code == 401


@pytest.mark.asyncio
async def test_inactive_user_cannot_login(client, session) -> None:
    user = await _create_user(session)
    user.is_active = False
    await session.commit()

    res = await client.post(
        "/api/login", json={"username": "taro", "password": "taro1234"}
    )
    assert res.status_code == 401
