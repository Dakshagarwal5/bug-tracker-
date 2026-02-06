import os
import sys
import time
from typing import Dict, Optional

import redis.asyncio as redis
from fastapi import Request, Response, HTTPException, status

from app.core.config import settings


class _InMemoryPipeline:
    def __init__(self, store: Dict[str, int], expirations: Dict[str, float]):
        self._store = store
        self._expirations = expirations

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def incr(self, key: str):
        self._store[key] = self._store.get(key, 0) + 1

    async def expire(self, key: str, seconds: int):
        self._expirations[key] = time.monotonic() + seconds

    async def execute(self):
        return True


class _InMemoryRedis:
    def __init__(self):
        self._store: Dict[str, int] = {}
        self._expirations: Dict[str, float] = {}

    def _is_expired(self, key: str) -> bool:
        expires_at = self._expirations.get(key)
        if expires_at is None:
            return False
        if time.monotonic() >= expires_at:
            self._store.pop(key, None)
            self._expirations.pop(key, None)
            return True
        return False

    async def get(self, key: str) -> Optional[str]:
        if self._is_expired(key):
            return None
        value = self._store.get(key)
        return None if value is None else str(value)

    async def set(self, key: str, value: str, ex: Optional[int] = None):
        self._store[key] = int(value) if isinstance(value, int) else value
        if ex is not None:
            self._expirations[key] = time.monotonic() + ex

    async def incr(self, key: str):
        current = self._store.get(key)
        next_value = int(current) + 1 if current is not None else 1
        self._store[key] = next_value
        return next_value

    async def exists(self, key: str) -> int:
        if self._is_expired(key):
            return 0
        return 1 if key in self._store else 0

    async def delete(self, key: str) -> int:
        existed = 1 if key in self._store else 0
        self._store.pop(key, None)
        self._expirations.pop(key, None)
        return existed

    async def flushall(self) -> None:
        self._store.clear()
        self._expirations.clear()

    def pipeline(self):
        return _InMemoryPipeline(self._store, self._expirations)


if "pytest" in sys.modules or os.getenv("ALLOW_INMEMORY_RATE_LIMIT") == "1":
    redis_client = _InMemoryRedis()
else:
    redis_client = redis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        encoding="utf-8",
        decode_responses=True,
    )

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
            
