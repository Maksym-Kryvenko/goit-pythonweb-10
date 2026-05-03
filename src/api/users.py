import logging
import redis.asyncio as aioredis
from fastapi import APIRouter, HTTPException, Depends, status, Request, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.limiter import limiter
from src.database.db import get_db_session
from src.database.models import User
from src.database.redis import get_redis
from src.schemas.users import UserResponse
from src.services.users import UserService
from src.services.auth import get_current_user, invalidate_user_cache

router = APIRouter(prefix="/api/users", tags=["users"])
logger = logging.getLogger(__name__)

@router.get(
    "/me",
    response_model=UserResponse
)
@limiter.limit("10/minute")
async def get_my_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.patch(
    "/avatar",
    response_model=UserResponse
)
@limiter.limit("5/minute")
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    redis: aioredis.Redis = Depends(get_redis),
):
    service = UserService(db)
    updated = await service.upload_avatar(current_user, file)
    if not updated:
        logger.warning(f"User not found: {current_user.username}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await invalidate_user_cache(current_user.username, redis)
    return updated
