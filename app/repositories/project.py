from typing import List, Optional
from sqlalchemy import select, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.project import Project

class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db: AsyncSession):
        super().__init__(Project, db)

    async def get_active_projects(self, skip: int = 0, limit: int = 100) -> List[Project]:
        query = select(Project).where(Project.is_archived == False).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_filtered(
        self,
        search: Optional[str],
        include_archived: bool,
        skip: int,
        limit: int,
        sort: str,
    ) -> List[Project]:
        sort_mapping = {
            "name": Project.name,
            "-name": desc(Project.name),
            "created_at": Project.created_at,
            "-created_at": desc(Project.created_at),
        }
        order_clause = sort_mapping.get(sort, Project.created_at)

        query = select(Project)
        if not include_archived:
            query = query.where(Project.is_archived == False)
        if search:
            query = query.where(Project.name.ilike(f"%{search}%"))
        query = query.order_by(order_clause).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_id_active(self, id: int) -> Optional[Project]:
        query = select(Project).where(Project.id == id, Project.is_archived == False)
        result = await self.db.execute(query)
        return result.scalars().first()
