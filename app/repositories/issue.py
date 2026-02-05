from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.issue import Issue, IssueStatus

class IssueRepository(BaseRepository[Issue]):
    def __init__(self, db: AsyncSession):
        super().__init__(Issue, db)

    async def get_by_project(self, project_id: int, skip: int = 0, limit: int = 100) -> List[Issue]:
        query = select(Issue).where(Issue.project_id == project_id).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_filtered(
        self,
        project_id: Optional[int],
        status: Optional[IssueStatus],
        severity: Optional[str],
        assignee_id: Optional[int],
        search: Optional[str],
        skip: int,
        limit: int,
        sort: str,
    ) -> List[Issue]:
        sort_mapping = {
            "created_at": Issue.created_at,
            "-created_at": desc(Issue.created_at),
            "severity": Issue.severity,
            "-severity": desc(Issue.severity),
            "title": Issue.title,
            "-title": desc(Issue.title),
        }
        order_clause = sort_mapping.get(sort, desc(Issue.created_at))

        query = select(Issue)
        if project_id:
            query = query.where(Issue.project_id == project_id)
        if status:
            query = query.where(Issue.status == status)
        if severity:
            query = query.where(Issue.severity == severity)
        if assignee_id:
            query = query.where(Issue.assignee_id == assignee_id)
        if search:
            query = query.where(Issue.title.ilike(f"%{search}%"))

        query = query.order_by(order_clause).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
