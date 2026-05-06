from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from src.database.models import RolesEnum


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "user@example.com",
                "password": "password123"
            }
        }
    }

class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    avatar_url: Optional[str] = None
    is_verified: bool = False
    created_at: Optional[datetime] = None
    role: RolesEnum = RolesEnum.user

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    username: str
    password: str


class RequestEmail(BaseModel):
    email: EmailStr


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    refresh_token: Optional[str] = None
    avatar_url: Optional[str] = None

class PasswordReset(BaseModel):
    token: str
    new_password: str
    