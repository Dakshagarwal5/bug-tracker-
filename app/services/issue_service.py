from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.issue import IssueRepository
from app.repositories.comment import CommentRepository
from app.repositories.project import ProjectRepository
from app.repositories.user import UserRepository
from app.schemas.issue import IssueCreate, IssueUpdate
from app.models.user import User
from app.models.issue import Issue, IssueStatus
from app.core.exceptions import EntityNotFoundException, PermissionDeniedException, DomainRuleViolationException

class IssueService:
    def __init__(self, db: AsyncSession):
        self.issue_repo = IssueRepository(db)
        self.comment_repo = CommentRepository(db)
        self.project_repo = ProjectRepository(db)
        self.user_repo = UserRepository(db)

    async def create_issue(self, issue_in: IssueCreate, current_user: User) -> Issue:
        # Validate Project exists
        project = await self.project_repo.get_by_id_active(issue_in.project_id)
        if not project:
            raise EntityNotFoundException(entity_name="Project", identifier=issue_in.project_id)

        # Validate Assignee exists (if provided)
        if issue_in.assignee_id:
            assignee = await self.user_repo.get_by_id(issue_in.assignee_id)
            if not assignee or not assignee.is_active:
                raise EntityNotFoundException(entity_name="User", identifier=issue_in.assignee_id)

        try:
            issue_data = issue_in.model_dump()
            issue_data["reporter_id"] = current_user.id
            issue_data["status"] = IssueStatus.OPEN
            return await self.issue_repo.create(issue_data)
        except Exception as e:
            # Fallback catch-all for unexpected database driver errors
            print(f"CRITICAL DB ERROR: {e}")
            raise e

    async def get_issues(
        self,
        project_id: int | None,
        status: IssueStatus | None,
        severity: str | None,
        assignee_id: int | None,
        search: str | None,
        skip: int = 0,
        limit: int = 100,
        sort: str = "created_at",
    ) -> List[Issue]:
        return await self.issue_repo.get_filtered(
            project_id=project_id,
            status=status,
            severity=severity,
            assignee_id=assignee_id,
            search=search,
            skip=skip,
            limit=limit,
            sort=sort,
        )

    async def get_issue(self, issue_id: int) -> Issue:
        issue = await self.issue_repo.get_by_id(issue_id)
        if not issue:
            raise EntityNotFoundException(entity_name="Issue", identifier=issue_id)
        await self.issue_repo.db.refresh(issue, ["project"])
        if issue.project and issue.project.is_archived:
            raise EntityNotFoundException(entity_name="Project", identifier=issue.project_id)
        return issue

    async def update_issue(self, issue_id: int, issue_in: IssueUpdate, current_user: User) -> Issue:
        issue = await self.get_issue(issue_id)
        
        await self.issue_repo.db.refresh(issue, ["project"])
        if issue.project and issue.project.is_archived:
            raise EntityNotFoundException(entity_name="Project", identifier=issue.project_id)
        is_reporter = issue.reporter_id == current_user.id
        is_assignee = issue.assignee_id == current_user.id
        is_admin = current_user.is_admin
        is_project_owner = issue.project.owner_id == current_user.id
        
        if not (is_reporter or is_assignee or is_project_owner or is_admin):
            raise PermissionDeniedException("You do not have permission to edit this issue")

        if issue_in.assignee_id is not None and issue_in.assignee_id != issue.assignee_id:
            if not (is_reporter or is_project_owner or is_admin):
                 raise PermissionDeniedException("Only Reporter, Manager or Admin can change assignee")

        # State Machine Validation
        if issue_in.status is not None and issue_in.status != issue.status:
            allowed_transitions = {
                IssueStatus.OPEN: [IssueStatus.IN_PROGRESS],
                IssueStatus.IN_PROGRESS: [IssueStatus.RESOLVED],
                IssueStatus.RESOLVED: [IssueStatus.CLOSED, IssueStatus.REOPENED],
                IssueStatus.REOPENED: [IssueStatus.IN_PROGRESS, IssueStatus.RESOLVED],
                IssueStatus.CLOSED: [IssueStatus.REOPENED]
            }
            
            if issue_in.status not in allowed_transitions.get(issue.status, []):
                 raise DomainRuleViolationException(f"Invalid status transition from {issue.status} to {issue_in.status}")

            # Critical Issue Check
            if issue_in.status == IssueStatus.CLOSED and issue.severity == "critical":
                # Check comments count
                comments = await self.comment_repo.get_by_issue(issue_id, limit=1)
                if not comments:
                     raise DomainRuleViolationException("Critical issues cannot be closed without a comment")

        return await self.issue_repo.update(issue, issue_in.model_dump(exclude_unset=True))
