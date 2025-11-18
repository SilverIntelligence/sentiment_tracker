"""Sentiment API endpoints."""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.responses import SentimentMetrics, SentimentResponse, SentimentSeriesPoint
from app.workers.aggregation import compute_entity_window

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/sentiment", response_model=SentimentResponse)
def get_sentiment(
    entity: str = Query(..., description="Entity name (e.g., 'gold', 'silver', 'SLV')"),
    window: str = Query("24h", description="Time window: 1h, 24h, or 7d"),
    db: Session = Depends(get_db),
):
    """
    Get sentiment metrics and time series for an entity.

    Returns rolling sentiment metrics over the specified window.
    """
    # Parse window
    window_map = {"1h": 1, "24h": 24, "7d": 168}
    hours = window_map.get(window, 24)

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)

    # Compute current metrics
    metrics = compute_entity_window(db, entity, start_time, end_time)

    current_metrics = SentimentMetrics(
        entity=entity,
        mentions=metrics["mentions"],
        unique_authors=metrics["unique_authors"],
        mean_sentiment=metrics["mean_sentiment"],
        bull_ratio=metrics["bull_ratio"],
        index_value=metrics.get("index_value", 0.0),
    )

    # For time series, compute hourly buckets
    series = []
    bucket_hours = 1 if hours <= 24 else 6  # 1h buckets for day, 6h for week

    current_bucket_end = end_time
    while current_bucket_end > start_time:
        bucket_start = current_bucket_end - timedelta(hours=bucket_hours)

        bucket_metrics = compute_entity_window(db, entity, bucket_start, current_bucket_end)

        if bucket_metrics["mentions"] > 0:
            series.append(
                SentimentSeriesPoint(
                    timestamp=bucket_start,
                    sentiment=bucket_metrics["mean_sentiment"],
                    mentions=bucket_metrics["mentions"],
                    bull_ratio=bucket_metrics["bull_ratio"],
                )
            )

        current_bucket_end = bucket_start

    # Reverse to chronological order
    series.reverse()

    return SentimentResponse(
        entity=entity,
        window=window,
        current_metrics=current_metrics,
        series=series,
    )
