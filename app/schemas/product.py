from pydantic import BaseModel, Field
import uuid
from typing import List

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
    images: List[ProductImageSchema] = Field(..., max_items=1)

    class Config:
        orm_mode = True