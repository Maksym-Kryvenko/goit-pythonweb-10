import logging
from typing import Optional

import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError
from fastapi import UploadFile
from libgravatar import Gravatar
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import config
from src.database.models import User
from src.repository.users import UserRepository
from src.schemas.users import UserCreate
from src.services.hash import Hash

logger = logging.getLogger(__name__)
_hash = Hash()


class UserService:
    """Business logic layer for user account operations."""

    def __init__(self, db: AsyncSession):
        """
        Args:
            db: Active async SQLAlchemy session.
        """
        self.db = db
        self.user_repository = UserRepository(db)

    def hash_password(self, password: str) -> str:
        """Return a bcrypt hash of the given plain-text password.

        Args:
            password: Plain-text password to hash.

        Returns:
            Hashed password string.
        """
        return _hash.get_password_hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Check whether a plain-text password matches its stored hash.

        Args:
            plain_password: Password supplied by the user.
            hashed_password: Hash retrieved from the database.

        Returns:
            True if the password matches, False otherwise.
        """
        return _hash.verify_password(plain_password, hashed_password)

    async def create_user(self, user_data: UserCreate) -> User:
        """Register a new user, fetching a Gravatar avatar as the default.

        Args:
            user_data: Validated registration payload.

        Returns:
            Newly created User ORM instance.
        """
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
        """Retrieve a user by username.

        Args:
            username: The username to look up.

        Returns:
            User instance or None.
        """
        return await self.user_repository.get_user_by_username(username)

    async def get_user_by_email(self, email: str) -> User | None:
        """Retrieve a user by email address.

        Args:
            email: The email address to look up.

        Returns:
            User instance or None.
        """
        return await self.user_repository.get_user_by_email(email)

    async def set_refresh_token(self, user_id: int, refresh_token: str | None) -> bool:
        """Store or clear the user's refresh token.

        Args:
            user_id: Target user's database ID.
            refresh_token: Token to store, or None to log out.

        Returns:
            True on success, False if the user was not found.
        """
        return await self.user_repository.set_refresh_token(user_id, refresh_token)

    async def confirmed_email(self, email: str) -> None:
        """Mark a user's email as verified.

        Args:
            email: The email address to confirm.
        """
        user = await self.user_repository.get_user_by_email(email)
        if user:
            await self.user_repository.set_verified(user.id, True)

    async def update_password(self, user_id: int, hashed_password: str) -> bool:
        """Update the stored password hash for a user.

        Args:
            user_id: Target user's database ID.
            hashed_password: New bcrypt hash.

        Returns:
            True on success, False if the user was not found.
        """
        return await self.user_repository.update_password(user_id, hashed_password)

    async def upload_avatar(self, user: User, file: UploadFile) -> User | None:
        """Upload an image to Cloudinary and update the user's avatar URL.

        Args:
            user: The user whose avatar is being updated.
            file: Image file received from the multipart request.

        Raises:
            RuntimeError: If Cloudinary credentials are not configured.
            HTTPException: 400 on Cloudinary API error, 500 on unexpected failure.

        Returns:
            Updated User instance with the new avatar URL, or None.
        """
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
        try:
            upload_result = cloudinary.uploader.upload(
                file.file, public_id=public_id, overwrite=True
            )
            avatar_url = cloudinary.CloudinaryImage(public_id).build_url(
                width=250, height=250, crop="fill", version=upload_result.get("version")
            )
            return await self.user_repository.update_avatar_url(user.id, avatar_url)
        except CloudinaryError as e:
            logger.error(f"Cloudinary API error: {e}")
            raise HTTPException(status_code=400, detail="Avatar upload failed")
        except Exception as e:
            logger.error(f"Unexpected error during avatar upload: {e}")
            raise HTTPException(status_code=500, detail="Server error")
