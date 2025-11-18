"""Posts API endpoints."""

import logging
import math
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Comment, Post
from app.schemas.responses import PostComment, PostDetailResponse, TopPost

logger = logging.getLogger(__name__)
router = APIRouter()


def calculate_impact_score(post: Post) -> float:
    """Calculate post impact score with time decay."""
    # Base score: upvotes + 2*comments
    base = post.score + (post.num_comments * 2)

    # Time decay: exp(-age_hours / 24)
    age_hours = (datetime.utcnow() - post.created_utc).total_seconds() / 3600
    decay = math.exp(-age_hours / 24)

    # Sentiment weight (absolute value boosts impact)
    sentiment_weight = 1.0 + abs(post.sentiment or 0) * 0.5

    return base * decay * sentiment_weight


@router.get("/top-posts", response_model=list[TopPost])
def get_top_posts(
    window: str = Query("24h", description="Time window: 1h, 24h, or 7d"),
    limit: int = Query(20, le=100, description="Maximum number of posts"),
    db: Session = Depends(get_db),
):
    """
    Get top posts by impact score.

    Returns posts ranked by engagement, sentiment, and recency.
    """
    # Parse window
    window_map = {"1h": 1, "24h": 24, "7d": 168}
    hours = window_map.get(window, 24)

    cutoff = datetime.utcnow() - timedelta(hours=hours)

    # Fetch posts from window
    posts = (
        db.query(Post)
        .filter(
            Post.created_utc >= cutoff,
            Post.sentiment.isnot(None),
        )
        .all()
    )

    # Calculate impact scores
    post_scores = []
    for post in posts:
        impact = calculate_impact_score(post)
        post_scores.append((post, impact))

    # Sort by impact
    post_scores.sort(key=lambda x: x[1], reverse=True)

    # Return top N
    top_posts = [
        TopPost(
            post_id=p.post_id,
            title=p.title,
            author=p.author,
            score=p.score,
            num_comments=p.num_comments,
            sentiment=p.sentiment,
            impact_score=impact,
            created_utc=p.created_utc,
            url=p.url,
        )
        for p, impact in post_scores[:limit]
    ]

    return top_posts


@router.get("/post/{post_id}", response_model=PostDetailResponse)
def get_post_detail(
    post_id: str = Path(..., description="Reddit post ID"),
    db: Session = Depends(get_db),
):
    """
    Get detailed post information with comments.

    Returns full post data including all comments and sentiment breakdown.
    """
    # Fetch post
    post = db.query(Post).filter(Post.post_id == post_id).first()

    if not post:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Post not found")

    # Fetch comments
    comments = (
        db.query(Comment)
        .filter(Comment.post_id == post_id)
        .order_by(Comment.score.desc())
        .all()
    )

    comment_list = [
        PostComment(
            comment_id=c.comment_id,
            author=c.author,
            body=c.body,
            score=c.score,
            sentiment=c.sentiment,
            created_utc=c.created_utc,
        )
        for c in comments
    ]

    # Sentiment breakdown
    bullish = sum(1 for c in comments if c.sentiment and c.sentiment > 0.2)
    bearish = sum(1 for c in comments if c.sentiment and c.sentiment < -0.2)
    neutral = len(comments) - bullish - bearish

    breakdown = {
        "bullish": bullish,
        "bearish": bearish,
        "neutral": neutral,
    }

    # Extract entities
    entities = []
    if post.entities and "entities" in post.entities:
        entities = post.entities["entities"]

    return PostDetailResponse(
        post_id=post.post_id,
        subreddit=post.subreddit,
        author=post.author,
        title=post.title,
        selftext=post.selftext,
        url=post.url,
        score=post.score,
        num_comments=post.num_comments,
        sentiment=post.sentiment,
        entities=entities,
        created_utc=post.created_utc,
        comments=comment_list,
        comment_sentiment_breakdown=breakdown,
    )
