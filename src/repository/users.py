from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas.users import UserCreate, UserUpdate


class UserRepository:
    """Handles all database operations for user accounts."""

    def __init__(self, session: AsyncSession):
        """
        Args:
            session: Active async SQLAlchemy session.
        """
        self.db = session

    async def create_user(
        self,
        user_data: UserCreate,
        hashed_password: str,
        avatar_url: str | None = None,
    ) -> User:
        """Persist a new user record and return it.

        Args:
            user_data: Validated registration data (username, email).
            hashed_password: Bcrypt-hashed password string.
            avatar_url: Optional initial avatar URL (e.g. from Gravatar).

        Returns:
            The newly created User ORM instance.
        """
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            avatar_url=avatar_url,
        )
        self.db.add(new_user)
        await self.db.flush()
        await self.db.refresh(new_user)
        return new_user

    async def get_user_by_username(self, username: str) -> User | None:
        """Look up a user by their unique username.

        Args:
            username: The username to search for.

        Returns:
            User instance or None if not found.
        """
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """Look up a user by their unique email address.

        Args:
            email: The email address to search for.

        Returns:
            User instance or None if not found.
        """
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> User | None:
        """Fetch a user by their primary key.

        Args:
            user_id: The user's database ID.

        Returns:
            User instance or None if not found.
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def update_user(self, user_id: int, user_data: UserUpdate) -> User | None:
        """Apply partial field updates to an existing user.

        Args:
            user_id: The user's database ID.
            user_data: Fields to update (only explicitly set fields are applied).

        Returns:
            Updated User instance, or None if the user does not exist.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        for field, value in user_data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)

        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def set_refresh_token(self, user_id: int, refresh_token: str | None) -> bool:
        """Store or clear the user's refresh token.

        Args:
            user_id: The user's database ID.
            refresh_token: New token value, or None to invalidate the session.

        Returns:
            True on success, False if the user does not exist.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        user.refresh_token = refresh_token
        await self.db.flush()
        return True

    async def set_verified(self, user_id: int, verified: bool = True) -> bool:
        """Set the email verification status for a user.

        Args:
            user_id: The user's database ID.
            verified: Verification flag value (default True).

        Returns:
            True on success, False if the user does not exist.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        user.is_verified = verified
        await self.db.flush()
        return True

    async def update_password(self, user_id: int, hashed_password: str) -> bool:
        """Replace the user's stored hashed password.

        Args:
            user_id: The user's database ID.
            hashed_password: New bcrypt hash to store.

        Returns:
            True on success, False if the user does not exist.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        user.hashed_password = hashed_password
        await self.db.flush()
        return True

    async def update_avatar_url(self, user_id: int, avatar_url: str) -> User | None:
        """Update the user's avatar URL.

        Args:
            user_id: The user's database ID.
            avatar_url: New publicly accessible avatar URL.

        Returns:
            Updated User instance, or None if the user does not exist.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        user.avatar_url = avatar_url
        await self.db.flush()
        await self.db.refresh(user)
        return user
