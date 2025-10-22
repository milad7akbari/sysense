import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import typing as t

from sqlalchemy.sql.expression import distinct
from sqlalchemy.sql.functions import func

from app.models import Product, Seller, AttributeValue, ProductInteraction, User
from app.models.collection import collection_pins_table
from app.models.product import product_category_association


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


async def get_personalized_feed_for_user(db: AsyncSession, user: User, limit: int = 20) -> t.List[Product]:
    """
    Simulates an AI recommendation engine to generate a personalized feed for a logged-in user.
    """
    # 1. Find all products the user has already interacted with (liked, disliked, or saved)
    interacted_stmt = select(ProductInteraction.product_id).where(ProductInteraction.user_id == user.id)
    saved_stmt = select(collection_pins_table.c.product_id).join(User.collections).where(User.id == user.id)

    interacted_ids = (await db.execute(interacted_stmt)).scalars().all()
    saved_ids = (await db.execute(saved_stmt)).scalars().all()
    excluded_product_ids = set(interacted_ids + saved_ids)

    # 2. Get the "taste profile" (favorite brands and categories) from liked and saved items
    liked_stmt = select(ProductInteraction.product_id).where(ProductInteraction.user_id == user.id,
                                                             ProductInteraction.interaction_type == 'like')
    liked_ids = (await db.execute(liked_stmt)).scalars().all()
    taste_profile_ids = set(saved_ids + liked_ids)

    if not taste_profile_ids:
        # If user has no interactions, return the guest feed but exclude seen items
        return await get_guest_feed_products(db, limit)

    # 3. Extract brand and category IDs from the taste profile products
    taste_brands_stmt = select(distinct(Product.brand_id)).where(Product.id.in_(taste_profile_ids))
    taste_categories_stmt = select(distinct(product_category_association.c.category_id)).where(
        product_category_association.c.product_id.in_(taste_profile_ids))

    brand_ids = (await db.execute(taste_brands_stmt)).scalars().all()
    category_ids = (await db.execute(taste_categories_stmt)).scalars().all()

    # 4. Find new, unseen products that match the user's taste profile
    recommendation_stmt = (
        select(Product)
        .join(product_category_association)
        .where(
            Product.id.notin_(excluded_product_ids),
            (Product.brand_id.in_(brand_ids) | product_category_association.c.category_id.in_(category_ids))
        )
        .order_by(func.random())  # Use random order to simulate discovery
        .limit(limit)
        .options(
            selectinload(Product.images),
            selectinload(Product.brand)
        )
    )

    result = await db.scalars(recommendation_stmt)
    recommended_products = result.unique().all()

    # Fallback: If no recommendations found, return some random unseen items
    if not recommended_products:
        fallback_stmt = (
            select(Product)
            .where(Product.id.notin_(excluded_product_ids))
            .order_by(func.random())
            .limit(limit)
            .options(selectinload(Product.images), selectinload(Product.brand))
        )
        result = await db.scalars(fallback_stmt)
        return result.unique().all()

    return recommended_products
