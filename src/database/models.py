import enum
from datetime import date
from sqlalchemy import Integer, String, Date, Boolean, func, ForeignKey, Enum
from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""


class RolesEnum(enum.Enum):
    """User role options controlling access permissions."""

    user = "user"
    admin = "admin"


class Contact(Base):
    """ORM model for a contact record owned by a user."""

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    birthday: Mapped[date] = mapped_column(Date, nullable=False)
    additional_data: Mapped[str] = mapped_column(String(255), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    owner: Mapped["User"] = relationship("User", back_populates="contacts")


class User(Base):
    """ORM model for an application user with authentication and role fields."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[date] = mapped_column(
        Date, server_default=func.now(), nullable=False
    )
    refresh_token: Mapped[str] = mapped_column(String(500), nullable=True)
    contacts: Mapped[list[Contact]] = relationship("Contact", back_populates="owner")
    role: Mapped[RolesEnum] = mapped_column(
        Enum(RolesEnum), default=RolesEnum.user, nullable=False
    )
