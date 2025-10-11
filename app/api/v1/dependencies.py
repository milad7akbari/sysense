from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.db.session import get_async_db
from app.models.user import User
from app.crud import user as user_crud

async def get_current_user(
        db: AsyncSession = Depends(get_async_db),
        token: str = Depends(security.oauth2_scheme)
) -> User:
    payload = security.decode_token(token)

    if not payload or payload.type != 'access':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Access Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.sub
    user = await user_crud.get_user_by_id(db, user_id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user