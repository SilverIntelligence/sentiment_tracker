"""Leaderboard API endpoints."""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.nlp.vocabulary import ENTITY_CATEGORIES
from app.schemas.responses import LeaderboardEntry, LeaderboardResponse
from app.workers.aggregation import compute_entity_window

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(
    bucket: str = Query("metals", description="Entity bucket: metals, etfs, miners, futures"),
    window: str = Query("7d", description="Time window: 1h, 24h, or 7d"),
    db: Session = Depends(get_db),
):
    """
    Get entity leaderboard for a category.

    Returns entities ranked by sentiment index within a category.
    """
    # Get entities for this bucket
    if bucket not in ENTITY_CATEGORIES:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=f"Invalid bucket: {bucket}")

    entities = ENTITY_CATEGORIES[bucket]

    # Parse window
    window_map = {"1h": 1, "24h": 24, "7d": 168}
    hours = window_map.get(window, 168)

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)

    # Compute metrics for each entity
    entity_metrics = []

    for entity in entities:
        metrics = compute_entity_window(db, entity, start_time, end_time)

        if metrics["mentions"] > 0:
            # Calculate sentiment index
            import numpy as np

            index = metrics["mean_sentiment"] * np.log1p(metrics["mentions"])

            entity_metrics.append(
                {
                    "entity": entity,
                    "mentions": metrics["mentions"],
                    "mean_sentiment": metrics["mean_sentiment"],
                    "index_value": index,
                }
            )

    # Sort by index value
    entity_metrics.sort(key=lambda x: x["index_value"], reverse=True)

    # Create leaderboard entries
    entries = [
        LeaderboardEntry(
            entity=m["entity"],
            rank=i + 1,
            mentions=m["mentions"],
            mean_sentiment=m["mean_sentiment"],
            index_value=m["index_value"],
        )
        for i, m in enumerate(entity_metrics)
    ]

    return LeaderboardResponse(
        bucket=bucket,
        window=window,
        entries=entries,
        timestamp=datetime.utcnow(),
    )
