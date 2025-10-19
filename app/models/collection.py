import uuid
from typing import List, TYPE_CHECKING
import sqlalchemy as sa
from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.schema import Table, Column, Index

from app.db.base import Base

if TYPE_CHECKING:
    from .user import User
    from .product import Product


collection_pins_table = Table(
    "collection_pins", Base.metadata,
    Column("collection_id", UUID(as_uuid=True), ForeignKey("collections.id"), primary_key=True),
    Column("product_id", UUID(as_uuid=True), ForeignKey("products.id"), primary_key=True),
)

class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_default_favorites: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    user: Mapped["User"] = relationship(back_populates="collections")
    products: Mapped[List["Product"]] = relationship(secondary=collection_pins_table)
    ble_args__ = (
        Index(
            '_user_default_favorites_uc',
            'user_id',
            unique=True,
            postgresql_where=sa.text('is_default_favorites = true')
        ),
    )