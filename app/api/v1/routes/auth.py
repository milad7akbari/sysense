import logging
import uuid
import time
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core import security
from app.core.config import settings
import redis.asyncio as redis
from app.db.redis_session import get_redis_client
from app.db.session import get_async_db
from app.models.user import User, RefreshToken, OtpRequest
from app.schemas.token import (
    Token,
    PhoneNumberRequest,
    OTPVerification,
    UserInfo,
    RefreshTokenRequest
)
router = APIRouter(prefix="/auth", tags=["Authentication (OTP)"])
logger = logging.getLogger(__name__)

# --- Simulated Rate Limiter (in Production use Redis) ---
OTP_REQUEST_CACHE = {}
THROTTLE_TIME_SECONDS = 60  # enforced wait time between two OTP requests


def is_throttled(phone_number: str) -> bool:
    """Checks if the phone number is currently throttled by rate limiting."""
    last_request_time = OTP_REQUEST_CACHE.get(phone_number)
    if last_request_time and (time.time() - last_request_time) < THROTTLE_TIME_SECONDS:
        return True
    return False


def update_throttle_time(phone_number: str):
    """Update the last request time for OTP of a phone number."""
    OTP_REQUEST_CACHE[phone_number] = time.time()


def simulate_send_sms(phone_number: str, otp_code: str):
    """
    Simulate sending SMS (e.g., KavehNegar).
    (This should be replaced with actual API call logic.)
    """
    logger.info(f"--- [KavehNegar Simulation] ---")
    logger.info(f"OTP {otp_code} sent to {phone_number}")
    # Simulate external API call
    # requests.post("https://api.kavenegar.com/v1/...", ...)
    logger.info(f"--- [End Simulation] ---")


# --- Utility Functions ---

async def get_user_by_phone_number(db: AsyncSession, phone_number: str) -> User | None:
    query = select(User).where(User.phone_number == phone_number)
    result = await db.execute(query)
    return result.scalar_one_or_none()


# async def get_current_user(
#         db: AsyncSession = Depends(get_async_db),
#         token: str = Depends(security.oauth2_scheme)
# ) -> User:
#     """Dependency for validating Access Token and retrieving the current user."""
#     payload_data = security.decode_jwt(token)
#
#     # Check token validity, type (must be access), and subject
#     if not payload_data or payload_data.type != 'access' or not payload_data.sub:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid or expired Access Token",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#
#     user_identifier = payload_data.sub
#     user = await get_user_by_phone_number(db, user_identifier)
#
#     if user is None or not user.is_active:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="User not found or inactive",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     return user

@router.post("/send-otp", status_code=status.HTTP_202_ACCEPTED)
async def send_otp(
        request: PhoneNumberRequest,
        db: AsyncSession = Depends(get_async_db),
        redis_client: redis.Redis = Depends(get_redis_client),
        background_tasks: BackgroundTasks = None
):
    phone_number = request.phone_number

    rate_limit_key = f"otp_rate_limit:{phone_number}"

    request_count = await redis_client.incr(rate_limit_key)

    if request_count == 1:
        await redis_client.expire(rate_limit_key, THROTTLE_TIME_SECONDS)

    if request_count > 991:
        ttl = await redis_client.ttl(rate_limit_key)
        logger.warning(f"OTP request throttled for {phone_number}. Retry in {ttl}s.")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Please try again in {ttl} seconds.",
            headers={"Retry-After": str(ttl)}
        )

    plain_otp = security.generate_otp()

    otp_request_instance = OtpRequest.create(
        phone_number=phone_number,
        hashed_otp=plain_otp,
        ttl_seconds=120
    )
    db.add(otp_request_instance)
    await db.commit()
    logger.info(f"OTP request for {phone_number} stored in the database.")

    # 4. Send the PLAIN OTP in a background task
    # This prevents the API from waiting for the SMS service to respond.
    return {"message": "OTP has been sent successfully."}


