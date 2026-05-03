import json
import logging
from datetime import datetime, timedelta, date, UTC
from typing import Optional

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from src.database.db import get_db_session
from src.database.models import User
from src.database.redis import get_redis
from src.conf.config import config
from src.services.hash import Hash
from src.services.users import UserService

logger = logging.getLogger(__name__)
http_bearer = HTTPBearer()


def _create_token(data: dict, expires_delta: int, token_type: str) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(seconds=expires_delta)
    to_encode.update({"exp": expire, "scope": token_type})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)


async def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:
    return _create_token(
        data,
        expires_delta or config.ACCESS_TOKEN_EXPIRE_SECONDS,
        token_type="access_token",
    )


async def create_refresh_token(data: dict, expires_delta: Optional[int] = None) -> str:
    return _create_token(
        data,
        expires_delta or config.REFRESH_TOKEN_EXPIRE_SECONDS,
        token_type="refresh_token",
    )


def decode_token(token: str, expected_scope: str) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username = payload.get("sub")
        scope = payload.get("scope")
        if username is None or scope != expected_scope:
            logger.warning(f"Could not validate credentials for username: {username}.")
            raise credentials_exception
        return username
    except JWTError:
        logger.warning(f"Could not validate credentials.")
        raise credentials_exception


def create_email_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(UTC), "exp": expire})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)


async def get_email_from_token(token: str) -> str:
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        email = payload["sub"]
        return email
    except JWTError:
        logger.warning("Invalid token for email verification.")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid token for email verification",
        )


def _user_cache_key(username: str) -> str:
    return f"user:{username}"


def _user_to_json(user: User) -> str:
    return json.dumps({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "hashed_password": user.hashed_password,
        "avatar_url": user.avatar_url,
        "is_verified": user.is_verified,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "refresh_token": user.refresh_token,
    })


def _user_from_json(data: str) -> User:
    payload = json.loads(data)
    user = User()
    user.id = payload["id"]
    user.username = payload["username"]
    user.email = payload["email"]
    user.hashed_password = payload["hashed_password"]
    user.avatar_url = payload.get("avatar_url")
    user.is_verified = payload["is_verified"]
    created_at = payload.get("created_at")
    user.created_at = date.fromisoformat(created_at) if created_at else None
    user.refresh_token = payload.get("refresh_token")
    return user


async def invalidate_user_cache(username: str, redis: aioredis.Redis) -> None:
    await redis.delete(_user_cache_key(username))


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: AsyncSession = Depends(get_db_session),
    redis: aioredis.Redis = Depends(get_redis),
) -> User:

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    username = decode_token(token, expected_scope="access_token")

    cached = await redis.get(_user_cache_key(username))
    if cached:
        return _user_from_json(cached)

    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    if user is None:
        logging.warning("Could not validate credentials.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    await redis.set(_user_cache_key(username), _user_to_json(user), ex=config.USER_CACHE_TTL)
    return user
