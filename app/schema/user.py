import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl, ConfigDict

class UserMinimal(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    username: Optional[str] = None
    profile_picture_url: Optional[HttpUrl] = None

class SellerMinimal(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    brand_name: str

class RefreshTokenBase(BaseModel):
    token: str
    user_id: uuid.UUID
    expires_at: datetime

class RefreshTokenCreate(RefreshTokenBase):
    pass

class RefreshTokenRead(RefreshTokenBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    is_revoked: bool

class SellerBase(BaseModel):
    brand_name: str = Field(..., min_length=2, max_length=100)
    bio: Optional[str] = None

class SellerCreate(SellerBase):
    pass

class SellerUpdate(BaseModel):
    brand_name: Optional[str] = Field(None, min_length=2, max_length=100)
    bio: Optional[str] = None

class SellerRead(SellerBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    is_verified: bool

class UserBase(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = None
    profile_picture_url: Optional[HttpUrl] = None

class UserCreate(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$", description="E.164 format")

class UserUpdate(UserBase):
    pass

class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    phone_number: str
    created_at: datetime
    seller_profile: Optional[SellerRead] = None
