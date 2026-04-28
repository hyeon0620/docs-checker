from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import (
    COOKIE_NAME,
    authenticate,
    create_token,
    current_user,
)
from api.initial_admin import ensure_initial_admin
from api.models import Base, User
from api.session import SessionLocal, engine, get_session


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        await ensure_initial_admin(session)
    yield
    await engine.dispose()


app = FastAPI(title="Docs Checker API", lifespan=lifespan)


class LoginIn(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    role: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/login", response_model=UserOut)
async def login(
    body: LoginIn,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> User:
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
    response.delete_cookie(COOKIE_NAME)
    return {"status": "ok"}


@app.get("/api/me", response_model=UserOut)
async def me(user: User = Depends(current_user)) -> User:
    return user
