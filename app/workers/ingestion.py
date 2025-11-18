"""Reddit ingestion worker jobs."""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.redis_client import get_redis
from app.models import Comment as CommentModel
from app.models import Post as PostModel
from app.reddit import RedditClient

logger = logging.getLogger(__name__)


def get_last_ingestion_time(key: str) -> Optional[datetime]:
    """Get the last ingestion timestamp from Redis."""
    r = get_redis()
    timestamp_str = r.get(key)
    if timestamp_str:
        return datetime.fromisoformat(timestamp_str)
    return None


def set_last_ingestion_time(key: str, timestamp: datetime) -> None:
    """Save the last ingestion timestamp to Redis."""
    r = get_redis()
    r.set(key, timestamp.isoformat())


def upsert_post(db: Session, submission) -> PostModel:
    """
    Insert or update a post in the database.

    Args:
        db: Database session
        submission: PRAW submission object

    Returns:
        PostModel instance
    """
    post_id = submission.id

    # Check if post exists
    existing = db.query(PostModel).filter(PostModel.post_id == post_id).first()

    post_data = {
        "post_id": post_id,
        "subreddit": submission.subreddit.display_name,
        "author": str(submission.author) if submission.author else "[deleted]",
        "created_utc": datetime.fromtimestamp(submission.created_utc),
        "title": submission.title,
        "selftext": submission.selftext if submission.is_self else None,
        "score": submission.score,
        "num_comments": submission.num_comments,
        "url": submission.url,
        "is_self": submission.is_self,
        "removed": submission.removed_by_category is not None,
    }

    if existing:
        # Update existing post
        for key, value in post_data.items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        logger.debug(f"Updated post {post_id}")
        return existing
    else:
        # Create new post
        post = PostModel(**post_data)
        db.add(post)
        db.commit()
        db.refresh(post)
        logger.debug(f"Created post {post_id}")
        return post


def upsert_comment(db: Session, comment_obj, post_id: str) -> CommentModel:
    """
    Insert or update a comment in the database.

    Args:
        db: Database session
        comment_obj: PRAW comment object
        post_id: Parent post ID

    Returns:
        CommentModel instance
    """
    comment_id = comment_obj.id

    # Check if comment exists
    existing = (
        db.query(CommentModel).filter(CommentModel.comment_id == comment_id).first()
    )

    comment_data = {
        "comment_id": comment_id,
        "post_id": post_id,
        "author": str(comment_obj.author) if comment_obj.author else "[deleted]",
        "created_utc": datetime.fromtimestamp(comment_obj.created_utc),
        "body": comment_obj.body,
        "score": comment_obj.score,
    }

    if existing:
        # Update existing comment
        for key, value in comment_data.items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        logger.debug(f"Updated comment {comment_id}")
        return existing
    else:
        # Create new comment
        comment = CommentModel(**comment_data)
        db.add(comment)
        db.commit()
        db.refresh(comment)
        logger.debug(f"Created comment {comment_id}")
        return comment


def ingest_posts(limit: int = 100) -> dict:
    """
    Ingest new posts from Reddit.

    Args:
        limit: Maximum posts to fetch per subreddit

    Returns:
        Dict with ingestion statistics
    """
    logger.info(f"Starting post ingestion (limit={limit})")

    client = RedditClient()
    db = SessionLocal()

    try:
        # Get last ingestion time
        since = get_last_ingestion_time("last_post_ingestion")
        logger.info(f"Last post ingestion: {since}")

        posts_processed = 0
        posts_created = 0
        posts_updated = 0
        latest_timestamp = since

        # Fetch posts from all subreddits
        for submission in client.get_all_new_posts(limit_per_sub=limit, since=since):
            try:
                # Determine if this is a new post
                existing = (
                    db.query(PostModel)
                    .filter(PostModel.post_id == submission.id)
                    .first()
                )
                is_new = existing is None

                # Upsert post
                upsert_post(db, submission)

                if is_new:
                    posts_created += 1
                else:
                    posts_updated += 1

                posts_processed += 1

                # Track latest timestamp
                post_time = datetime.fromtimestamp(submission.created_utc)
                if not latest_timestamp or post_time > latest_timestamp:
                    latest_timestamp = post_time

            except Exception as e:
                logger.error(f"Error processing post {submission.id}: {e}")
                continue

        # Update last ingestion time
        if latest_timestamp:
            set_last_ingestion_time("last_post_ingestion", latest_timestamp)

        stats = {
            "posts_processed": posts_processed,
            "posts_created": posts_created,
            "posts_updated": posts_updated,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Post ingestion complete: {posts_created} created, {posts_updated} updated"
        )
        return stats

    except Exception as e:
        logger.error(f"Error during post ingestion: {e}")
        raise
    finally:
        db.close()


