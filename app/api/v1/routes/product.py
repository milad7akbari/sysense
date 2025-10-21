import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db
from app.schemas.product import ProductFeedItemSchema, ProductDetailSchema
from app.crud import product as product_crud

router = APIRouter(prefix="", tags=["Products"])

@router.get("/feed", response_model=List[ProductFeedItemSchema])
async def get_guest_feed(db: AsyncSession = Depends(get_async_db)):
    products = await product_crud.get_guest_feed_products(db, limit=20)

    for product in products:
        if product.images:
            product.images = [product.images[0]]
        else:
            product.images = []

    return products


@router.get("/{product_id}", response_model=ProductDetailSchema)
async def get_product_details(
        product_id: uuid.UUID,
        db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieves detailed information for a single product, suitable for a product detail page.
    """
    product = await product_crud.get_product_by_id(db, product_id=product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Manually populate the seller field for the schema from the loaded relationship
    # This is needed because the schema expects 'seller' but the relationship is product.seller.user
    product_data = product.__dict__
    product_data['seller'] = product.seller.user

    return product_data
