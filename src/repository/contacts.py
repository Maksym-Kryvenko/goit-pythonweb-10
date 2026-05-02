from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy import select, or_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.schemas.contacts import ContactCreate, ContactUpdate, ContactResponse


class ContactRepository:
    def __init__(self, session: AsyncSession, current_user: User):
        self.db = session
        self.current_user = current_user

    async def get_contacts(
        self,
        skip: int = 0,
        limit: int = 50,
        q: str | None = None,
        birthday_range: Optional[Tuple[date, date]] = None,
    ) -> List[ContactResponse]:
        stmt = select(Contact).where(Contact.user_id == self.current_user.id)

        if q:
            stmt = stmt.where(
                or_(
                    Contact.first_name.ilike(f"%{q}%"),
                    Contact.last_name.ilike(f"%{q}%"),
                    Contact.email.ilike(f"%{q}%"),
                )
            )

        if birthday_range:
            today, end_date = birthday_range
            # Compare only month and day to ignore birth year
            if today.month == end_date.month:
                stmt = stmt.where(
                    extract("month", Contact.birthday) == today.month,
                    extract("day", Contact.birthday) >= today.day,
                    extract("day", Contact.birthday) <= end_date.day,
                )
            else:
                # Window spans two months (e.g. Apr 28 → May 5)
                stmt = stmt.where(
                    or_(
                        (extract("month", Contact.birthday) == today.month) &
                        (extract("day", Contact.birthday) >= today.day),
                        (extract("month", Contact.birthday) == end_date.month) &
                        (extract("day", Contact.birthday) <= end_date.day),
                    )
                )

        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        contacts = result.scalars().all()
        return [ContactResponse.model_validate(contact) for contact in contacts]

    async def get_contact(self, contact_id: int) -> ContactResponse | None:
        result = await self.db.execute(select(Contact).where(
            Contact.id == contact_id, 
            Contact.user_id == self.current_user.id,
            ))
        contact = result.scalar_one_or_none()
        return ContactResponse.model_validate(contact) if contact else None

    async def create_contact(self, contact_data: ContactCreate) -> ContactResponse:
        new_contact = Contact(**contact_data.model_dump(), user_id=self.current_user.id)
        self.db.add(new_contact)
        await self.db.flush()
        await self.db.refresh(new_contact)
        return ContactResponse.model_validate(new_contact)

    async def update_contact(self, contact_id: int, contact_data: ContactUpdate) -> ContactResponse | None:
        result = await self.db.execute(select(Contact).where(
            Contact.id == contact_id, 
            Contact.user_id == self.current_user.id,
            ))
        contact = result.scalar_one_or_none()
        if not contact:
            return None
        for key, value in contact_data.model_dump(exclude_unset=True).items():
            setattr(contact, key, value)
        await self.db.flush()
        await self.db.refresh(contact)
        return ContactResponse.model_validate(contact)

    async def delete_contact(self, contact_id: int) -> bool:
        result = await self.db.execute(select(Contact).where(
            Contact.id == contact_id, 
            Contact.user_id == self.current_user.id,
            ))
        contact = result.scalar_one_or_none()
        if not contact:
            return False
        await self.db.delete(contact)
        await self.db.flush()
        return True
