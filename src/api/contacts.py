from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db_session
from src.schemas import ContactCreate, ContactUpdate, ContactResponse
from src.services.contacts import ContactService

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


@router.get("/", response_model=List[ContactResponse])
async def get_contacts(
    skip: int = 0,
    limit: int = 50,
    q: str | None = None,
    upcoming_birthdays: bool = False,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get contacts. Supports:
    - `q` — search by first name, last name or email
    - `upcoming_birthdays=true` — contacts with birthdays in the next 7 days
    """
    service = ContactService(db)
    return await service.get_contacts(skip=skip, limit=limit, q=q, upcoming_birthdays=upcoming_birthdays)


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    service = ContactService(db)
    contact = await service.get_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact: ContactCreate,
    db: AsyncSession = Depends(get_db_session),
):
    service = ContactService(db)
    return await service.create_contact(contact)


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    contact: ContactUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    service = ContactService(db)
    updated = await service.update_contact(contact_id, contact)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return updated


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    service = ContactService(db)
    deleted = await service.delete_contact(contact_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
