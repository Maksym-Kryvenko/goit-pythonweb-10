import redis.asyncio as aioredis
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db_session
from src.database.redis import get_redis
from src.schemas.users import UserCreate, UserResponse, Token, RefreshTokenRequest
from src.services.users import UserService
from src.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    invalidate_user_cache,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: AsyncSession = Depends(get_db_session)):
    user_service = UserService(db)

    if await user_service.get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already in use"
        )
    if await user_service.get_user_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already in use"
        )

    return await user_service.create_user(user_data)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session),
):
    user_service = UserService(db)
    user = await user_service.get_user_by_username(form_data.username)
    if not user or not user_service.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = await create_access_token({"sub": user.username})
    refresh_token = await create_refresh_token({"sub": user.username})
    await user_service.set_refresh_token(user.id, refresh_token)

    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
async def refresh(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session),
    redis: aioredis.Redis = Depends(get_redis),
):
    username = decode_token(payload.refresh_token, expected_scope="refresh_token")

    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    if user is None or user.refresh_token != payload.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = await create_access_token({"sub": user.username})
    refresh_token = await create_refresh_token({"sub": user.username})
    await user_service.set_refresh_token(user.id, refresh_token)
    await invalidate_user_cache(username, redis)

    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session),
    redis: aioredis.Redis = Depends(get_redis),
):
    username = decode_token(payload.refresh_token, expected_scope="refresh_token")
    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    if user is not None:
        await user_service.set_refresh_token(user.id, None)
        await invalidate_user_cache(username, redis)