async def get_valid_otp_request(db: AsyncSession, phone_number: str) -> OtpRequest | None:
    """
    Fetches the most recent, non-expired OTP request for a given phone number.
    """
    now = datetime.now(timezone.utc)
    stmt = (
        select(OtpRequest)
        .where(OtpRequest.phone_number == phone_number)
        .where(OtpRequest.expires_at > now)
        .order_by(OtpRequest.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


@router.post("/verify-otp", response_model=Token)
async def verify_otp(
        request: OTPVerification,
        db: AsyncSession = Depends(get_async_db)
):
    """
    Step 2: Validate OTP and issue Access Token and Refresh Token.
    """
    # 1. Fetch the OTP request record from the database
    otp_record = await get_valid_otp_request(db, request.phone_number)

    if not otp_record:
        logger.warning(f"No valid OTP record found for {request.phone_number}.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or OTP code."
        )

    # 2. Securely verify the OTP hash
    if not security.verify_otp(request.otp_code, otp_record.hashed_otp):
        logger.warning(f"OTP verification failed for {request.phone_number}. (Invalid Code)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or OTP code."
        )

    # 3. Retrieve the associated user
    user = await get_user_by_phone_number(db, request.phone_number)
    if not user:
        # This case is unlikely if an OTP record exists, but good for safety
        logger.error(f"OTP record exists for non-existent user: {request.phone_number}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    # 4. Generate Tokens using the immutable User ID
    user_identifier = str(user.id)
    access_token = security.create_access_token(user_identifier=user_identifier)
    refresh_token = security.create_refresh_token(user_identifier=user_identifier)

    # 5. Store the new Refresh Token
    # Assuming your RefreshToken model stores the full token
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_rt = RefreshToken(
        token=refresh_token,
        user_id=user.id,
        expires_at=expires_at
    )
    db.add(new_rt)

    # 6. Consume the OTP by deleting it
    await db.delete(otp_record)

    # 7. Commit the transaction
    await db.commit()
    logger.info(f"User {user.id} logged in via OTP. Tokens issued.")

    return Token(access_token=access_token, refresh_token=refresh_token)

# @router.post("/refresh", response_model=Token)
# async def refresh_token(
#         request: RefreshTokenRequest,
#         db: AsyncSession = Depends(get_async_db),
# ) -> Any:
#     """
#     Endpoint to obtain a new Access Token using a Refresh Token (JTI-based).
#     The old refresh token will be revoked.
#     """
#     refresh_token_str = request.refresh_token
#     payload_data = security.decode_jwt(refresh_token_str)
#
#     # 1. Validate payload (type, JTI, subject)
#     if not payload_data or payload_data.type != 'refresh' or not payload_data.jti or not payload_data.sub:
#         logger.warning("Refresh attempt failed: Invalid token structure.")
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Refresh Token")
#
#     user_identifier = payload_data.sub
#     jti = payload_data.jti
#
#     # 2. Retrieve user
#     user = await get_user_by_phone_number(db, user_identifier)
#     if not user:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
#
#     # 3. Check refresh token in DB using JTI
#     rt_query = select(RefreshToken).where(
#         RefreshToken.jti == jti,
#         RefreshToken.user_id == user.id,
#     )
#     result = await db.execute(rt_query)
#     rt_db = result.scalar_one_or_none()
#
#     now = datetime.now(timezone.utc)
#
#     if rt_db is None or rt_db.is_revoked or rt_db.expires_at < now:
#         logger.error(f"Refresh Token {jti} is invalid, revoked, or expired in DB.")
#         # Standard 401 error to force logout on client
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                             detail="Refresh token is revoked or expired. Please log in again.")
#
#     # 4. Revoke the old refresh token
#     rt_db.is_revoked = True
#     db.add(rt_db)
#     logger.info(f"Old Refresh Token {jti} for user {user.id} revoked.")
#
#     # 5. Create a new token pair and store it
#     new_access_token = security.create_access_token(user_identifier=user_identifier)
#
#     new_jti_uuid = str(uuid.uuid4())
#     new_refresh_token = security.create_refresh_token(user_identifier=user_identifier, jti=new_jti_uuid)
#
#     new_rt = RefreshToken(
#         jti=new_jti_uuid,
#         hashed_jti=security.hash_jti(new_jti_uuid),
#         user_id=user.id,
#         expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
#     )
#     db.add(new_rt)
#     await db.commit()
#     logger.info(f"New Refresh Token {new_jti_uuid} issued for user {user.id}.")
#
#     return Token(access_token=new_access_token, refresh_token=new_refresh_token)

#
# @router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
# async def logout(
#         request: RefreshTokenRequest,
#         db: AsyncSession = Depends(get_async_db)
# ):
#     """
#     Endpoint for logging out and revoking the Refresh Token (blacklisting).
#     """
#     refresh_token_str = request.refresh_token
#     payload_data = security.decode_jwt(refresh_token_str)
#
#     if not payload_data or payload_data.type != 'refresh' or not payload_data.jti:
#         logger.warning("Logout attempt with invalid token structure.")
#         return  # Always return 204 to avoid leaking information
#
#     jti = payload_data.jti
#
#     rt_query = select(RefreshToken).where(RefreshToken.jti == jti)
#     result = await db.execute(rt_query)
#     rt_db = result.scalar_one_or_none()
#
#     if rt_db and not rt_db.is_revoked:
#         rt_db.is_revoked = True
#         await db.commit()
#         logger.info(f"Refresh Token {jti} revoked on logout.")
#
#     # Response 204 (No Content)
#     return
