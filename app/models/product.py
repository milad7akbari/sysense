import uuid
import enum
from typing import List, TYPE_CHECKING
from sqlalchemy import (
    Enum, String, DateTime, Text, Boolean, Integer, Numeric, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base, variant_attributes_table

if TYPE_CHECKING:
    from .user import User, Seller


class ProductType(enum.Enum):
    NATIVE = "NATIVE"
    REFERRAL = "REFERRAL"


class Product(Base):
    __tablename__ = "products"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), mapped_column.ForeignKey("sellers.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    product_type: Mapped[ProductType] = mapped_column(Enum(ProductType), nullable=False, default=ProductType.NATIVE)
    external_url: Mapped[str | None] = mapped_column(Text)
    display_price: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now(),
                                                 server_default=func.now())

    seller: Mapped["Seller"] = relationship(back_populates="products")
    variants: Mapped[List["ProductVariant"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    liked_by_users: Mapped[List["User"]] = relationship(secondary="product_likes", back_populates="liked_products")


class Attribute(Base):
    __tablename__ = "attributes"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    values: Mapped[List["AttributeValue"]] = relationship(back_populates="attribute", cascade="all, delete-orphan")


class AttributeValue(Base):
    __tablename__ = "attribute_values"
    id: Mapped[int] = mapped_column(primary_key=True)
    attribute_id: Mapped[int] = mapped_column(mapped_column.ForeignKey("attributes.id"))
    value: Mapped[str] = mapped_column(String(100), nullable=False)
    __table_args__ = (UniqueConstraint('attribute_id', 'value', name='_attribute_value_uc'),)

    attribute: Mapped["Attribute"] = relationship(back_populates="values")


class ProductVariant(Base):
    __tablename__ = "product_variants"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), mapped_column.ForeignKey("products.id"))
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    product: Mapped["Product"] = relationship(back_populates="variants")
    attributes: Mapped[List["AttributeValue"]] = relationship(secondary=variant_attributes_table)
