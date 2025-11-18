"""API routes package."""

from fastapi import APIRouter

from app.api import endpoints

api_router = APIRouter()

# Include endpoint routers (will be added as we build features)
# api_router.include_router(endpoints.summary.router, tags=["summary"])
# api_router.include_router(endpoints.sentiment.router, tags=["sentiment"])
# api_router.include_router(endpoints.posts.router, tags=["posts"])
# api_router.include_router(endpoints.admin.router, tags=["admin"])

__all__ = ["api_router"]
