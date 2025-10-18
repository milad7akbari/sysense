from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies import get_current_user
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.interaction import InteractionCreate, InteractionRead
from app.crud import interaction as interaction_crud

router = APIRouter(prefix="/interactions", tags=["Interactions"])

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