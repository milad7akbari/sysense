import secrets
import string
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# This should be defined once in your application, using Argon2 as recommended
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

ALGORITHM = "HS256"



def generate_otp(length: int = 6) -> str:
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def hash_otp(otp: str) -> str:
    return pwd_context.hash(otp)


def verify_otp(plain_otp: str, hashed_otp: str) -> bool:
    """Verifies a plain-text OTP against a hashed version."""
    return pwd_context.verify(plain_otp, hashed_otp)


# --- Password Specific Functions (Unchanged) ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hashed version."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hashes a plain-text password."""
    return pwd_context.hash(password)


# --- JWT Token Functions (Updated) ---

def create_access_token(user_identifier: str) -> str:
    """
    Creates a new Access Token.
    Args:
        user_identifier: The subject of the token (e.g., user ID).
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": user_identifier,
        "exp": expire,
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_identifier: str) -> str:
    """
    Creates a new Refresh Token with a unique JTI.
    Args:
        user_identifier: The subject of the token (e.g., user ID).
    """
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": user_identifier,
        "exp": expire,
        "jti": str(uuid.uuid4()),  # JWT ID for revocation
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Dict[str, Any] | None:
    """
    Decodes a JWT token.
    Returns the payload dictionary on success, None on failure.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.JWTError:
        return None