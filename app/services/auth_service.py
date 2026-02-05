from datetime import timedelta, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserResponse, Token
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import EntityNotFoundException, AuthenticationFailedException
from app.core.config import settings
from app.core.token_service import generate_token_pair, rotate_refresh_token, logout, logout_all_devices
from app.models.user import UserRole

class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)

    async def register_user(self, user_in: UserCreate) -> UserResponse:
        existing_user = await self.user_repo.get_by_email(user_in.email)
        existing_username = await self.user_repo.get_by_username(user_in.username)
        if existing_user or existing_username:
            raise AuthenticationFailedException(detail="Email or username already registered")
        
        hashed_pw = get_password_hash(user_in.password)
        user_data = user_in.model_dump(exclude={"password"})
        user_data["hashed_password"] = hashed_pw
        # keep legacy flag aligned
        user_data["is_admin"] = user_in.role == UserRole.ADMIN

        new_user = await self.user_repo.create(user_data)
        return UserResponse.model_validate(new_user)

    async def login(self, email: str, password: str) -> Token:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationFailedException(detail="Invalid credentials")
        
        if not user.is_active:
            raise AuthenticationFailedException(detail="User is inactive")

        # Update last_login
        user.last_login = datetime.now(tz=timezone.utc)
        await self.user_repo.update(user, {"last_login": user.last_login})

        pair = await generate_token_pair(user.id)
        return Token(access_token=pair["access_token"], refresh_token=pair["refresh_token"], token_type="bearer")

    async def refresh(self, refresh_token: str) -> Token:
        pair = await rotate_refresh_token(refresh_token)
        return Token(access_token=pair["access_token"], refresh_token=pair["refresh_token"], token_type="bearer")

    async def logout(self, refresh_token: str) -> None:
        await logout(refresh_token)

    async def logout_all(self, user_id: int) -> None:
        await logout_all_devices(user_id)
