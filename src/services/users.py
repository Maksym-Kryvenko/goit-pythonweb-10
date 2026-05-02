import logging
from typing import Optional

import cloudinary
import cloudinary.uploader
from fastapi import UploadFile
from libgravatar import Gravatar
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import config
from src.database.models import User
from src.repository.users import UserRepository
from src.schemas.users import UserCreate
from src.services.auth import Hash

logger = logging.getLogger(__name__)
_hash = Hash()


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repository = UserRepository(db)

    def hash_password(self, password: str) -> str:
        return _hash.get_password_hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return _hash.verify_password(plain_password, hashed_password)

    async def create_user(self, user_data: UserCreate) -> User:
        avatar_url: Optional[str] = None
        try:
            avatar_url = Gravatar(user_data.email).get_image()
        except Exception as exc:
            logger.warning("Gravatar lookup failed: %s", exc)

        hashed = self.hash_password(user_data.password)
        return await self.user_repository.create_user(
            user_data, hashed_password=hashed, avatar_url=avatar_url
        )

    async def get_user_by_username(self, username: str) -> User | None:
        return await self.user_repository.get_user_by_username(username)

    async def get_user_by_email(self, email: str) -> User | None:
        return await self.user_repository.get_user_by_email(email)

    async def set_refresh_token(self, user_id: int, refresh_token: str | None) -> bool:
        return await self.user_repository.set_refresh_token(user_id, refresh_token)

    async def confirmed_email(self, email: str) -> None:
        user = await self.user_repository.get_user_by_email(email)
        if user:
            await self.user_repository.set_verified(user.id, True)

    async def upload_avatar(self, user: User, file: UploadFile) -> User | None:
        if not (
            config.CLOUDINARY_CLOUD_NAME
            and config.CLOUDINARY_API_KEY
            and config.CLOUDINARY_API_SECRET
        ):
            raise RuntimeError("Cloudinary is not configured")

        cloudinary.config(
            cloud_name=config.CLOUDINARY_CLOUD_NAME,
            api_key=config.CLOUDINARY_API_KEY,
            api_secret=config.CLOUDINARY_API_SECRET,
            secure=True,
        )

        public_id = f"contacts_app/avatars/{user.username}"
        upload_result = cloudinary.uploader.upload(
            file.file, public_id=public_id, overwrite=True
        )
        avatar_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=upload_result.get("version")
        )
        return await self.user_repository.update_avatar_url(user.id, avatar_url)