def ingest_comments(limit: int = 100) -> dict:
    """
    Ingest recent comments from Reddit.

    Args:
        limit: Maximum comments to fetch per subreddit

    Returns:
        Dict with ingestion statistics
    """
    logger.info(f"Starting comment ingestion (limit={limit})")

    client = RedditClient()
    db = SessionLocal()

    try:
        comments_processed = 0
        comments_created = 0
        comments_updated = 0

        # Fetch comments from all subreddits
        for comment_obj in client.get_all_recent_comments(limit_per_sub=limit):
            try:
                # Get or create parent post
                post_id = comment_obj.submission.id

                # Check if parent post exists
                parent_post = (
                    db.query(PostModel).filter(PostModel.post_id == post_id).first()
                )

                if not parent_post:
                    # Fetch and create parent post
                    logger.debug(
                        f"Parent post {post_id} not found, fetching from Reddit"
                    )
                    submission = client.get_post_by_id(post_id)
                    if submission:
                        upsert_post(db, submission)
                    else:
                        logger.warning(
                            f"Could not fetch parent post {post_id}, skipping comment"
                        )
                        continue

                # Determine if this is a new comment
                existing = (
                    db.query(CommentModel)
                    .filter(CommentModel.comment_id == comment_obj.id)
                    .first()
                )
                is_new = existing is None

                # Upsert comment
                upsert_comment(db, comment_obj, post_id)

                if is_new:
                    comments_created += 1
                else:
                    comments_updated += 1

                comments_processed += 1

            except Exception as e:
                logger.error(f"Error processing comment {comment_obj.id}: {e}")
                continue

        stats = {
            "comments_processed": comments_processed,
            "comments_created": comments_created,
            "comments_updated": comments_updated,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Comment ingestion complete: {comments_created} created, {comments_updated} updated"
        )
        return stats

    except Exception as e:
        logger.error(f"Error during comment ingestion: {e}")
        raise
    finally:
        db.close()


def backfill_comments_for_post(post_id: str) -> dict:
    """
    Backfill all comments for a specific post.

    Args:
        post_id: Reddit post ID

    Returns:
        Dict with ingestion statistics
    """
    logger.info(f"Backfilling comments for post {post_id}")

    client = RedditClient()
    db = SessionLocal()

    try:
        comments_processed = 0
        comments_created = 0
        comments_updated = 0

        # Fetch all comments for the post
        comments = client.get_comments(post_id)

        for comment_obj in comments:
            try:
                # Determine if this is a new comment
                existing = (
                    db.query(CommentModel)
                    .filter(CommentModel.comment_id == comment_obj.id)
                    .first()
                )
                is_new = existing is None

                # Upsert comment
                upsert_comment(db, comment_obj, post_id)

                if is_new:
                    comments_created += 1
                else:
                    comments_updated += 1

                comments_processed += 1

            except Exception as e:
                logger.error(f"Error processing comment {comment_obj.id}: {e}")
                continue

        stats = {
            "post_id": post_id,
            "comments_processed": comments_processed,
            "comments_created": comments_created,
            "comments_updated": comments_updated,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Comment backfill complete for {post_id}: {comments_created} created, {comments_updated} updated"
        )
        return stats

    except Exception as e:
        logger.error(f"Error during comment backfill for {post_id}: {e}")
        raise
    finally:
        db.close()
