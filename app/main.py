from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.core.logging import setup_logging
from app.middlewares.global_rate_limit import GlobalRateLimitMiddleware
from app.core.exceptions import BaseAPIException

from contextlib import asynccontextmanager

# Setup Logging
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation
    print("Startup: Validating configuration...")
    if not settings.PRIVATE_KEY or not settings.PUBLIC_KEY:
        print("CRITICAL: Keys are missing. Exiting.")
        # In a real ASGI app exception here prevents startup
        raise RuntimeError("Keys missing! Cannot start.")
    print("Startup: Keys verified.")
    yield
    # Shutdown logic if any

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Global Rate Limit: 100 req/min/IP
app.add_middleware(GlobalRateLimitMiddleware, times=100, seconds=60)

# Trusted Host Middleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.ALLOWED_HOSTS
)

@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint to verify service status.
    """
    return {"status": "ok"}

# Exception Handlers
@app.exception_handler(BaseAPIException)
async def api_exception_handler(request: Request, exc: BaseAPIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


from redis.exceptions import ConnectionError as RedisConnectionError

@app.exception_handler(RedisConnectionError)
async def redis_exception_handler(request: Request, exc: RedisConnectionError):
    return JSONResponse(
        status_code=503,
        content={"detail": "Service unavailable: Cache/Rate-limit service is down."},
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
