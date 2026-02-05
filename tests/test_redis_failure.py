
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from redis.exceptions import ConnectionError as RedisConnectionError

# Import app after patching if necessary, but we can patch object instances
from app.main import app
from app.core.rate_limit import redis_client

@pytest.mark.asyncio
async def test_redis_connection_error_handling():
    # Patch the redis_client.get method to raise ConnectionError
    # We need to patch where it is USED.
    # It is used in RateLimiter (Global Middleware) AND AuthService (Endpoint)
    
    # We want to see what happens when Redis is down effectively everywhere.
    
    with patch.object(redis_client, 'get', side_effect=RedisConnectionError("Connection refused")), \
         patch.object(redis_client, 'pipeline', side_effect=RedisConnectionError("Connection refused")):
        
        client = TestClient(app)
        
        # Try to login
        # We expect 503 if our handler works and middleware doesn't swallow it.
        # If middleware swallows it as 429, we will see 429.
        # If something else blows up, we might see 500.
        
        response = client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "password"})
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Content: {response.json() if response.headers.get('content-type') == 'application/json' else response.text}")
        
        # We assert 503 because that's our GOAL. 
        # If this fails, we debug.
        assert response.status_code == 503
        assert "Service unavailable" in response.json().get("detail", "")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_redis_connection_error_handling())
