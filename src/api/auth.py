import logging
import redis.asyncio as aioredis
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.limiter import limiter
from src.database.db import get_db_session
from src.database.redis import get_redis
from src.schemas.users import UserCreate, UserResponse, Token, RefreshTokenRequest, RequestEmail, LoginRequest
from src.services.users import UserService
from src.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_email_from_token,
    invalidate_user_cache,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def signup(
    request: Request,
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
):
    user_service = UserService(db)

    if await user_service.get_user_by_email(user_data.email):
        logger.info(f"Signup failed: email already registered")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already in use"
        )
    if await user_service.get_user_by_username(user_data.username):
        logger.info(f"Signup failed: username already taken")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already in use"
        )

    new_user = await user_service.create_user(user_data)
    logger.info(f"New user registered: {new_user.username}")

    from src.services.email import send_email
    background_tasks.add_task(send_email, new_user.email, new_user.username, str(request.base_url))

    return new_user


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
):
    user_service = UserService(db)
    user = await user_service.get_user_by_username(credentials.username)
    if not user or not user_service.verify_password(credentials.password, user.hashed_password):
        logger.debug(f"Failed login attempt from IP: {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_verified:
        logger.info(f"Login blocked: email not verified for user {user.id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email address not confirmed",
        )

    access_token = await create_access_token({"sub": user.username})
    refresh_token = await create_refresh_token({"sub": user.username})
    await user_service.set_refresh_token(user.id, refresh_token)

    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db_session)):
    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        logger.warning(f"Verification error: invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.is_verified:
        return {"message": "Your email is already confirmed"}
    await user_service.confirmed_email(email)
    return {"message": "Email confirmed"}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if user and user.is_verified:
        return {"message": "Your email is already confirmed"}
    if user:
        from src.services.email import send_email
        background_tasks.add_task(send_email, user.email, user.username, str(request.base_url))
    return {"message": "Check your email for a confirmation link"}


@router.post("/refresh", response_model=Token)
@limiter.limit("5/minute")
async def refresh(
    request: Request,
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session),
    redis: aioredis.Redis = Depends(get_redis),
):
    username = decode_token(payload.refresh_token, expected_scope="refresh_token")

    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    if user is None or user.refresh_token != payload.refresh_token:
        logger.warning(f"Invalid refresh token attempt from IP: {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = await create_access_token({"sub": user.username})
    refresh_token = await create_refresh_token({"sub": user.username})
    await user_service.set_refresh_token(user.id, refresh_token)
    await invalidate_user_cache(username, redis)
    logger.info(f"Token refreshed for user {user.id}")

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
        logger.info(f"User logout: {user.id}")
