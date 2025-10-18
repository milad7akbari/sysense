import uuid
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.base import Base
from .user import User
from .product import Product
from enum import Enum

class InteractionType(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"

class ProductInteraction(Base):
    __tablename__ = "product_interactions"

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True)
    product_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), sa.ForeignKey("products.id"), primary_key=True)
    interaction_type: Mapped[InteractionType] = mapped_column(sa.Enum(InteractionType), nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship()
    product: Mapped["Product"] = relationship()

    __table_args__ = (
        sa.UniqueConstraint('user_id', 'product_id', name='_user_product_uc'),
    )