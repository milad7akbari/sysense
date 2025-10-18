from sqlalchemy.ext.asyncio import AsyncSession
from app.models.interaction import ProductInteraction
from app.schemas.interaction import InteractionCreate
import uuid

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