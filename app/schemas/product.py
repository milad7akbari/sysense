import uuid
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl, ConfigDict

from .user import SellerMinimal
from app.models.product import ProductType

class AttributeValueBase(BaseModel):
    value: str = Field(..., min_length=1, max_length=100)

class AttributeValueRead(AttributeValueBase):
    model_config = ConfigDict(from_attributes=True)
    id: int

class AttributeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class AttributeRead(AttributeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    values: List[AttributeValueRead] = []

class ProductVariantBase(BaseModel):
    price: float = Field(..., gt=0)
    stock_quantity: int = Field(..., ge=0)
    sku: Optional[str] = Field(None, max_length=100)
    is_active: bool = True

class ProductVariantCreate(ProductVariantBase):
    attribute_value_ids: List[int]

class ProductVariantRead(ProductVariantBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    attributes: List[AttributeValueRead] = []

class ProductBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    product_type: ProductType = ProductType.NATIVE
    external_url: Optional[HttpUrl] = None
    display_price: Optional[str] = Field(None, max_length=100)
    is_active: bool = True

class ProductCreate(ProductBase):
    variants: List[ProductVariantCreate] = Field(..., min_length=1)

class ProductUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    seller: SellerMinimal
    variants: List[ProductVariantRead] = []
