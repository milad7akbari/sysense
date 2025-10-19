import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.product import ProductFeedItemSchema
from app.crud import collection as collection_crud

# All routes in this file start with /me
router = APIRouter(prefix="/me", tags=["Profile & Collections"])


@router.post("/favorites/{product_id}", status_code=status.HTTP_201_CREATED, summary="Add a product to favorites")
async def add_product_to_favorites(
        product_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    Adds the specified product to the user's default "Favorites" list.
    """
    favorites_collection = await collection_crud.get_or_create_favorites_collection(db, user_id=current_user.id)

    added = await collection_crud.add_product_to_collection(db, collection=favorites_collection, product_id=product_id)

    if not added:
        # This case might occur if the product doesn't exist or is already in the list.
        # For simplicity, we return a success message in both cases.
        # A more precise implementation could return a 404 error if the product doesn't exist.
        return {"message": "Product is already in favorites."}

    return {"message": "Product added to favorites successfully."}


@router.get("/favorites", response_model=List[ProductFeedItemSchema], summary="Get user's favorite products")
async def get_my_favorites(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieves the list of all products in the user's "Favorites" collection.
    """
    favorites_collection = await collection_crud.get_or_create_favorites_collection(db, user_id=current_user.id)
    products = await collection_crud.get_products_in_collection(db, collection_id=favorites_collection.id)
    return products


@router.delete("/favorites/{product_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Remove a product from favorites")
async def remove_product_from_favorites(
        product_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    Removes the specified product from the user's "Favorites" list.
    """
    favorites_collection = await collection_crud.get_or_create_favorites_collection(db, user_id=current_user.id)

    removed = await collection_crud.remove_product_from_collection(db, collection=favorites_collection,
                                                                   product_id=product_id)

    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found in favorites.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
