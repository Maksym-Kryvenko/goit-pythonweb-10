from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
import re

PHONE_PATTERN = re.compile(r"^\+?\d{7,15}$")


def validate_phone(value: Optional[str]) -> Optional[str]:
    if value is not None and not PHONE_PATTERN.match(value):
        raise ValueError("Invalid phone number format. Must contain only digits and may start with '+'.")
    return value


def validate_birthday(value: Optional[date]) -> Optional[date]:
    if value is not None and value > date.today():
        raise ValueError("Birthday cannot be in the future.")
    return value


class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthday: date
    additional_data: str | None = None

    @field_validator("phone_number")
    @classmethod
    def check_phone(cls, v: str) -> str:
        return validate_phone(v)

    @field_validator("birthday")
    @classmethod
    def check_birthday(cls, v: date) -> date:
        return validate_birthday(v)
    
    @field_validator("email")
    @classmethod
    def check_email(cls, v: EmailStr) -> EmailStr:
        return v


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    birthday: Optional[date] = None
    additional_data: Optional[str] = None

    @field_validator("phone_number")
    @classmethod
    def check_phone(cls, v: Optional[str]) -> Optional[str]:
        return validate_phone(v)

    @field_validator("birthday")
    @classmethod
    def check_birthday(cls, v: Optional[date]) -> Optional[date]:
        return validate_birthday(v)


class ContactResponse(ContactBase):
    id: int

    model_config = ConfigDict(from_attributes=True)