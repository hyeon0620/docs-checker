from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import hash_password
from api.config import settings
from api.models import User


async def ensure_initial_admin(session: AsyncSession) -> None:
    """サーバー起動時（lifespan 内）：初期 admin を作成する（無ければ作る、有れば何もしない / 冪等）。"""
    if not settings.initial_admin_password:
        return

    stmt = select(User).where(User.username == settings.initial_admin_username)
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        return

    admin = User(
        username=settings.initial_admin_username,
        password_hash=hash_password(settings.initial_admin_password),
        role="admin",
        is_active=True,
    )
    session.add(admin)
    await session.commit()
