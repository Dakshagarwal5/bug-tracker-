from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.config import settings

from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.core.exceptions import AuthenticationFailedException, EntityNotFoundException
from app.core.token_service import decode_and_validate, logout_all_devices

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    payload = await decode_and_validate(token, expected_type="access")
    user_id = int(payload["sub"])

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise EntityNotFoundException("User", identifier=user_id)

    if not user.is_active:
        raise AuthenticationFailedException("Inactive user")

    # Align legacy flag with role enum for downstream permission checks
    try:
        from app.models.user import UserRole
        user.is_admin = user.role == UserRole.ADMIN
    except Exception:
        pass
    return user

async def get_current_active_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="The user doesn't have enough privileges"
        )
    return current_user
