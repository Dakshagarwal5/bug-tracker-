import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_issue_validation(client: AsyncClient):
    # 1. Register and Login
    register_data = {
        "email": "issue_tester@example.com",
        "password": "password123",
        "full_name": "Issue Tester"
    }
    await client.post("/api/v1/auth/register", json=register_data)
    
    login_data = {"username": "issue_tester@example.com", "password": "password123"}
    response = await client.post("/api/v1/auth/login", data=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create a Project (ID 1)
    project_data = {"name": "Test Project", "description": "Test Desc", "key": "TP"}
    response = await client.post("/api/v1/projects/", json=project_data, headers=headers)
    assert response.status_code == 200, response.text
    project_id = response.json()["id"]

    # 3. Test Invalid Project ID (Foreign Key Check)
    invalid_project_issue = {
        "title": "Bug with invalid project",
        "description": "This should fail",
        "project_id": 99999
    }
    response = await client.post("/api/v1/issues/", json=invalid_project_issue, headers=headers)
    assert response.status_code == 404
    assert "Project" in response.json()["detail"]

    # 4. Test Schema Validation (project_id=0)
    zero_project_issue = {
        "title": "Bug with zero project",
        "description": "This should fail validation",
        "project_id": 0
    }
    response = await client.post("/api/v1/issues/", json=zero_project_issue, headers=headers)
    assert response.status_code == 422
    
    # 5. Test Invalid Assignee (Foreign Key Check)
    invalid_assignee_issue = {
        "title": "Bug with invalid assignee",
        "description": "This should fail",
        "project_id": project_id,
        "assignee_id": 99999
    }
    response = await client.post("/api/v1/issues/", json=invalid_assignee_issue, headers=headers)
    assert response.status_code == 404
    assert "User" in response.json()["detail"]

    # 6. Test Valid Creation
    valid_issue = {
        "title": "Valid Bug",
        "description": "This should succeed",
        "project_id": project_id
    }
    response = await client.post("/api/v1/issues/", json=valid_issue, headers=headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Valid Bug"
    
    print("\nSUCCESS: Issue creation hardening verified.")
