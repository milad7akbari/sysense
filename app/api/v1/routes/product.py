from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db
from app.schemas.product import ProductFeedItemSchema
from app.crud import product as product_crud

router = APIRouter(prefix="", tags=["Products"])

@router.get("/feed", response_model=List[ProductFeedItemSchema])
async def get_guest_feed(db: AsyncSession = Depends(get_async_db)):
    products = await product_crud.get_guest_feed_products(db, limit=20)
    return products
