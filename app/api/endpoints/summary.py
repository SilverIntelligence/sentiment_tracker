"""Summary API endpoint."""

import json
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.redis_client import cache_get, cache_set
from app.models import Post
from app.schemas.responses import PriceSummary, SentimentMetrics, SummaryResponse, TopPost
from app.workers.aggregation import compute_entity_window
from app.workers.prices import calculate_24h_change, get_latest_price

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/summary", response_model=SummaryResponse)
def get_summary(db: Session = Depends(get_db)):
    """
    Get current summary with prices, sentiment, and top posts.

    Returns high-level overview suitable for the Home tab.
    """
    # Check cache
    cache_key = "api:summary"
    cached = cache_get(cache_key)

    if cached:
        logger.debug("Returning cached summary")
        return json.loads(cached)

    # Fetch prices
    prices = {}
    for symbol in ["XAUUSD", "XAGUSD"]:
        latest = get_latest_price(db, symbol)
        if latest:
            change = calculate_24h_change(db, symbol)
            prices[symbol] = PriceSummary(
                symbol=symbol,
                price=latest.close,
                change_24h=change,
                timestamp=latest.timestamp,
            )

    # Compute sentiment for gold and silver across windows
    sentiment = {}
    windows = {"1h": 1, "24h": 24, "7d": 168}

    for entity in ["gold", "silver"]:
        sentiment[entity] = {}

        for window_name, hours in windows.items():
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)

            metrics = compute_entity_window(db, entity, start_time, end_time)

            sentiment[entity][window_name] = SentimentMetrics(
                entity=entity,
                mentions=metrics["mentions"],
                unique_authors=metrics["unique_authors"],
                mean_sentiment=metrics["mean_sentiment"],
                bull_ratio=metrics["bull_ratio"],
                index_value=metrics.get("index_value", 0.0),
            )

    # Get top posts from last 24h
    cutoff = datetime.utcnow() - timedelta(hours=24)

    posts = (
        db.query(Post)
        .filter(
            Post.created_utc >= cutoff,
            Post.sentiment.isnot(None),
        )
        .order_by((Post.score + Post.num_comments * 2).desc())
        .limit(10)
        .all()
    )

    top_posts = [
        TopPost(
            post_id=p.post_id,
            title=p.title,
            author=p.author,
            score=p.score,
            num_comments=p.num_comments,
            sentiment=p.sentiment,
            impact_score=p.score + p.num_comments * 2,
            created_utc=p.created_utc,
            url=p.url,
        )
        for p in posts
    ]

    response = SummaryResponse(
        prices=prices,
        sentiment=sentiment,
        top_posts=top_posts,
        timestamp=datetime.utcnow(),
    )

    # Cache for 30 seconds
    cache_set(cache_key, response.model_dump_json(), ttl=30)

    return response
