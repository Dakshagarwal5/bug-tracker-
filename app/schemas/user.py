from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from app.models.user import UserRole

class UserBase(BaseModel):
    username: Optional[str] = None
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    role: UserRole = UserRole.USER

class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None

class UserResponse(UserBase):
    id: int
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
