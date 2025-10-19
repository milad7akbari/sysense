import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.interaction import InteractionCreate, InteractionRead, InteractionWithProduct
from app.crud import interaction as interaction_crud
from app.crud import collection as collection_crud

router = APIRouter(prefix="/me/interactions", tags=["Interactions"])

@router.post("", response_model=InteractionRead, status_code=status.HTTP_201_CREATED)
async def record_interaction(
    interaction_in: InteractionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Records a user's interaction (like or dislike) with a product.
    If an interaction for this product already exists, it will be updated.
    """
    interaction = await interaction_crud.create_interaction(db, user_id=current_user.id, interaction_in=interaction_in)
    return interaction



@router.get("", response_model=List[InteractionWithProduct])
async def get_my_interactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieves a list of the current user's likes and dislikes.
    """
    interactions = await interaction_crud.get_interactions_by_user(db, user_id=current_user.id)
    return interactions

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_interaction(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Deletes a user's interaction (like or dislike) for a specific product.
    """
    deleted = await interaction_crud.delete_interaction(db, user_id=current_user.id, product_id=product_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/favorites/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_product_from_favorites(
        product_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    Removes a product from the user's default 'Favorites' list.
    """
    favorites_collection = await collection_crud.get_or_create_favorites_collection(db, user_id=current_user.id)

    removed = await collection_crud.remove_product_from_collection(db, collection=favorites_collection,
                                                                   product_id=product_id)

    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found in favorites.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)