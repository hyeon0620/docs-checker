"""POST /api/admin/user / PATCH /api/admin/user/{id}/deactivate / GET /api/admin/users のテスト。"""

import pytest

from api.auth import hash_password
from api.models import User

# === ヘルパ ===


async def _create_user(
    session,
    *,
    username: str,
    password: str = "pass1234",
    role: str = "user",
    is_active: bool = True,
) -> User:
    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def _login(client, username: str, password: str) -> None:
    res = await client.post("/api/login", json={"username": username, "password": password})
    assert res.status_code == 200


# === GET /api/admin/users ===


@pytest.mark.asyncio
async def test_list_users_requires_admin(client, session) -> None:
    await _create_user(session, username="taro")
    await _login(client, "taro", "pass1234")

    res = await client.get("/api/admin/users")
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_list_users_as_admin(client, session) -> None:
    await _create_user(session, username="root", role="admin")
    await _create_user(session, username="taro")
    await _login(client, "root", "pass1234")

    res = await client.get("/api/admin/users")
    assert res.status_code == 200
    data = res.json()
    usernames = [u["username"] for u in data]
    assert "root" in usernames
    assert "taro" in usernames


# === POST /api/admin/user ===


@pytest.mark.asyncio
async def test_create_user_requires_admin(client, session) -> None:
    await _create_user(session, username="taro")
    await _login(client, "taro", "pass1234")

    res = await client.post("/api/admin/user", json={"username": "new", "password": "pass1234"})
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_create_user_as_admin(client, session) -> None:
    await _create_user(session, username="root", role="admin")
    await _login(client, "root", "pass1234")

    res = await client.post("/api/admin/user", json={"username": "newbie", "password": "newpass1"})
    assert res.status_code == 200
    body = res.json()
    assert body["username"] == "newbie"
    assert body["role"] == "user"
    assert body["is_active"] is True

    # 作成された user で実際にログインできること
    res = await client.post("/api/login", json={"username": "newbie", "password": "newpass1"})
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_create_user_duplicate_username(client, session) -> None:
    await _create_user(session, username="root", role="admin")
    await _create_user(session, username="taro")
    await _login(client, "root", "pass1234")

    res = await client.post("/api/admin/user", json={"username": "taro", "password": "another"})
    assert res.status_code == 409


# === PATCH /api/admin/user/{id}/deactivate ===


@pytest.mark.asyncio
async def test_deactivate_requires_admin(client, session) -> None:
    target = await _create_user(session, username="taro")
    await _create_user(session, username="hanako")
    await _login(client, "hanako", "pass1234")

    res = await client.patch(f"/api/admin/user/{target.id}/deactivate")
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_deactivate_blocks_login(client, session) -> None:
    admin = await _create_user(session, username="root", role="admin")
    target = await _create_user(session, username="taro")
    await _login(client, "root", "pass1234")

    res = await client.patch(f"/api/admin/user/{target.id}/deactivate")
    assert res.status_code == 200
    assert res.json()["is_active"] is False

    # 無効化後のログインは 401
    await client.post("/api/logout")
    res = await client.post("/api/login", json={"username": "taro", "password": "pass1234"})
    assert res.status_code == 401
    # admin 自身はまだログインできる
    res = await client.post("/api/login", json={"username": admin.username, "password": "pass1234"})
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_deactivate_self_forbidden(client, session) -> None:
    admin = await _create_user(session, username="root", role="admin")
    await _login(client, "root", "pass1234")

    res = await client.patch(f"/api/admin/user/{admin.id}/deactivate")
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_deactivate_unknown_user(client, session) -> None:
    await _create_user(session, username="root", role="admin")
    await _login(client, "root", "pass1234")

    res = await client.patch("/api/admin/user/9999/deactivate")
    assert res.status_code == 404
