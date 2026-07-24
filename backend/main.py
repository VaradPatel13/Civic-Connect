from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.ai_pipeline import router as ai_router
from backend.api.auth import router as auth_router
from backend.api.departments import router as departments_router
from backend.api.notifications import router as notifications_router
from backend.api.reports import router as reports_router
from backend.api.rewards import router as rewards_router
from backend.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS middleware for web & Expo React Native clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
api_v1_router.include_router(ai_router)

app.include_router(api_v1_router)


@app.get("/health", include_in_schema=False)
async def health_check():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy", "service": settings.app_name},
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
