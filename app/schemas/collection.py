import uuid
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

from .user import UserMinimal

class CollectionBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    is_public: bool = True

class CollectionCreate(CollectionBase):
    pass

class CollectionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    is_public: Optional[bool] = None

class CollectionRead(CollectionBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user: UserMinimal
