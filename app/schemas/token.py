from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
import re


class TokenPayload(BaseModel):
    """ساختار Payload داخلی JWT: شامل Subject (شماره موبایل)، JTI برای رفرش و نوع توکن."""
    sub: Optional[str] = None  # Subject: معمولاً شماره موبایل است
    jti: Optional[str] = None  # JWT ID: برای Refresh Token الزامی است
    type: str  # نوع توکن: 'access' یا 'refresh'


class Token(BaseModel):
    """شمای پاسخ برای بازگرداندن Access Token و Refresh Token."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PhoneNumberRequest(BaseModel):
    phone_number: str = Field(..., description="شماره موبایل کاربر")
    @field_validator('phone_number')
    def validate_phone_number(cls, v):
        if not re.match(r'^09\d{9}$', v):
            raise ValueError('شماره موبایل نامعتبر است.')
        return v


class OTPVerification(BaseModel):
    phone_number: str
    otp_code: str = Field(..., min_length=1, max_length=6, description="کد OTP دریافتی (معمولاً 4 تا 6 رقمی)")


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserInfo(BaseModel):
    """شمای اطلاعات کاربری برای endpoint /me."""
    id: int
    phone_number: str
    is_superuser: bool

    # CORRECTED: Replaced inner Config class with model_config
    model_config = ConfigDict(
        from_attributes=True,  # فعال کردن از attributes برای سازگاری با مدل SQLAlchemy
    )