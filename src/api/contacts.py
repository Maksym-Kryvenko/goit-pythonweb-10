from typing import List
import logging

from fastapi import APIRouter, HTTPException, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.limiter import limiter
from src.database.db import get_db_session
from src.database.models import User
from src.schemas.contacts import ContactCreate, ContactUpdate, ContactResponse
from src.services.contacts import ContactService
from src.services.auth import get_current_user

router = APIRouter(prefix="/api/contacts", tags=["contacts"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[ContactResponse])
@limiter.limit("10/minute")
async def get_contacts(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    q: str | None = None,
    upcoming_birthdays: bool = False,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Return a paginated list of the authenticated user's contacts.

    Supports optional full-text search (``q``) and a 7-day birthday window filter.
    """
    service = ContactService(db, current_user)
    return await service.get_contacts(
        skip=skip, limit=limit, q=q, upcoming_birthdays=upcoming_birthdays
    )


@router.get("/{contact_id}", response_model=ContactResponse)
@limiter.limit("10/minute")
async def get_contact(
    request: Request,
    contact_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Fetch a single contact by ID. Returns 404 if not found or not owned by the user."""
    service = ContactService(db, current_user)
    contact = await service.get_contact(contact_id)
    if not contact:
        logger.info(
            f"Contact {contact_id} not found for {current_user.username} while reading."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_contact(
    request: Request,
    contact: ContactCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new contact linked to the authenticated user. Returns 201 on success."""
    service = ContactService(db, current_user)
    return await service.create_contact(contact)


@router.patch("/{contact_id}", response_model=ContactResponse)
@limiter.limit("10/minute")
async def update_contact(
    request: Request,
    contact_id: int,
    contact: ContactUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Apply partial updates to an existing contact. Returns 404 if not found."""
    service = ContactService(db, current_user)
    updated = await service.update_contact(contact_id, contact)
    if not updated:
        logger.info(
            f"Contact {contact_id} not found for {current_user.username} while patching."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return updated


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_contact(
    request: Request,
    contact_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a contact by ID. Returns 204 on success, 404 if not found."""
    service = ContactService(db, current_user)
    deleted = await service.delete_contact(contact_id)
    if not deleted:
        logger.info(
            f"Contact {contact_id} not found for {current_user.username} while deleting."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
