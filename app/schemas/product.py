from pydantic import BaseModel
import uuid
from typing import Optional


class ProductImageSchema(BaseModel):
    url: str

    class Config:
        orm_mode = True

class BrandSchema(BaseModel):
    name: str

    class Config:
        orm_mode = True

class ProductFeedItemSchema(BaseModel):
    id: uuid.UUID
    name: str
    selling_price: int
    brand: BrandSchema
    primary_image: Optional[ProductImageSchema] = None

    class Config:
        orm_mode = True