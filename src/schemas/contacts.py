from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
import re

PHONE_PATTERN = re.compile(r"^\+?\d{7,15}$")


def validate_phone(value: Optional[str]) -> Optional[str]:
    """Validate that a phone number matches the expected format.

    Args:
        value: Phone number string, or ``None`` to skip validation.

    Raises:
        ValueError: If the value is not ``None`` and does not match ``PHONE_PATTERN``.

    Returns:
        The original value unchanged if valid.
    """
    if value is not None and not PHONE_PATTERN.match(value):
        raise ValueError(
            "Invalid phone number format. Must contain only digits and may start with '+'."
        )
    return value


def validate_birthday(value: Optional[date]) -> Optional[date]:
    """Validate that a birthday date is not in the future.

    Args:
        value: Date of birth, or ``None`` to skip validation.

    Raises:
        ValueError: If the date is after today.

    Returns:
        The original value unchanged if valid.
    """
    if value is not None and value > date.today():
        raise ValueError("Birthday cannot be in the future.")
    return value


class ContactBase(BaseModel):
    """Shared fields and validators for contact creation and update schemas."""

    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthday: date
    additional_data: str | None = None

    @field_validator("phone_number")
    @classmethod
    def check_phone(cls, v: str) -> str:
        """Validate phone_number using :func:`validate_phone`."""
        return validate_phone(v)

    @field_validator("birthday")
    @classmethod
    def check_birthday(cls, v: date) -> date:
        """Validate birthday using :func:`validate_birthday`."""
        return validate_birthday(v)

    @field_validator("email")
    @classmethod
    def check_email(cls, v: EmailStr) -> EmailStr:
        """Pass-through validator; Pydantic's EmailStr already validates the format."""
        return v


class ContactCreate(ContactBase):
    """Schema for creating a new contact — all fields required."""


class ContactUpdate(BaseModel):
    """Schema for partially updating an existing contact — all fields optional."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    birthday: Optional[date] = None
    additional_data: Optional[str] = None

    @field_validator("phone_number")
    @classmethod
    def check_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone_number using :func:`validate_phone`."""
        return validate_phone(v)

    @field_validator("birthday")
    @classmethod
    def check_birthday(cls, v: Optional[date]) -> Optional[date]:
        """Validate birthday using :func:`validate_birthday`."""
        return validate_birthday(v)


class ContactResponse(ContactBase):
    """Response schema for a contact, including the database-assigned ``id``."""

    id: int

    model_config = ConfigDict(from_attributes=True)
