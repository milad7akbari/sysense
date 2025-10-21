import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import typing as t
from app.models import Product, Seller, AttributeValue


async def get_guest_feed_products(db: AsyncSession, limit: int = 20) -> t.List[Product]:
    stmt = (
        select(Product)
        .join(Product.categories)
        .order_by(Product.created_at.desc())
        .limit(limit)
        .options(
            selectinload(Product.images),
            selectinload(Product.brand)
        )
    )

    result = await db.scalars(stmt)
    products = result.unique().all()
    return products



async def get_product_by_id(db: AsyncSession, product_id: uuid.UUID) -> t.Optional[Product]:
    """
    Fetches a single product by its ID with all related details for the product page.
    This query is optimized to load all necessary data in a single database trip.
    """
    stmt = (
        select(Product)
        .where(Product.id == product_id)
        .options(
            # Eagerly load all images for the product
            selectinload(Product.images),
            # Eagerly load the brand information
            selectinload(Product.brand),
            # Eagerly load the seller's user profile
            selectinload(Product.seller).selectinload(Seller.user),
            # Eagerly load the attributes and their corresponding names
            selectinload(Product.attributes).selectinload(AttributeValue.attribute)
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
