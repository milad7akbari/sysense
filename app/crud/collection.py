import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.collection import Collection
from app.models.product import Product


async def get_or_create_favorites_collection(db: AsyncSession, user_id: uuid.UUID) -> Collection:
    """
    Retrieves the default 'Favorites' collection for a user using the is_default_favorites flag,
    creating it if it doesn't exist.
    """
    # Query using the new, more robust flag
    stmt = select(Collection).where(
        Collection.user_id == user_id,
        Collection.is_default_favorites == True
    )
    result = await db.execute(stmt)
    favorites_collection = result.scalar_one_or_none()

    if not favorites_collection:
        # Create the default collection with the flag set to True
        favorites_collection = Collection(
            user_id=user_id,
            name="علاقه‌مندی‌ها",  # This name is for display purposes
            is_public=False,
            is_default_favorites=True  # The key change is here
        )
        db.add(favorites_collection)
        await db.commit()
        await db.refresh(favorites_collection)

    return favorites_collection


async def add_product_to_collection(db: AsyncSession, collection: Collection, product_id: uuid.UUID) -> bool:
    """
    Adds a product to a collection if it's not already there.
    Returns True if added, False if it was already present or product not found.
    """
    product = await db.get(Product, product_id)
    if not product:
        return False

    # Eagerly load the products relationship if not already loaded to avoid extra queries.
    if 'products' not in collection.__dict__:
        await db.refresh(collection, attribute_names=['products'])

    if product not in collection.products:
        collection.products.append(product)
        await db.commit()
        return True

    return False


async def remove_product_from_collection(db: AsyncSession, collection: Collection, product_id: uuid.UUID) -> bool:
    """
    Removes a product from a collection.
    Returns True if removed, False if it was not in the collection or product not found.
    """
    product = await db.get(Product, product_id)
    if not product:
        return False

    if 'products' not in collection.__dict__:
        await db.refresh(collection, attribute_names=['products'])

    if product in collection.products:
        collection.products.remove(product)
        await db.commit()
        return True

    return False


async def get_products_in_collection(db: AsyncSession, collection_id: uuid.UUID) -> List[Product]:
    """
    Retrieves all products within a specific collection, optimized with eager loading.
    """
    stmt = (
        select(Collection)
        .where(Collection.id == collection_id)
        .options(
            selectinload(Collection.products)
            .selectinload(Product.images),
            selectinload(Collection.products)
            .selectinload(Product.brand)
        )
    )
    result = await db.execute(stmt)
    collection = result.scalar_one_or_none()
    return collection.products if collection else []
