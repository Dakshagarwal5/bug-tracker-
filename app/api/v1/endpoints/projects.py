from typing import Any, List
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.project_service import ProjectService
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[ProjectResponse])
async def read_projects(
    db: AsyncSession = Depends(deps.get_db),
    page: int = Query(1, ge=1, examples=[1]),
    limit: int = Query(20, gt=0, le=100, examples=[20]),
    search: str | None = Query(None, min_length=1, max_length=100),
    is_archived: bool = Query(False, description="Include archived projects"),
    sort: str = Query("created_at", description="Sort by name,-name,created_at,-created_at"),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    service = ProjectService(db)
    skip = (page - 1) * limit
    return await service.get_projects(
        skip=skip,
        limit=limit,
        search=search,
        include_archived=is_archived,
        sort=sort if sort in {"name", "-name", "created_at", "-created_at"} else "created_at",
    )

@router.post("/", response_model=ProjectResponse)
async def create_project(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_in: ProjectCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    service = ProjectService(db)
    return await service.create_project(project_in, current_user)

@router.get("/{project_id}", response_model=ProjectResponse)
async def read_project(
    project_id: int = Path(..., gt=0, title="The ID of the project to get", examples=[1]),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    service = ProjectService(db)
    return await service.get_project(project_id)

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_id: int = Path(..., gt=0, title="The ID of the project to update", examples=[1]),
    project_in: ProjectUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    service = ProjectService(db)
    return await service.update_project(project_id, project_in, current_user)

@router.delete("/{project_id}", response_model=ProjectResponse)
async def archive_project(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_id: int = Path(..., gt=0, title="The ID of the project to delete", examples=[1]),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    service = ProjectService(db)
    return await service.archive_project(project_id, current_user)
