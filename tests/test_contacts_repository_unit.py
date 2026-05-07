import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock

from src.database.models import Contact, User
from src.repository.contacts import ContactRepository
from src.schemas.contacts import ContactCreate, ContactUpdate


@pytest.fixture
def contact_repository(mock_session, sample_user):
    return ContactRepository(mock_session, sample_user)


@pytest.fixture
def sample_contact():
    return Contact(
        id=1,
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone_number="+380991112233",
        birthday=date(1990, 5, 5),
        user_id=1,
    )


@pytest.mark.asyncio
async def test_get_contacts(contact_repository, mock_session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        Contact(
            id=1,
            first_name="test name",
            last_name="test surname",
            email="test_email@gmail.com",
            phone_number="+380991112233",
            birthday=date(2005, 5, 5),
            user_id=1,
        )
    ]
    mock_session.execute = AsyncMock(return_value=mock_result)

    contacts = await contact_repository.get_contacts(skip=0, limit=10)

    assert len(contacts) == 1
    assert contacts[0].first_name == "test name"


@pytest.mark.asyncio
async def test_get_contacts_empty(contact_repository, mock_session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)

    contacts = await contact_repository.get_contacts()

    assert contacts == []


@pytest.mark.asyncio
async def test_get_contact_found(contact_repository, mock_session, sample_contact):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contact_repository.get_contact(1)

    assert result is not None
    assert result.id == 1
    assert result.first_name == "John"


@pytest.mark.asyncio
async def test_get_contact_not_found(contact_repository, mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contact_repository.get_contact(999)

    assert result is None


@pytest.mark.asyncio
async def test_create_contact(contact_repository, mock_session):
    contact_data = ContactCreate(
        first_name="Jane",
        last_name="Smith",
        email="jane@example.com",
        phone_number="+380991112244",
        birthday=date(1995, 3, 15),
    )

    async def set_id(obj):
        obj.id = 2

    mock_session.refresh = AsyncMock(side_effect=set_id)

    result = await contact_repository.create_contact(contact_data)

    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once()
    assert result.first_name == "Jane"
    assert result.email == "jane@example.com"


@pytest.mark.asyncio
async def test_update_contact_found(contact_repository, mock_session, sample_contact):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_contact
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.refresh = AsyncMock()

    update_data = ContactUpdate(first_name="Updated")
    result = await contact_repository.update_contact(1, update_data)

    assert result is not None
    assert result.first_name == "Updated"
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_update_contact_not_found(contact_repository, mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    update_data = ContactUpdate(first_name="Updated")
    result = await contact_repository.update_contact(999, update_data)

    assert result is None
    mock_session.flush.assert_not_called()


@pytest.mark.asyncio
async def test_delete_contact_found(contact_repository, mock_session, sample_contact):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_contact
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.delete = AsyncMock()

    result = await contact_repository.delete_contact(1)

    assert result is True
    mock_session.delete.assert_called_once_with(sample_contact)
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_delete_contact_not_found(contact_repository, mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.delete = AsyncMock()

    result = await contact_repository.delete_contact(999)

    assert result is False
    mock_session.delete.assert_not_called()
