import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.user import UserRead, UserBase
from app.crud import user as user_crud

router = APIRouter(tags=["Users"])
logger = logging.getLogger(__name__)


@router.patch("/me", response_model=UserRead)
async def update_user_profile(
    user_updates: UserBase,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        updated_user = await user_crud.update_user(db, db_user=current_user, user_in=user_updates)
        return updated_user
    except IntegrityError:
        await db.rollback() # Rollback the session to a clean state
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, # 409 Conflict is often more suitable
            detail="Could not update profile. The email or phone number might already be in use."
        )
    except Exception as e:
        # A general catch-all for other unexpected errors
        await db.rollback()
        logger.error(f"An unexpected error occurred updating user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating the profile."
        )
