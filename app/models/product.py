import uuid
from typing import List, Optional

from sqlalchemy import (
    String, DateTime, Integer, UniqueConstraint, Table, Column, ForeignKey, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import Text

from app.db.base import Base

product_category_association = Table(
    'product_category_association', Base.metadata,
    Column('product_id', PG_UUID(as_uuid=True), ForeignKey('products.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)

product_attribute_association = Table(
    "product_attribute_association", Base.metadata,
    Column("product_id", PG_UUID(as_uuid=True), ForeignKey("products.id"), primary_key=True),
    Column("attribute_value_id", Integer, ForeignKey("attribute_values.id"), primary_key=True),
)


class Brand(Base):
    __tablename__ = "brands"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    products: Mapped[List["Product"]] = relationship(back_populates="brand")


class Product(Base):
    __tablename__ = "products"
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dg_product_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=True)
    dg_variant_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    selling_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"))
    seller_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sellers.id"))
    brand: Mapped["Brand"] = relationship(back_populates="products", lazy="selectin")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                 onupdate=func.now())
    images: Mapped[List["ProductImage"]] = relationship(back_populates="product", cascade="all, delete-orphan")

    @property
    def primary_image(self):
        if self.images:
            return self.images[0]
        return None

    categories: Mapped[List["Category"]] = relationship(secondary=product_category_association,
                                                        back_populates="products", lazy="selectin")
    attributes: Mapped[List["AttributeValue"]] = relationship(secondary=product_attribute_association,
                                                              back_populates="products", lazy="selectin")
    seller: Mapped["Seller"] = relationship(back_populates="products")


class ProductImage(Base):
    __tablename__ = "product_images"
    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("products.id"))
    product: Mapped["Product"] = relationship(back_populates="images", lazy="selectin")


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))
    parent: Mapped[Optional["Category"]] = relationship(back_populates="children", remote_side=[id], lazy="selectin")
    children: Mapped[List["Category"]] = relationship(back_populates="parent", lazy="selectin")
    products: Mapped[List["Product"]] = relationship(secondary=product_category_association,
                                                     back_populates="categories")
    __table_args__ = (UniqueConstraint('parent_id', 'name', name='_parent_name_uc'),)


class Attribute(Base):
    __tablename__ = "attributes"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    values: Mapped[List["AttributeValue"]] = relationship(back_populates="attribute")


class AttributeValue(Base):
    __tablename__ = "attribute_values"
    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    attribute_id: Mapped[int] = mapped_column(ForeignKey("attributes.id"))
    attribute: Mapped["Attribute"] = relationship(back_populates="values", lazy="selectin")
    products: Mapped[List["Product"]] = relationship(secondary=product_attribute_association,
                                                     back_populates="attributes", lazy="selectin")
    __table_args__ = (UniqueConstraint('attribute_id', 'value', name='_attribute_value_uc'),)
