from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from src.database.models import RolesEnum


class Token(BaseModel):
    """Response schema returned after successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    """Request body for the login endpoint."""

    username: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)

    model_config = {
        "json_schema_extra": {
            "example": {"username": "user@example.com", "password": "password123"}
        }
    }


class RefreshTokenRequest(BaseModel):
    """Request body carrying the refresh token used to obtain new access tokens."""

    refresh_token: str


class UserCreate(BaseModel):
    """Request body for registering a new user account."""

    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Public user profile returned by user-facing endpoints."""

    id: int
    username: str
    email: EmailStr
    avatar_url: Optional[str] = None
    is_verified: bool = False
    created_at: Optional[datetime] = None
    role: RolesEnum = RolesEnum.user

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """Internal schema representing login credentials."""

    username: str
    password: str


class RequestEmail(BaseModel):
    """Request body used for email-only operations such as re-sending a verification link."""

    email: EmailStr


class UserUpdate(BaseModel):
    """Schema for partially updating a user's profile — all fields optional."""

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    refresh_token: Optional[str] = None
    avatar_url: Optional[str] = None


class PasswordReset(BaseModel):
    """Request body for confirming a password reset with a signed token."""

    token: str
    new_password: str
