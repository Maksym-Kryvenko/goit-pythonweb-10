import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from main import app
from src.conf.config import config
from src.database.models import Base, User, RolesEnum
from src.database.db import get_db_session
from src.database.redis import get_redis
from src.services.auth import create_access_token, get_current_user, require_admin
from src.services.hash import Hash

_hash = Hash()
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+asyncpg://{config.POSTGRESQL_USER}:{config.POSTGRESQL_PASSWORD}"
    f"@{config.POSTGRESQL_HOST}:{config.POSTGRESQL_PORT}/test_{config.POSTGRESQL_DB}"
)

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=NullPool,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)

test_user = {
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "testuser@12345678",
}

unverified_user = {
    "username": "unverified",
    "email": "unverified@example.com",
    "password": "unverified@12345678",
}


@pytest.fixture(scope="module")
def init_models_wrap():
    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with TestingSessionLocal() as session:
            _h = Hash()
            session.add_all(
                [
                    User(
                        username=test_user["username"],
                        email=test_user["email"],
                        hashed_password=_h.get_password_hash(test_user["password"]),
                        is_verified=True,
                        avatar_url="https://twitter.com/gravatar",
                        role=RolesEnum.admin,
                    ),
                    User(
                        username=unverified_user["username"],
                        email=unverified_user["email"],
                        hashed_password=_h.get_password_hash(
                            unverified_user["password"]
                        ),
                        is_verified=False,
                    ),
                ]
            )
            await session.commit()

    asyncio.run(init_models())


@pytest.fixture(scope="module")
def client(init_models_wrap):
    # Dependency override

    async def override_get_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception as err:
                await session.rollback()
                raise

    async def override_get_current_user():
        return User(
            id=1,
            username=test_user["username"],
            email=test_user["email"],
            is_verified=True,
            role=RolesEnum.admin,
        )

    async def override_get_redis():
        mock_redis = AsyncMock()
        return mock_redis

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[require_admin] = override_get_current_user
    app.dependency_overrides[get_redis] = override_get_redis

    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def get_token():
    token = await create_access_token(data={"sub": test_user["username"]})
    return token


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def sample_user():
    return User(
        id=1,
        username="testuser",
        email="test_email@gmail.com",
        hashed_password=_hash.get_password_hash("testPAssword@12345"),
        is_verified=True,
    )
