from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from redis.exceptions import ConnectionError as RedisConnectionError
from app.core.rate_limit import RateLimiter

class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, times: int = 100, seconds: int = 60):
        super().__init__(app)
        self.limiter = RateLimiter(times=times, seconds=seconds)

    async def dispatch(self, request: Request, call_next):
        # We need to manually call the limiter.
        # Note: RateLimiter.__call__ raises HTTPException.
        # Middleware catching exception is tricky in Starlette, easier to try/except
        # But RateLimiter is async.
        
        # Also rate limiter needs 'response' object sometimes if we want to set headers, 
        # but here we just raise exception.
        # But `RateLimiter.__call__` expects (request, response).
        
        # Let's adapt logic here or use the limiter class differently.
        # The limiter class logic:
        # checks redis, raises 429 if too many.
        
        try:
            # Fake response object or modify limiter signature?
            # Let's just copy logic:
            await self.limiter(request, None)
        except RedisConnectionError:
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "Service unavailable: cache / rate-limit service is down."
                },
            )
        except HTTPException as exc:
            if exc.status_code == 429:
                return Response("Too many requests", status_code=429)
            raise

        response = await call_next(request)
        return response
