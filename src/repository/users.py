from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas.users import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def create_user(
        self,
        user_data: UserCreate,
        hashed_password: str,
        avatar_url: str | None = None,
    ) -> User:
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
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def update_user(self, user_id: int, user_data: UserUpdate) -> User | None:
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        for field, value in user_data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)

        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def set_refresh_token(self, user_id: int, refresh_token: str | None) -> bool:
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        user.refresh_token = refresh_token
        await self.db.flush()
        return True

    async def set_verified(self, user_id: int, verified: bool = True) -> bool:
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        user.is_verified = verified
        await self.db.flush()
        return True

    async def update_password(self, user_id: int, hashed_password: str) -> bool:
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        user.hashed_password = hashed_password
        await self.db.flush()
        return True

    async def update_avatar_url(self, user_id: int, avatar_url: str) -> User | None:
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        user.avatar_url = avatar_url
        await self.db.flush()
        await self.db.refresh(user)
        return user
