import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.db import session
from app.models import user as user_model
from app.schemas import token as token_schema
from app.schemas import user as user_schema

# تنظیمات لاگ‌گیری
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


def get_user_by_email(db: Session, email: str) -> user_model.User:
    """
    تابع کمکی برای گرفتن کاربر بر اساس ایمیل
    """
    return db.query(user_model.User).filter(user_model.User.email == email).first()


@router.post("/login", response_model=token_schema.Token)
def login(
        response: Response,
        db: Session = Depends(session.get_db),
        form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    Endpoint برای ورود کاربر و دریافت توکن‌ها.
    از شماره موبایل یا ایمیل به عنوان username استفاده می‌شود.
    """
    user = get_user_by_email(db, email=form_data.username)

    if not user or not security.verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Login attempt failed for email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # ایجاد توکن‌ها
    access_token = security.create_access_token(data={"sub": user.email})
    refresh_token = security.create_refresh_token(data={"sub": user.email})

    # ذخیره رفرش توکن در دیتابیس
    expire_date = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db_refresh_token = user_model.RefreshToken(
        token=refresh_token,
        user_id=user.id,
        expires_at=expire_date
    )
    db.add(db_refresh_token)
    db.commit()
    db.refresh(db_refresh_token)

    logger.info(f"User {user.email} logged in successfully.")

    # می‌توان توکن‌ها را در کوکی هم ست کرد، اما برای سازگاری با Flutter، در JSON برمی‌گردانیم
    # response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    # response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=token_schema.Token)
def refresh_token(
        refresh_token_data: token_schema.RefreshTokenCreate,
        db: Session = Depends(session.get_db),
) -> Any:
    """
    Endpoint برای دریافت Access Token جدید با استفاده از Refresh Token.
    """
    token = refresh_token_data.refresh_token
    payload = security.decode_token(token)

    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    email = payload["sub"]
    user = get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # بررسی اعتبار رفرش توکن در دیتابیس
    db_token = db.query(user_model.RefreshToken).filter(
        user_model.RefreshToken.token == token,
        user_model.RefreshToken.user_id == user.id,
        user_model.RefreshToken.is_revoked == False,
        user_model.RefreshToken.expires_at > datetime.now(timezone.utc)
    ).first()

    if not db_token:
        raise HTTPException(status_code=401, detail="Refresh token is invalid or expired")

    # ایجاد اکسس توکن جدید
    new_access_token = security.create_access_token(data={"sub": user.email})

    return {
        "access_token": new_access_token,
        "refresh_token": token,  # رفرش توکن فعلی همچنان معتبر است
        "token_type": "bearer",
    }


@router.post("/logout")
def logout(
        refresh_token_data: token_schema.RefreshTokenCreate,
        db: Session = Depends(session.get_db),
):
    """
    Endpoint برای خروج کاربر و باطل کردن Refresh Token.
    """
    token = refresh_token_data.refresh_token
    db_token = db.query(user_model.RefreshToken).filter(user_model.RefreshToken.token == token).first()

    if db_token:
        db_token.is_revoked = True
        db.commit()
        logger.info(f"User with token {token[:10]}... logged out.")
        return {"message": "Successfully logged out"}

    raise HTTPException(status_code=404, detail="Refresh token not found")


# Dependency برای گرفتن کاربر فعلی از روی Access Token
async def get_current_active_user(
        token: str = Depends(security.oauth2_scheme), db: Session = Depends(session.get_db)
) -> user_model.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = security.decode_token(token)
    if payload is None or "sub" not in payload:
        raise credentials_exception

    email = payload.get("sub")
    if email is None:
        raise credentials_exception

    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


@router.get("/me", response_model=user_schema.User)
def read_users_me(current_user: user_model.User = Depends(get_current_active_user)):
    """
    Endpoint محافظت شده برای دریافت اطلاعات کاربر فعلی.
    """
    return current_user
