from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.contacts import ContactRepository
from src.schemas import ContactCreate, ContactUpdate, ContactResponse


class ContactService:
    def __init__(self, db: AsyncSession):
        self.repository = ContactRepository(db)

    async def get_contacts(
        self,
        skip: int = 0,
        limit: int = 50,
        q: str | None = None,
        upcoming_birthdays: bool = False,
    ) -> list[ContactResponse]:
        birthday_range = None
        if upcoming_birthdays:
            today = date.today()
            birthday_range = (today, today + timedelta(days=7))

        return await self.repository.get_contacts(
            skip=skip, limit=limit, q=q, birthday_range=birthday_range
        )

    async def get_contact(self, contact_id: int) -> ContactResponse | None:
        return await self.repository.get_contact(contact_id)

    async def create_contact(self, contact_data: ContactCreate) -> ContactResponse:
        return await self.repository.create_contact(contact_data)

    async def update_contact(self, contact_id: int, contact_data: ContactUpdate) -> ContactResponse | None:
        return await self.repository.update_contact(contact_id, contact_data)

    async def delete_contact(self, contact_id: int) -> bool:
        return await self.repository.delete_contact(contact_id)
