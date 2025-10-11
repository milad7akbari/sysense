import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate
from app.crud import user as user_crud

router = APIRouter(tags=["Users"])
logger = logging.getLogger(__name__)

@router.patch("/me", response_model=UserRead)
async def update_user_profile(
    user_updates: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):

    try:
        updated_user = await user_crud.update_user(db, db_user=current_user, user_in=user_updates)
        return updated_user
    except Exception as e:
        # Handle potential database errors, like a duplicate email
        logger.error(f"Error updating profile for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not update profile. The email might already be in use."
        )