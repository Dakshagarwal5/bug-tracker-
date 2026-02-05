from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate, UserResponse, Token
from app.core.rate_limit import RateLimiter

router = APIRouter()

# Rate limit login: 5 per minute
login_limiter = RateLimiter(times=5, seconds=60)
refresh_limiter = RateLimiter(times=10, seconds=60)

@router.post("/login", response_model=Token, dependencies=[Depends(login_limiter)])
async def login_access_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    auth_service = AuthService(db)
    token = await auth_service.login(
        email=form_data.username, password=form_data.password
    )
    return token

@router.post("/register", response_model=UserResponse)
async def register_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user without the need to be logged in
    """
    auth_service = AuthService(db)
    user = await auth_service.register_user(user_in)
    return user

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user
    """
    return current_user


@router.post("/refresh", response_model=Token, dependencies=[Depends(refresh_limiter)])
async def refresh_token(
    *,
    db: AsyncSession = Depends(deps.get_db),
    refresh_token: str = Body(..., embed=True, min_length=10),
) -> Any:
    """
    Rotate refresh token and issue new token pair.
    """
    auth_service = AuthService(db)
    return await auth_service.refresh(refresh_token)


@router.post("/logout")
async def logout_current(
    *,
    db: AsyncSession = Depends(deps.get_db),
    refresh_token: str = Body(..., embed=True, min_length=10),
) -> Any:
    """
    Logout current session by revoking the provided refresh token.
    """
    auth_service = AuthService(db)
    await auth_service.logout(refresh_token)
    return {"detail": "Logged out"}


@router.post("/logout_all")
async def logout_all_devices(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
) -> Any:
    """
    Logout from all devices by bumping session version.
    """
    auth_service = AuthService(db)
    await auth_service.logout_all(current_user.id)
    return {"detail": "Logged out from all devices"}
