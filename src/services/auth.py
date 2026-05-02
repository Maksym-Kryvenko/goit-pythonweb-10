import hashlib
from datetime import datetime, timedelta, UTC
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from src.database.db import get_db_session
from src.database.models import User
from src.conf.config import config

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def _prehash(password: str) -> bytes:
    # SHA-256 reduces any password to 32 bytes so bcrypt never silently truncates
    return hashlib.sha256(password.encode()).hexdigest().encode()


class Hash:
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(_prehash(plain_password), hashed_password.encode())

    def get_password_hash(self, password: str) -> str:
        return bcrypt.hashpw(_prehash(password), bcrypt.gensalt()).decode()


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
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    from src.services.users import UserService

    username = decode_token(token, expected_scope="access_token")
    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
