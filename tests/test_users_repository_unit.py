import pytest
from unittest.mock import AsyncMock, MagicMock

from src.database.models import User, RolesEnum
from src.repository.users import UserRepository
from src.schemas.users import UserCreate, UserUpdate


@pytest.fixture
def user_repository(mock_session):
    return UserRepository(mock_session)


@pytest.mark.asyncio
async def test_get_user_by_username_found(user_repository, mock_session, sample_user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.get_user_by_username("testuser")

    assert result is not None
    assert result.username == "testuser"


@pytest.mark.asyncio
async def test_get_user_by_username_not_found(user_repository, mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.get_user_by_username("nobody")

    assert result is None


@pytest.mark.asyncio
async def test_get_user_by_email_found(user_repository, mock_session, sample_user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.get_user_by_email("test_email@gmail.com")

    assert result is not None
    assert result.email == "test_email@gmail.com"


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(user_repository, mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.get_user_by_email("nobody@example.com")

    assert result is None


@pytest.mark.asyncio
async def test_get_user_by_id_found(user_repository, mock_session, sample_user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.get_user_by_id(1)

    assert result is not None
    assert result.id == 1


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(user_repository, mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.get_user_by_id(999)

    assert result is None


@pytest.mark.asyncio
async def test_create_user(user_repository, mock_session):
    user_data = UserCreate(username="newuser", email="new@example.com", password="secret123")

    async def set_id(obj):
        obj.id = 1

    mock_session.refresh = AsyncMock(side_effect=set_id)

    result = await user_repository.create_user(user_data, "hashed_secret", "http://avatar.url/1.png")

    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once()
    assert result.username == "newuser"
    assert result.email == "new@example.com"
    assert result.hashed_password == "hashed_secret"
    assert result.avatar_url == "http://avatar.url/1.png"


@pytest.mark.asyncio
async def test_update_user_found(user_repository, mock_session, sample_user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_user
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.refresh = AsyncMock()

    update_data = UserUpdate(username="updated_user")
    result = await user_repository.update_user(1, update_data)

    assert result is not None
    assert result.username == "updated_user"
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_not_found(user_repository, mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    update_data = UserUpdate(username="updated_user")
    result = await user_repository.update_user(999, update_data)

    assert result is None
    mock_session.flush.assert_not_called()


@pytest.mark.asyncio
async def test_set_refresh_token_found(user_repository, mock_session, sample_user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.set_refresh_token(1, "new_token")

    assert result is True
    assert sample_user.refresh_token == "new_token"
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_set_refresh_token_not_found(user_repository, mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.set_refresh_token(999, "new_token")

    assert result is False
    mock_session.flush.assert_not_called()


@pytest.mark.asyncio
async def test_set_verified_found(user_repository, mock_session, sample_user):
    sample_user.is_verified = False
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.set_verified(1)

    assert result is True
    assert sample_user.is_verified is True
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_set_verified_not_found(user_repository, mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.set_verified(999)

    assert result is False
    mock_session.flush.assert_not_called()


@pytest.mark.asyncio
async def test_update_password_found(user_repository, mock_session, sample_user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.update_password(1, "new_hashed_pw")

    assert result is True
    assert sample_user.hashed_password == "new_hashed_pw"
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_update_password_not_found(user_repository, mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.update_password(999, "new_hashed_pw")

    assert result is False
    mock_session.flush.assert_not_called()


@pytest.mark.asyncio
async def test_update_avatar_url_found(user_repository, mock_session, sample_user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_user
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.refresh = AsyncMock()

    result = await user_repository.update_avatar_url(1, "http://new-avatar.url/1.png")

    assert result is not None
    assert result.avatar_url == "http://new-avatar.url/1.png"
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_update_avatar_url_not_found(user_repository, mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.update_avatar_url(999, "http://new-avatar.url/1.png")

    assert result is None
