import hashlib
import secrets
import string
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from jose import jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings

pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

class TokenPayload(BaseModel):
    sub: str
    exp: datetime
    type: str
    jti: str

def decode_token(token: str) -> TokenPayload | None:
    try:
        payload_dict = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayload(**payload_dict)
    except jwt.ExpiredSignatureError as e:
        print(e)
        return None
    except (jwt.JWTError, Exception) as e:
        print(e)
        return None

def generate_otp(length: int = 1) -> str:
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


def create_access_token(user_identifier: str, jti: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": user_identifier,
        "type": "access",
        "jti": jti,
        "exp": expire,
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/verify-otp")

def create_refresh_token(user_identifier: str, jti: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": user_identifier,
        "exp": expire,
        "type": "refresh",
        "jti": jti,
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

def hash_jti(jti: str) -> str:
    return hashlib.sha256(jti.encode()).hexdigest()

