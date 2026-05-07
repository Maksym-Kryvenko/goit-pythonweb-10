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
from src.database.models import User, RolesEnum
from src.database.redis import get_redis
from src.conf.config import config
from src.services.hash import Hash
from src.services.users import UserService

logger = logging.getLogger(__name__)
http_bearer = HTTPBearer()


def _create_token(data: dict, expires_delta: int, token_type: str) -> str:
    """Encode a JWT with an expiry timestamp and a scope claim.

    Args:
        data: Payload claims to include (e.g. ``{"sub": username}``).
        expires_delta: Lifetime in seconds from now.
        token_type: Value for the ``scope`` claim (e.g. ``"access_token"``).

    Returns:
        Signed JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(seconds=expires_delta)
    to_encode.update({"exp": expire, "scope": token_type})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)


async def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:
    """Create a short-lived JWT access token.

    Args:
        data: Claims to encode (must include ``sub``).
        expires_delta: Custom lifetime in seconds; defaults to config value.

    Returns:
        Signed access token string.
    """
    return _create_token(
        data,
        expires_delta or config.ACCESS_TOKEN_EXPIRE_SECONDS,
        token_type="access_token",
    )


async def create_refresh_token(data: dict, expires_delta: Optional[int] = None) -> str:
    """Create a long-lived JWT refresh token.

    Args:
        data: Claims to encode (must include ``sub``).
        expires_delta: Custom lifetime in seconds; defaults to config value.

    Returns:
        Signed refresh token string.
    """
    return _create_token(
        data,
        expires_delta or config.REFRESH_TOKEN_EXPIRE_SECONDS,
        token_type="refresh_token",
    )


def decode_token(token: str, expected_scope: str) -> str:
    """Verify a JWT signature and scope, returning the ``sub`` claim.

    Args:
        token: Encoded JWT string.
        expected_scope: Required value of the ``scope`` claim.

    Raises:
        HTTPException: 401 if the token is invalid, expired, or has wrong scope.

    Returns:
        Username extracted from the ``sub`` claim.
    """
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
    """Create a 7-day JWT used for email verification links.

    Args:
        data: Claims to encode (must include ``sub`` with the email).

    Returns:
        Signed email verification token.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(UTC), "exp": expire})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)


async def get_email_from_token(token: str) -> str:
    """Decode an email-verification JWT and return the embedded email address.

    Args:
        token: Signed email verification token.

    Raises:
        HTTPException: 422 if the token is invalid or expired.

    Returns:
        Email address stored in the ``sub`` claim.
    """
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
    """Return the Redis key used to cache a user object.

    Args:
        username: The user's login name.

    Returns:
        A namespaced key string, e.g. ``"user:john"``.
    """
    return f"user:{username}"


def _user_to_json(user: User) -> str:
    """Serialise a User ORM instance to a JSON string for Redis storage.

    Args:
        user: The ORM user object to serialise.

    Returns:
        JSON string containing all cacheable user fields.
    """
    return json.dumps(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "hashed_password": user.hashed_password,
            "avatar_url": user.avatar_url,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "refresh_token": user.refresh_token,
            "role": user.role.value if user.role else RolesEnum.user.value,
        }
    )


def _user_from_json(data: str) -> User:
    """Deserialise a JSON string from Redis back into a User ORM instance.

    Args:
        data: JSON string previously produced by :func:`_user_to_json`.

    Returns:
        A :class:`~src.database.models.User` instance populated from the cached data.
    """
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
    user.role = RolesEnum(payload.get("role", RolesEnum.user.value))
    return user


async def invalidate_user_cache(username: str, redis: aioredis.Redis) -> None:
    """Remove a user's cached profile from Redis.

    Args:
        username: The username whose cache entry should be deleted.
        redis: Active Redis connection.
    """
    await redis.delete(_user_cache_key(username))


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: AsyncSession = Depends(get_db_session),
    redis: aioredis.Redis = Depends(get_redis),
) -> User:
    """FastAPI dependency that resolves and returns the authenticated user.

    Checks Redis cache first; falls back to the database and then caches the result.

    Args:
        request: Incoming HTTP request (used to read the Authorization header).
        credentials: Bearer token extracted by HTTPBearer.
        db: Async database session.
        redis: Redis connection for user caching.

    Raises:
        HTTPException: 401 if the token is missing, invalid, or the user does not exist.

    Returns:
        Authenticated User ORM instance.
    """

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logging.warning("Could not validate credentials.")
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

    await redis.set(
        _user_cache_key(username), _user_to_json(user), ex=config.USER_CACHE_TTL
    )
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """FastAPI dependency that enforces admin-only access.

    Args:
        current_user: Resolved by :func:`get_current_user`.

    Raises:
        HTTPException: 403 if the user does not have the ``admin`` role.

    Returns:
        The authenticated admin User instance.
    """
    if current_user.role != RolesEnum.admin:
        logging.info("It is not an admin user.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not sufficient access role.",
        )
    return current_user


async def create_password_reset_token(email: str) -> str:
    """Create a short-lived (15 min) JWT for password reset confirmation.

    Args:
        email: The email address of the user requesting a reset.

    Returns:
        Signed password-reset token string.
    """
    return _create_token(
        data={"sub": email},
        expires_delta=900,
        token_type="password_reset",
    )


async def verify_password_reset_token(token: str) -> str:
    """Validate a password-reset JWT and return the email address it contains.

    Args:
        token: Signed password-reset token from the email link.

    Raises:
        HTTPException: 401 if the token is invalid, expired, or has wrong scope.

    Returns:
        Email address extracted from the token's ``sub`` claim.
    """
    email = decode_token(token, expected_scope="password_reset")
    return email
