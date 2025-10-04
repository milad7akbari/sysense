import uuid
from datetime import datetime
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str
    user_id: str

class RefreshTokenBase(BaseModel):
    token: str
    user_id: uuid.UUID
    expires_at: datetime

class RefreshTokenCreate(RefreshTokenBase):
    pass
