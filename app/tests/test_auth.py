import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    # Register
    register_data = {
        "email": "test@example.com",
        "password": "strongpassword",
        "full_name": "Test User"
    }
    response = await client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == register_data["email"]
    assert "id" in data
    
    # Login
    login_data = {
        "username": "test@example.com",
        "password": "strongpassword"
    }
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    # Register
    register_data = {
        "email": "test2@example.com",
        "password": "strongpassword",
        "full_name": "Test User"
    }
    await client.post("/api/v1/auth/register", json=register_data)
    
    # Login Fail
    login_data = {
        "username": "test2@example.com",
        "password": "wrongpassword"
    }
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401
