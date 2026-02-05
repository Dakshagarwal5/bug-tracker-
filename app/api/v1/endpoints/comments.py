from typing import Any, List
from fastapi import APIRouter, Depends, Path, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.schemas.comment import CommentCreate, CommentResponse
from app.services.comment_service import CommentService
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[CommentResponse])
async def read_comments(
    issue_id: int = Query(..., gt=0, title="ID of the issue to fetch comments for", examples=[10]),
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0, le=1000),
    limit: int = Query(100, gt=0, le=100),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    service = CommentService(db)
    return await service.get_comments(issue_id, skip=skip, limit=limit)

@router.post("/", response_model=CommentResponse)
async def create_comment(
    *,
    db: AsyncSession = Depends(deps.get_db),
    comment_in: CommentCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    service = CommentService(db)
    return await service.create_comment(comment_in, current_user)


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    *,
    db: AsyncSession = Depends(deps.get_db),
    comment_id: int = Path(..., gt=0, examples=[1]),
    content: str = Body(..., embed=True, min_length=1, max_length=2000),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    service = CommentService(db)
    return await service.update_comment(comment_id, content, current_user)
