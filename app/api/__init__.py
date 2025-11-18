"""API routes package."""

from fastapi import APIRouter

from app.api.endpoints import admin, leaderboard, posts, sentiment, summary

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(summary.router, tags=["summary"])
api_router.include_router(sentiment.router, tags=["sentiment"])
api_router.include_router(posts.router, tags=["posts"])
api_router.include_router(leaderboard.router, tags=["leaderboard"])
api_router.include_router(admin.router, tags=["admin"])

__all__ = ["api_router"]
