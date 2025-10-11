import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Set, TYPE_CHECKING
from sqlalchemy import (
    String, DateTime, Text, Boolean, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.schema import Table, Column
from sqlalchemy.sql.sqltypes import Integer

from ..db.base import Base

if TYPE_CHECKING:
    from .product import Product
    from .collection import Collection

class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(50), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    full_name: Mapped[str | None] = mapped_column(String(100))
    bio: Mapped[str | None] = mapped_column(Text)
    profile_picture_url: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), server_default=func.now()
    )

    seller_profile: Mapped["Seller | None"] = relationship(back_populates="user", cascade="all, delete-orphan")
    collections: Mapped[List["Collection"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class OtpRequest(Base):
    __tablename__ = "otp_requests"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(length=15), index=True, nullable=False)
    hashed_otp = Column(String(length=255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)  # Flag if OTP already used
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def is_expired(self) -> bool:
        """Return True if OTP is expired or already used"""
        return self.used or datetime.now(timezone.utc) > self.expires_at

    def mark_as_used(self):
        """Mark OTP as used to prevent reuse"""
        self.used = True

    @classmethod
    def create(cls, phone_number: str, hashed_otp: str, ttl_seconds: int = 300) -> "OtpRequest":
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        return cls(phone_number=phone_number, hashed_otp=hashed_otp, expires_at=expires_at)


class Seller(Base):
    __tablename__ = "sellers"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    bio: Mapped[str | None] = mapped_column(Text)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="seller_profile")
    products: Mapped[List["Product"]] = relationship(back_populates="seller", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    hashed_jti: Mapped[str] = mapped_column(String, index=True, nullable=False, unique=True)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")