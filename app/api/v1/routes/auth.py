import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Response
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.core import security
from app.core.config import settings
from app.db.redis_session import get_redis_client
from app.db.session import get_async_db
from app.crud import user as user_crud
from app.schemas.token import Token, PhoneNumberRequest, OTPVerification, RefreshTokenRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)

THROTTLE_TIME_SECONDS = 60


@router.post("/send-otp", status_code=status.HTTP_202_ACCEPTED)
async def send_otp(
        request: PhoneNumberRequest,
        db: AsyncSession = Depends(get_async_db),
        redis_client: redis.Redis = Depends(get_redis_client),
):
    phone_number = request.phone_number
    rate_limit_key = f"otp_rate_limit:{phone_number}"

    # Rate Limiting
    request_count = await redis_client.incr(rate_limit_key)
    if request_count == 1:
        await redis_client.expire(rate_limit_key, THROTTLE_TIME_SECONDS)
    if request_count > 5:  # A more realistic limit
        ttl = await redis_client.ttl(rate_limit_key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Please try again in {ttl} seconds.",
            headers={"Retry-After": str(ttl)}
        )

    # Logic
    plain_otp = security.generate_otp()
    hashed_otp = security.hash_otp(plain_otp)
    await user_crud.create_otp_request(db, phone_number, hashed_otp)
    await db.commit()

    return {"message": "OTP has been sent successfully.", "code": plain_otp}


@router.post("/verify-otp", response_model=Token)
async def verify_otp(request: OTPVerification, db: AsyncSession = Depends(get_async_db)):
    otp_record = await user_crud.get_valid_otp(db, request.phone_number)
    if not otp_record or not security.verify_otp(request.otp_code, otp_record.hashed_otp):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired OTP code.")

    user = await user_crud.get_user_by_phone(db, request.phone_number)
    if not user:
        user = await user_crud.create_user(db, request.phone_number)

    # Token Generation
    new_jti = str(uuid.uuid4())
    user_identifier = str(user.id)
    access_token = security.create_access_token(user_identifier=user_identifier)
    refresh_token = security.create_refresh_token(user_identifier=user_identifier, jti=new_jti)

    # Store Refresh Token
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    await user_crud.create_refresh_token(db, user.id, security.hash_jti(new_jti), expires_at)

    otp_record.mark_as_used()
    await db.commit()
    logger.info(f"User {user.id} logged in. Tokens issued with JTI {new_jti}.")

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest, db: AsyncSession = Depends(get_async_db)):
    payload = security.decode_token(request.refresh_token)
    if not payload or payload.type != 'refresh':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Refresh Token")

    user = await user_crud.get_user_by_id(db, payload.sub)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    hashed_jti = security.hash_jti(payload.jti)
    rt_db = await user_crud.get_refresh_token_by_jti(db, hashed_jti, user.id)

    now = datetime.now(timezone.utc)
    if not rt_db or rt_db.is_revoked or rt_db.expires_at < now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Refresh token has expired or been revoked.")

    # Token Rotation
    rt_db.is_revoked = True

    new_jti = str(uuid.uuid4())
    user_identifier = str(user.id)
    new_access_token = security.create_access_token(user_identifier=user_identifier)
    new_refresh_token = security.create_refresh_token(user_identifier=user_identifier, jti=new_jti)

    expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    await user_crud.create_refresh_token(db, user.id, security.hash_jti(new_jti), expires_at)

    await db.commit()
    logger.info(f"Refreshed token for user {user.id}. Old JTI: {payload.jti}, New JTI: {new_jti}.")

    return Token(access_token=new_access_token, refresh_token=new_refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: RefreshTokenRequest, db: AsyncSession = Depends(get_async_db)):
    payload = security.decode_token(request.refresh_token)
    if not payload or payload.type != 'refresh':
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    user = await user_crud.get_user_by_id(db, payload.sub)
    if not user:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    hashed_jti = security.hash_jti(payload.jti)
    rt_db = await user_crud.get_refresh_token_by_jti(db, hashed_jti, user.id)

    if rt_db and not rt_db.is_revoked:
        rt_db.is_revoked = True
        await db.commit()
        logger.info(f"Refresh Token with JTI {payload.jti} has been revoked on logout.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)