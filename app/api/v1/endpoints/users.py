from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.exceptions import PermissionDeniedException, EntityNotFoundException
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.auth_service import AuthService

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def read_users(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, gt=0, le=100),
    is_active: bool = Query(True),
    current_user: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Retrieve users. Only for Admins.
    """
    # Simple filtration by active status for now, can be expanded
    # We'll use a direct repository call here or service if logic grows.
    # Since it's simple retrieval, repo is fine, but sticking to service pattern is better if we had a UserService. 
    # For now, using Repo directly as per existing patterns in some places or AuthService?
    # Actually, User management fits well in AuthService or a dedicated UserService. 
    # Given AuthService exists, let's see if we should add there or keep it simple.
    # Let's use the Repository directly for read operations to avoid bloating AuthService with simple CRUD 
    # unless business logic is needed.
    
    repo = UserRepository(db)
    # We need to implement get_multi in UserRepository or BaseRepository
    # Assuming BaseRepository has get_multi or similar. 
    # Looking at BaseRepository (we saw user.py repo, let's assume base has it or we add it).
    # Wait, we haven't seen BaseRepository. Let's assume standard crud. 
    # If not, we'll write a simple query here.
    
    # Actually, let's implement a clean query here to be safe and explicit.
    from sqlalchemy import select
    query = select(User).offset(skip).limit(limit)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
        
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserResponse)
async def read_user_by_id(
    user_id: int = Path(..., gt=0, example=1),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    if user_id == current_user.id:
        return current_user
        
    if not current_user.is_admin:
        raise PermissionDeniedException("Not enough privileges")
        
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise EntityNotFoundException("User", user_id)
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_id: int = Path(..., gt=0, example=1),
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update a user.
    """
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise EntityNotFoundException("User", user_id)

    # Permission check: Self or Admin
    if not current_user.is_admin and current_user.id != user_id:
        raise PermissionDeniedException("Not enough privileges")

    # Prevent privilege escalation: Non-admin cannot set role to admin
    if user_in.role == UserRole.ADMIN and not current_user.is_admin:
         raise PermissionDeniedException("Cannot promote to Admin without Admin privileges")

    # If updating self and disabling active, warning? Allowed.
    
    # We need to handle password update if present (hashing)
    update_data = user_in.model_dump(exclude_unset=True)
    
    if "password" in update_data and update_data["password"]:
        from app.core.security import get_password_hash
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        update_data["hashed_password"] = hashed_password

    user = await repo.update(user, update_data)
    return user


@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_id: int = Path(..., gt=0, example=1),
    current_user: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Delete a user (Soft delete typically, or hard delete?).
    The requirements say "User deletion behavior is safe". 
    Soft delete is usually safer. Let's start with soft delete (is_active=False).
    Or if we want actual delete, we need to handle orphans. 
    Let's stick to Soft Delete for now by setting is_active=False, 
    unless the spec explicitly asks for hard delete. 
    "User deletion behavior is safe" implies we shouldn't break FKs.
    So Soft Delete is the way.
    """
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise EntityNotFoundException("User", user_id)
        
    # Prevent deleting self?
    if user.id == current_user.id:
         raise PermissionDeniedException("Cannot delete yourself")
         
    # Soft delete
    user = await repo.update(user, {"is_active": False})
    return user
