# ruff: noqa: E402
import logging
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

# Ensure project root directory is in sys.path for uvicorn reloader on Windows
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# noqa: E402
from fastapi import APIRouter, FastAPI, Request, status  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.api.ai_pipeline import router as ai_router
from backend.api.auth import router as auth_router
from backend.api.departments import router as departments_router
from backend.api.notifications import router as notifications_router
from backend.api.reports import router as reports_router
from backend.api.rewards import router as rewards_router
from backend.api.uploads import router as uploads_router
from backend.core.config import settings
from backend.core.database import engine
from backend.core.logging_config import setup_logging
from backend.models import Base

# Initialize production-grade structured JSON logging (PR-02)
setup_logging()

logger = logging.getLogger(__name__)



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: validate DB connectivity & create tables if missing (F-01)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database connection pool & tables initialized successfully")
    except Exception as e:
        logger.warning("Database connection pool startup warning: %s", e)

    yield


    # Shutdown: dispose engine pool cleanly (F-01)
    try:
        await engine.dispose()
        logger.info("Database connection pool disposed cleanly")
    except Exception as e:
        logger.warning("Database connection pool disposal error: %s", e)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Generate or propagate unique X-Request-ID header for end-to-end request tracing (F-03)."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Sanitizes unhandled exceptions to prevent internal data leakage (F-02, S-11)."""
    logger.error(
        f"Unhandled server exception on path {request.url.path}: {exc}",
        exc_info=True,
    )
    detail = str(exc) if settings.debug else "An unexpected internal server error occurred."
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": detail,
            "request_id": getattr(request.state, "request_id", None),
        },
    )


# CORS middleware configuration for web & Expo clients (S-02)
cors_origins = settings.cors_origins if settings.cors_origins else ["*"]
allow_origin_regex = settings.cors_origin_regex if settings.debug else None

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# Base API v1 router
api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(departments_router)
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(rewards_router)
api_v1_router.include_router(uploads_router)
api_v1_router.include_router(ai_router)

app.include_router(api_v1_router)


@app.get("/health", include_in_schema=False)
async def health_check():
    """Dependency-aware health check verifying DB connectivity (PR-01)."""
    checks: dict[str, Any] = {
        "database": "unknown",
    }
    is_healthy = True

    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        logger.error("Health check database failure: %s", e)
        checks["database"] = f"unhealthy: {type(e).__name__}"
        is_healthy = False

    overall_status = "healthy" if is_healthy else "unhealthy"
    status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status,
            "service": settings.app_name,
            "version": settings.app_version,
            "checks": checks,
        },
    )



@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.app_name} API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
