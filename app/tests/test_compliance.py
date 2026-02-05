import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import UserRole
from app.core.security import create_access_token

# Helpers
def get_auth_headers(user_id: int):
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_user_crud_permissions(client: AsyncClient, db_session: AsyncSession):
    # Setup: Create Admin and Regular User in DB
    from app.models.user import User
    from app.core.security import get_password_hash
    
    admin = User(
        username="admin", 
        email="admin@test.com", 
        hashed_password=get_password_hash("pass"), 
        role=UserRole.ADMIN,
        is_active=True
    )
    user = User(
        username="user", 
        email="user@test.com", 
        hashed_password=get_password_hash("pass"), 
        role=UserRole.USER,
        is_active=True
    )
    db_session.add_all([admin, user])
    await db_session.commit()
    await db_session.refresh(admin)
    await db_session.refresh(user)

    # 1. Admin can list users
    headers = get_auth_headers(admin.id)
    r = await client.get("/api/v1/users/", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) >= 2

    # 2. Regular user CANNOT list users
    headers_user = get_auth_headers(user.id)
    r = await client.get("/api/v1/users/", headers=headers_user)
    assert r.status_code == 403

    # 3. Regular user cannot update others
    r = await client.put(f"/api/v1/users/{admin.id}", headers=headers_user, json={"full_name": "Hacked"})
    assert r.status_code == 403

@pytest.mark.asyncio
async def test_issue_state_machine(client: AsyncClient, db_session: AsyncSession):
    # Setup: Create User, Project, Issue
    from app.models.user import User
    from app.models.project import Project
    from app.models.issue import Issue, IssueStatus
    from app.core.security import get_password_hash

    me = User(username="me", email="me@test.com", hashed_password=get_password_hash("pass"), role=UserRole.USER)
    db_session.add(me)
    await db_session.commit()
    await db_session.refresh(me)

    project = Project(name="Test Proj", description="desc", key="TEST", owner_id=me.id)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    issue = Issue(
        title="Bug", 
        description="desc", 
        project_id=project.id, 
        reporter_id=me.id, 
        status=IssueStatus.OPEN,
        severity="medium"
    )
    db_session.add(issue)
    await db_session.commit()
    await db_session.refresh(issue)

    headers = get_auth_headers(me.id)

    # 1. Valid Transition: OPEN -> IN_PROGRESS
    r = await client.put(f"/api/v1/issues/{issue.id}", headers=headers, json={"status": "in_progress"})
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress"

    # 2. Invalid Transition: IN_PROGRESS -> OPEN (Not allowed in my spec/code logic?)
    # Checked logic: OPEN->IN_PG, IN_PG->RESOLVED. So IN_PG cannot go back to OPEN.
    r = await client.put(f"/api/v1/issues/{issue.id}", headers=headers, json={"status": "open"})
    assert r.status_code == 400  # DomainRuleViolation

@pytest.mark.asyncio
async def test_critical_issue_rule(client: AsyncClient, db_session: AsyncSession):
    from app.models.user import User
    from app.models.project import Project
    from app.models.issue import Issue, IssueStatus
    
    me = User(username="me2", email="me2@test.com", hashed_password="pw", role=UserRole.USER)
    db_session.add(me)
    await db_session.commit()
    
    p = Project(name="P2", key="P2", owner_id=me.id)
    db_session.add(p)
    await db_session.commit()

    # Create Critical Issue, Status RESOLVED (so we can try to CLOSE it)
    issue = Issue(
        title="Crit", project_id=p.id, reporter_id=me.id, 
        status=IssueStatus.RESOLVED, severity="critical"
    )
    db_session.add(issue)
    await db_session.commit()
    await db_session.refresh(issue)

    headers = get_auth_headers(me.id)

    # Try to CLOSE without comment -> Should Fails
    r = await client.put(f"/api/v1/issues/{issue.id}", headers=headers, json={"status": "closed"})
    assert r.status_code == 400
    assert "comment" in r.json()["detail"]

    # Now add comment
    from app.models.comment import Comment
    c = Comment(content="Fixed", issue_id=issue.id, author_id=me.id)
    db_session.add(c)
    await db_session.commit()

    # Try CLOSE again -> Success
    r = await client.put(f"/api/v1/issues/{issue.id}", headers=headers, json={"status": "closed"})
    assert r.status_code == 200

