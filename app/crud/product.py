from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import typing as t
from app.models import Product

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
