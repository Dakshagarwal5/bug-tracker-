
import asyncio
import sys
from app.core.config import settings
import redis.asyncio as redis

# Print settings to verify
print(f"Testing Redis connection at {settings.REDIS_HOST}:{settings.REDIS_PORT}")

async def test_redis():
    try:
        r = redis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}", 
            encoding="utf-8", 
            decode_responses=True,
            socket_connect_timeout=2  # Short timeout for testing
        )
        await r.ping()
        print("SUCCESS: Redis connection established.")
        await r.close()
    except Exception as e:
        print(f"FAILURE: Could not connect to Redis. Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_redis())
