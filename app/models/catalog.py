from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DECIMAL, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base

class Brand(Base):
    __tablename__ = 'sys_brands'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    logo_url = Column(String(255))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    products = relationship("Product", back_populates="brand")

class Vendor(Base):
    __tablename__ = 'sys_vendors'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    base_url = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    products = relationship("Product", back_populates="vendor")

class Tag(Base):
    __tablename__ = 'sys_tags'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)

class ProductTag(Base):
    __tablename__ = 'sys_product_tags'
    product_id = Column(Integer, ForeignKey('sys_products.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('sys_tags.id'), primary_key=True)

class Product(Base):
    __tablename__ = 'sys_products'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    brand_id = Column(Integer, ForeignKey('sys_brands.id'))
    vendor_id = Column(Integer, ForeignKey('sys_vendors.id'))
    base_price = Column(DECIMAL(10, 2))
    gender = Column(String(50))
    source_url = Column(String(1024), unique=True)
    source_product_code = Column(String(100))
    is_active = Column(Boolean, default=True)
    specifications = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    brand = relationship("Brand", back_populates="products")
    vendor = relationship("Vendor", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="sys_product_tags")

class ProductImage(Base):
    __tablename__ = 'sys_product_images'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('sys_products.id'), nullable=False)
    image_url = Column(String(1024), nullable=False)
    display_order = Column(Integer, default=0)
    product = relationship("Product", back_populates="images")
