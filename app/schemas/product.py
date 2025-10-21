from pydantic import BaseModel, HttpUrl, field_validator
import uuid
from typing import Optional, List

from app.schemas.user import UserMinimal


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


class AttributeSchema(BaseModel):
    name: str
    class Config:
        orm_mode = True

class AttributeValueDetailSchema(BaseModel):
    value: str
    attribute: AttributeSchema
    class Config:
        orm_mode = True

class ProductDetailSchema(BaseModel):
    id: uuid.UUID
    name: str
    selling_price: int
    brand: BrandSchema
    images: List[ProductImageSchema] = []
    seller: UserMinimal
    attributes: List[AttributeValueDetailSchema] = []
    referral_url: Optional[HttpUrl] = None

    @field_validator('referral_url', mode='before')
    def generate_referral_url(cls, v, values, **kwargs):
        if 'dg_product_id' in values and values['dg_product_id']:
            return f"https://www.example-store.com/product/{values['dg_product_id']}"
        return None

    class Config:
        orm_mode = True