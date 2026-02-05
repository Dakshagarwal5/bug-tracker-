import redis.asyncio as redis
from fastapi import Request, Response, HTTPException, status
from app.core.config import settings

redis_client = redis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}", encoding="utf-8", decode_responses=True)

class RateLimiter:
    def __init__(self, times: int, seconds: int):
        self.times = times
        self.seconds = seconds

    async def __call__(self, request: Request, response: Response):
        client_ip = request.client.host
        # Key specific to route or global? 
        # For simplicity, we use client_ip + path (optional) or just client_ip for global
        # But this class is generic.
        
        # If used as dependency on specific route, usage is per route logic usually.
        # But here we want simple "5/min/IP" for login.
        key = f"rate_limit:{client_ip}:{request.url.path}"
        
        current = await redis_client.get(key)
        
        if current and int(current) >= self.times:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests"
            )
            
        async with redis_client.pipeline() as pipe:
            await pipe.incr(key)
            if not current:
                await pipe.expire(key, self.seconds)
            await pipe.execute()
            
