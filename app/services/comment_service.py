from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
import bleach
from app.repositories.comment import CommentRepository
from app.schemas.comment import CommentCreate
from app.models.user import User
from app.models.comment import Comment
from app.repositories.issue import IssueRepository
from app.core.exceptions import EntityNotFoundException, PermissionDeniedException

class CommentService:
    def __init__(self, db: AsyncSession):
        self.comment_repo = CommentRepository(db)
        self.issue_repo = IssueRepository(db)

    async def create_comment(self, comment_in: CommentCreate, current_user: User) -> Comment:
        # Check if issue exists
        issue = await self.issue_repo.get_by_id(comment_in.issue_id)
        if not issue:
             raise EntityNotFoundException(entity_name="Issue", identifier=comment_in.issue_id)
             
        comment_data = comment_in.model_dump()
        comment_data["author_id"] = current_user.id
        comment_data["content"] = bleach.clean(comment_data["content"], strip=True)
        return await self.comment_repo.create(comment_data)

    async def get_comments(self, issue_id: int, skip: int = 0, limit: int = 100) -> List[Comment]:
        return await self.comment_repo.get_by_issue(issue_id, skip, limit)
    
    async def update_comment(self, comment_id: int, content: str, current_user: User) -> Comment:
        comment = await self.comment_repo.get_by_id(comment_id)
        if not comment:
            raise EntityNotFoundException(entity_name="Comment", identifier=comment_id)
        if comment.author_id != current_user.id:
            raise PermissionDeniedException("Only the author can edit a comment")
        sanitized = bleach.clean(content, strip=True)
        return await self.comment_repo.update(comment, {"content": sanitized})

    # Deleting comments is intentionally unsupported
