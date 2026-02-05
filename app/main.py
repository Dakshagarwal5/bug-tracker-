from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.logging import setup_logging
from app.middlewares.global_rate_limit import GlobalRateLimitMiddleware
from app.core.exceptions import BaseAPIException
from app.db.init_db import init_db


# -------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------
setup_logging()


# -------------------------------------------------------------------
# Lifespan (Startup / Shutdown)
# -------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🔐 Startup validation
    print("Startup: Validating configuration...")

    if not settings.PRIVATE_KEY or not settings.PUBLIC_KEY:
        print("CRITICAL: Auth keys are missing or empty.")
        print("Ensure /app/keys/private.pem and /app/keys/public.pem are mounted.")
        raise RuntimeError("Startup failed: authentication keys missing.")

    print("Startup: Keys verified successfully.")

    # 🗄️ Database initialization (DEV / TEST)
    print("Startup: Initializing database schema...")
    await init_db()
    print("Startup: Database schema ready.")

    yield

    # Optional shutdown logic
    print("Shutdown: Application shutting down.")


# -------------------------------------------------------------------
# FastAPI App
# -------------------------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)


# -------------------------------------------------------------------
# Middleware
# -------------------------------------------------------------------

# CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Global Rate Limiting (100 req/min/IP)
app.add_middleware(
    GlobalRateLimitMiddleware,
    times=100,
    seconds=60,
)

# Trusted Hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)


# -------------------------------------------------------------------
# Health Check
# -------------------------------------------------------------------
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint to verify service status.
    """
    return {"status": "ok"}


# -------------------------------------------------------------------
# Exception Handlers
# -------------------------------------------------------------------
@app.exception_handler(BaseAPIException)
async def api_exception_handler(request: Request, exc: BaseAPIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(RedisConnectionError)
async def redis_exception_handler(request: Request, exc: RedisConnectionError):
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Service unavailable: cache / rate-limit service is down."
        },
    )


# -------------------------------------------------------------------
# Routers
# -------------------------------------------------------------------
app.include_router(api_router, prefix=settings.API_V1_STR)
