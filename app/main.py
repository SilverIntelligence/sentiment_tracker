"""Main FastAPI application."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.core.config import get_settings
from app.db import get_redis, init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan handler."""
    # Startup
    print("Starting up sentiment tracker...")
    init_db()
    print("Database initialized")

    # Test Redis connection
    try:
        r = get_redis()
        r.ping()
        print("Redis connection successful")
    except Exception as e:
        print(f"Redis connection failed: {e}")

    yield

    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Reddit Precious Metals Sentiment Tracker API",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.app_name,
        "version": settings.version,
        "status": "running",
    }


@app.get("/healthz")
async def healthz():
    """Health check endpoint."""
    try:
        # Check Redis
        r = get_redis()
        r.ping()

        # Check DB (will be tested when we have models)

        return JSONResponse(
            content={
                "status": "healthy",
                "redis": "connected",
                "database": "connected",
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
            },
        )


# Include API router
app.include_router(api_router, prefix="/api/v1")
