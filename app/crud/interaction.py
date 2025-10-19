import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.models import Collection
from app.models.interaction import ProductInteraction
from app.schemas.interaction import InteractionCreate
from app.models.product import Product # Import Product model

async def create_interaction(db: AsyncSession, user_id: uuid.UUID, interaction_in: InteractionCreate) -> ProductInteraction:
    """
    Creates a new product interaction (like/dislike) for a user.
    If an interaction already exists for this user and product, it will be updated.
    """
    # Check for existing interaction
    existing_interaction = await db.get(ProductInteraction, (user_id, interaction_in.product_id))

    if existing_interaction:
        # Update the existing interaction
        existing_interaction.interaction_type = interaction_in.interaction_type
        db.add(existing_interaction)
        await db.commit()
        await db.refresh(existing_interaction)
        return existing_interaction
    else:
        # Create a new interaction
        db_interaction = ProductInteraction(
            user_id=user_id,
            product_id=interaction_in.product_id,
            interaction_type=interaction_in.interaction_type
        )
        db.add(db_interaction)
        await db.commit()
        await db.refresh(db_interaction)
        return db_interaction



async def get_interactions_by_user(db: AsyncSession, user_id: uuid.UUID) -> List[ProductInteraction]:
    """
    Retrieves all interactions for a specific user, with product details.
    """
    stmt = (
        select(ProductInteraction)
        .where(ProductInteraction.user_id == user_id)
        .options(
            selectinload(ProductInteraction.product)
            .selectinload(Product.images),
            selectinload(ProductInteraction.product)
            .selectinload(Product.brand)
        )
        .order_by(ProductInteraction.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def delete_interaction(db: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID) -> bool:
    """
    Deletes a specific interaction for a user.
    Returns True if an interaction was deleted, False otherwise.
    """
    stmt = (
        delete(ProductInteraction)
        .where(ProductInteraction.user_id == user_id, ProductInteraction.product_id == product_id)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


async def remove_product_from_collection(db: AsyncSession, collection: Collection, product_id: uuid.UUID) -> bool:
    """
    Removes a product from a collection.
    Returns True if removed, False if it was not in the collection.
    """
    product = await db.get(Product, product_id)
    if not product:
        return False  # Product not found

    if product in collection.products:
        collection.products.remove(product)
        await db.commit()
        return True

    return False