from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.contacts import ContactRepository
from src.schemas.contacts import ContactCreate, ContactUpdate, ContactResponse
from src.schemas.users import UserResponse


class ContactService:
    """Business logic layer for contact operations."""

    def __init__(self, db: AsyncSession, current_user: UserResponse):
        """
        Args:
            db: Active async SQLAlchemy session.
            current_user: The authenticated user making the request.
        """
        self.repository = ContactRepository(db, current_user)

    async def get_contacts(
        self,
        skip: int = 0,
        limit: int = 50,
        q: str | None = None,
        upcoming_birthdays: bool = False,
    ) -> list[ContactResponse]:
        """Return contacts with optional search and birthday-window filtering.

        Args:
            skip: Pagination offset.
            limit: Maximum records to return.
            q: Optional full-text search query (name or email).
            upcoming_birthdays: When True, restricts to contacts whose birthday falls within the next 7 days.

        Returns:
            List of matching ContactResponse objects.
        """
        birthday_range = None
        if upcoming_birthdays:
            today = date.today()
            birthday_range = (today, today + timedelta(days=7))

        return await self.repository.get_contacts(
            skip=skip, limit=limit, q=q, birthday_range=birthday_range
        )

    async def get_contact(self, contact_id: int) -> ContactResponse | None:
        """Retrieve a single contact by ID for the current user.

        Args:
            contact_id: Primary key of the contact.

        Returns:
            ContactResponse or None if not found.
        """
        return await self.repository.get_contact(contact_id)

    async def create_contact(self, contact_data: ContactCreate) -> ContactResponse:
        """Create and persist a new contact for the current user.

        Args:
            contact_data: Validated contact fields.

        Returns:
            The created ContactResponse.
        """
        return await self.repository.create_contact(contact_data)

    async def update_contact(
        self, contact_id: int, contact_data: ContactUpdate
    ) -> ContactResponse | None:
        """Apply partial updates to a contact.

        Args:
            contact_id: Primary key of the contact to update.
            contact_data: Fields to update.

        Returns:
            Updated ContactResponse or None if not found.
        """
        return await self.repository.update_contact(contact_id, contact_data)

    async def delete_contact(self, contact_id: int) -> bool:
        """Delete a contact by ID.

        Args:
            contact_id: Primary key of the contact to delete.

        Returns:
            True if deleted, False if not found.
        """
        return await self.repository.delete_contact(contact_id)
