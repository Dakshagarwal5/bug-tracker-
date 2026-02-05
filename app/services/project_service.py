from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.project import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.models.user import User
from app.models.project import Project
from app.core.exceptions import EntityNotFoundException, PermissionDeniedException

class ProjectService:
    def __init__(self, db: AsyncSession):
        self.project_repo = ProjectRepository(db)

    async def create_project(self, project_in: ProjectCreate, current_user: User) -> Project:
        project_data = project_in.model_dump()
        project_data["owner_id"] = current_user.id
        return await self.project_repo.create(project_data)

    async def get_projects(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        include_archived: bool = False,
        sort: str = "created_at",
    ) -> List[Project]:
        return await self.project_repo.get_filtered(
            search=search,
            include_archived=include_archived,
            skip=skip,
            limit=limit,
            sort=sort,
        )

    async def get_project(self, project_id: int) -> Project:
        project = await self.project_repo.get_by_id_active(project_id)
        if not project:
            raise EntityNotFoundException(entity_name="Project", identifier=project_id)
        return project

    async def update_project(self, project_id: int, project_in: ProjectUpdate, current_user: User) -> Project:
        project = await self.get_project(project_id)
        
        # Permission: Owner or Admin
        if project.owner_id != current_user.id and not current_user.is_admin:
            raise PermissionDeniedException("Only Owner or Admin can update project")

        return await self.project_repo.update(project, project_in.model_dump(exclude_unset=True))

    async def archive_project(self, project_id: int, current_user: User) -> Project:
        project = await self.get_project(project_id)
        
        # Permission: Owner or Admin
        if project.owner_id != current_user.id and not current_user.is_admin:
            raise PermissionDeniedException("Only Owner or Admin can archive project")
            
        return await self.project_repo.update(project, {"is_archived": True})
