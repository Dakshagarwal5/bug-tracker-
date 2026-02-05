from typing import Any, List
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.schemas.issue import IssueCreate, IssueUpdate, IssueResponse
from app.services.issue_service import IssueService
from app.models.user import User
from app.models.issue import IssueStatus

router = APIRouter()

@router.get("/", response_model=List[IssueResponse])
async def read_issues(
    db: AsyncSession = Depends(deps.get_db),
    project_id: int | None = Query(None, gt=0, title="Filter by project id", example=1),
    status: IssueStatus | None = Query(None),
    severity: str | None = Query(None, pattern="^(low|medium|high|critical)$"),
    assignee_id: int | None = Query(None, gt=0),
    search: str | None = Query(None, min_length=1, max_length=100),
    sort: str = Query("created_at", description="created_at,-created_at,severity,-severity,title,-title", example="-created_at"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, gt=0, le=100),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    service = IssueService(db)
    skip = (page - 1) * limit
    safe_sort = sort if sort in {"created_at", "-created_at", "severity", "-severity", "title", "-title"} else "created_at"
    return await service.get_issues(
        project_id=project_id,
        status=status,
        severity=severity,
        assignee_id=assignee_id,
        search=search,
        skip=skip,
        limit=limit,
        sort=safe_sort,
    )

@router.post("/", response_model=IssueResponse)
async def create_issue(
    *,
    db: AsyncSession = Depends(deps.get_db),
    issue_in: IssueCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    # issue_in contains project_id
    service = IssueService(db)
    return await service.create_issue(issue_in, current_user)

@router.get("/{issue_id}", response_model=IssueResponse)
async def read_issue(
    issue_id: int = Path(..., gt=0, title="The ID of the issue to get", example=10),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    service = IssueService(db)
    return await service.get_issue(issue_id)

@router.put("/{issue_id}", response_model=IssueResponse)
async def update_issue(
    *,
    db: AsyncSession = Depends(deps.get_db),
    issue_id: int = Path(..., gt=0, title="The ID of the issue to update", example=10),
    issue_in: IssueUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    service = IssueService(db)
    return await service.update_issue(issue_id, issue_in, current_user)
