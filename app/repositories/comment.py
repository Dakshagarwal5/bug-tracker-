from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.comment import Comment

class CommentRepository(BaseRepository[Comment]):
    def __init__(self, db: AsyncSession):
        super().__init__(Comment, db)

    async def get_by_issue(self, issue_id: int, skip: int = 0, limit: int = 100) -> List[Comment]:
        query = select(Comment).where(Comment.issue_id == issue_id).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
