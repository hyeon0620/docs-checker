import pytest
from sqlalchemy import select

from api.initial_admin import ensure_initial_admin
from api.models import User
from api.config import settings


@pytest.mark.asyncio
async def test_creates_admin_when_password_set(client, session, monkeypatch) -> None:
    monkeypatch.setattr(settings, "initial_admin_password", "Adm1n!Pass")
    monkeypatch.setattr(settings, "initial_admin_username", "rootadmin")

    await ensure_initial_admin(session)

    stmt = select(User).where(User.username == "rootadmin")
    user = (await session.execute(stmt)).scalar_one()
    assert user.role == "admin"


@pytest.mark.asyncio
async def test_idempotent_does_not_duplicate(client, session, monkeypatch) -> None:
    monkeypatch.setattr(settings, "initial_admin_password", "Adm1n!Pass")
    monkeypatch.setattr(settings, "initial_admin_username", "rootadmin")

    await ensure_initial_admin(session)
    await ensure_initial_admin(session)
    await ensure_initial_admin(session)

    stmt = select(User).where(User.username == "rootadmin")
    users = (await session.execute(stmt)).scalars().all()
    assert len(users) == 1


@pytest.mark.asyncio
async def test_skips_when_password_empty(client, session, monkeypatch) -> None:
    monkeypatch.setattr(settings, "initial_admin_password", "")

    await ensure_initial_admin(session)

    stmt = select(User)
    users = (await session.execute(stmt)).scalars().all()
    assert len(users) == 0
