import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, RefreshToken, OtpRequest

async def get_user_by_phone(db: AsyncSession, phone_number: str) -> Optional[User]:
    """Fetches a user by their phone number."""
    stmt = select(User).where(User.phone_number == phone_number)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    """Fetches a user by their UUID."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, phone_number: str) -> User:
    """Creates a new user with the given phone number."""
    new_user = User(phone_number=phone_number)
    db.add(new_user)
    await db.flush()  # Use flush to get the ID before committing
    return new_user

# --- OTP Request CRUD ---

async def create_otp_request(db: AsyncSession, phone_number: str, hashed_otp: str) -> OtpRequest:
    """Creates and stores a new OTP request."""
    otp_instance = OtpRequest.create(phone_number=phone_number, hashed_otp=hashed_otp)
    db.add(otp_instance)
    return otp_instance

async def get_valid_otp(db: AsyncSession, phone_number: str) -> Optional[OtpRequest]:
    """Gets the latest, valid, and unused OTP for a phone number."""
    now = datetime.now(timezone.utc)
    stmt = (
        select(OtpRequest)
        .where(
            OtpRequest.phone_number == phone_number,
            OtpRequest.expires_at > now,
            OtpRequest.used == False
        )
        .order_by(OtpRequest.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalars().first()

# --- Refresh Token CRUD ---

async def create_refresh_token(db: AsyncSession, user_id: uuid.UUID, hashed_jti: str, expires_at: datetime) -> RefreshToken:
    """Creates and stores a new refresh token."""
    new_rt = RefreshToken(user_id=user_id, hashed_jti=hashed_jti, expires_at=expires_at)
    db.add(new_rt)
    return new_rt

async def get_refresh_token_by_jti(db: AsyncSession, hashed_jti: str, user_id: uuid.UUID) -> Optional[RefreshToken]:
    """Fetches a refresh token by its hashed JTI for a specific user."""
    stmt = select(RefreshToken).where(
        RefreshToken.hashed_jti == hashed_jti,
        RefreshToken.user_id == user_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()