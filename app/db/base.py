from sqlalchemy import Column, String, Table, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()

followers_table = Table(
    "followers", Base.metadata,
    Column("follower_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column("followed_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
)

product_likes_table = Table(
    "product_likes", Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column("product_id", UUID(as_uuid=True), ForeignKey("products.id"), primary_key=True),
)

collection_pins_table = Table(
    "collection_pins", Base.metadata,
    Column("collection_id", UUID(as_uuid=True), ForeignKey("collections.id"), primary_key=True),
    Column("product_id", UUID(as_uuid=True), ForeignKey("products.id"), primary_key=True),
)

variant_attributes_table = Table(
    "variant_attributes", Base.metadata,
    Column("variant_id", UUID(as_uuid=True), ForeignKey("product_variants.id"), primary_key=True),
    # Corrected column name from 'value_id' to match usage
    Column("attribute_value_id", Integer, ForeignKey("attribute_values.id"), primary_key=True),
)