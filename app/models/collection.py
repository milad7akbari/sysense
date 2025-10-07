import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, collection_pins_table

if TYPE_CHECKING:
    from .user import User
    from .product import Product


class Collection(Base):
    __tablename__ = "collections"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="collections")
    products: Mapped[List["Product"]] = relationship(secondary=collection_pins_table)