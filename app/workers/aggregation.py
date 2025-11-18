"""Aggregation worker jobs for computing entity metrics."""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List

import numpy as np
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models import Comment, EntityDaily, Post

logger = logging.getLogger(__name__)


def compute_entity_window(
    db: Session, entity: str, start_time: datetime, end_time: datetime
) -> Dict:
    """
    Compute sentiment metrics for an entity within a time window.

    Args:
        db: Database session
        entity: Entity name
        start_time: Window start time
        end_time: Window end time

    Returns:
        Dict with aggregated metrics
    """
    # Query posts mentioning this entity
    posts = (
        db.query(Post)
        .filter(
            and_(
                Post.created_utc >= start_time,
                Post.created_utc < end_time,
                Post.entities.isnot(None),
                Post.sentiment.isnot(None),
            )
        )
        .all()
    )

    # Filter posts that actually mention the entity
    relevant_posts = [
        p
        for p in posts
        if p.entities and entity.lower() in [e.lower() for e in p.entities.get("entities", [])]
    ]

    # Query comments mentioning this entity
    comments = (
        db.query(Comment)
        .filter(
            and_(
                Comment.created_utc >= start_time,
                Comment.created_utc < end_time,
                Comment.entities.isnot(None),
                Comment.sentiment.isnot(None),
            )
        )
        .all()
    )

    # Filter comments that actually mention the entity
    relevant_comments = [
        c
        for c in comments
        if c.entities
        and entity.lower() in [e.lower() for e in c.entities.get("entities", [])]
    ]

    # Combine mentions
    all_mentions = relevant_posts + relevant_comments

    if not all_mentions:
        return {
            "mentions": 0,
            "unique_authors": 0,
            "mean_sentiment": 0.0,
            "bull_ratio": 0.0,
            "top_posts": [],
        }

    # Calculate metrics
    sentiments = [m.sentiment for m in all_mentions if m.sentiment is not None]
    authors = set(m.author for m in all_mentions if m.author != "[deleted]")

    mean_sentiment = float(np.mean(sentiments)) if sentiments else 0.0
    bull_ratio = (
        sum(1 for s in sentiments if s > 0.2) / len(sentiments) if sentiments else 0.0
    )

    # Get top posts by engagement
    post_scores = [
        {"post_id": p.post_id, "score": p.score + p.num_comments * 2, "sentiment": p.sentiment}
        for p in relevant_posts
    ]
    post_scores.sort(key=lambda x: x["score"], reverse=True)
    top_posts = post_scores[:10]

    return {
        "mentions": len(all_mentions),
        "unique_authors": len(authors),
        "mean_sentiment": mean_sentiment,
        "bull_ratio": bull_ratio,
        "top_posts": top_posts,
    }


def compute_sentiment_index(mentions: int, mean_sentiment: float) -> float:
    """
    Compute sentiment index: S_t = z(mean_sentiment) * log(1 + mentions).

    For simplicity, we skip z-score normalization and use raw sentiment.

    Args:
        mentions: Number of mentions
        mean_sentiment: Mean sentiment score

    Returns:
        Sentiment index value
    """
    if mentions == 0:
        return 0.0

    # Simple version: sentiment * log(1 + mentions)
    # In production, you'd normalize sentiment using historical z-scores
    return mean_sentiment * np.log1p(mentions)


def compute_daily_aggregates(target_date: date = None) -> Dict:
    """
    Compute daily aggregates for all entities.

    Args:
        target_date: Date to compute (defaults to yesterday)

    Returns:
        Dict with computation statistics
    """
    if target_date is None:
        target_date = (datetime.utcnow() - timedelta(days=1)).date()

    logger.info(f"Computing daily aggregates for {target_date}")

    db = SessionLocal()

    try:
        # Define time window (full day)
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = start_time + timedelta(days=1)

        # Get all unique entities from posts and comments in this window
        entities = set()

        # Get entities from posts
        posts = (
            db.query(Post)
            .filter(
                and_(
                    Post.created_utc >= start_time,
                    Post.created_utc < end_time,
                    Post.entities.isnot(None),
                )
            )
            .all()
        )

        for post in posts:
            if post.entities and "entities" in post.entities:
                entities.update(post.entities["entities"])

        # Get entities from comments
        comments = (
            db.query(Comment)
            .filter(
                and_(
                    Comment.created_utc >= start_time,
                    Comment.created_utc < end_time,
                    Comment.entities.isnot(None),
                )
            )
            .all()
        )

        for comment in comments:
            if comment.entities and "entities" in comment.entities:
                entities.update(comment.entities["entities"])

        logger.info(f"Found {len(entities)} unique entities for {target_date}")

        # Compute metrics for each entity
        entities_processed = 0

        for entity in entities:
            try:
                metrics = compute_entity_window(db, entity, start_time, end_time)

                if metrics["mentions"] == 0:
                    continue

                # Calculate sentiment index
                index_value = compute_sentiment_index(
                    metrics["mentions"], metrics["mean_sentiment"]
                )

                # Check if record exists
                existing = (
                    db.query(EntityDaily)
                    .filter(
                        and_(EntityDaily.dt == target_date, EntityDaily.entity == entity)
                    )
                    .first()
                )

                data = {
                    "dt": target_date,
                    "entity": entity,
                    "mentions": metrics["mentions"],
                    "unique_authors": metrics["unique_authors"],
                    "mean_sentiment": metrics["mean_sentiment"],
                    "bull_ratio": metrics["bull_ratio"],
                    "index_value": index_value,
                    "top_posts": metrics["top_posts"],
                }

                if existing:
                    # Update
                    for key, value in data.items():
                        setattr(existing, key, value)
                else:
                    # Create
                    record = EntityDaily(**data)
                    db.add(record)

                entities_processed += 1

            except Exception as e:
                logger.error(f"Error processing entity {entity}: {e}")
                continue

        db.commit()

        stats = {
            "target_date": str(target_date),
            "entities_processed": entities_processed,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"Daily aggregates complete: {entities_processed} entities processed")
        return stats

    except Exception as e:
        logger.error(f"Error during daily aggregation: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def compute_hourly_aggregates(hours: int = 1) -> Dict:
    """
    Compute rolling hourly aggregates.

    Args:
        hours: Number of hours to aggregate (1, 24, 168 for 7 days)

    Returns:
        Dict with computation statistics
    """
    logger.info(f"Computing {hours}h rolling aggregates")

    db = SessionLocal()

    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        # Get unique entities
        entities = set()

        posts = (
            db.query(Post)
            .filter(
                and_(
                    Post.created_utc >= start_time,
                    Post.entities.isnot(None),
                )
            )
            .all()
        )

        for post in posts:
            if post.entities and "entities" in post.entities:
                entities.update(post.entities["entities"])

        comments = (
            db.query(Comment)
            .filter(
                and_(
                    Comment.created_utc >= start_time,
                    Comment.entities.isnot(None),
                )
            )
            .all()
        )

        for comment in comments:
            if comment.entities and "entities" in comment.entities:
                entities.update(comment.entities["entities"])

        # Compute metrics for each entity
        results = {}

        for entity in entities:
            try:
                metrics = compute_entity_window(db, entity, start_time, end_time)
                if metrics["mentions"] > 0:
                    results[entity] = metrics
            except Exception as e:
                logger.error(f"Error processing entity {entity}: {e}")
                continue

        logger.info(f"{hours}h aggregates complete: {len(results)} entities")

        return {
            "window_hours": hours,
            "entities_count": len(results),
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error during hourly aggregation: {e}")
        raise
    finally:
        db.close()
