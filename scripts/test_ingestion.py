#!/usr/bin/env python3
"""Test script for Reddit ingestion."""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.db.database import init_db
from app.reddit import RedditClient
from app.workers.ingestion import ingest_comments, ingest_posts

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_reddit_connection():
    """Test Reddit API connection."""
    logger.info("Testing Reddit API connection...")

    try:
        client = RedditClient()
        settings = get_settings()

        # Test fetching a post from the first configured subreddit
        if not settings.subreddit_list:
            logger.error("No subreddits configured in TARGET_SUBREDDITS")
            return False

        subreddit = settings.subreddit_list[0]
        logger.info(f"Fetching test posts from r/{subreddit}...")

        posts = client.get_new_posts(subreddit, limit=5)

        if posts:
            logger.info(f"✓ Successfully fetched {len(posts)} posts")
            logger.info(f"  Example post: {posts[0].title[:50]}...")
            return True
        else:
            logger.warning("No posts fetched (subreddit might be empty)")
            return True

    except Exception as e:
        logger.error(f"✗ Reddit API connection failed: {e}")
        return False


def test_database_connection():
    """Test database connection."""
    logger.info("Testing database connection...")

    try:
        init_db()
        logger.info("✓ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False


def test_ingestion():
    """Test ingestion pipeline."""
    logger.info("Testing ingestion pipeline...")

    try:
        # Test post ingestion
        logger.info("Testing post ingestion...")
        post_stats = ingest_posts(limit=10)
        logger.info(f"✓ Post ingestion successful: {post_stats}")

        # Test comment ingestion
        logger.info("Testing comment ingestion...")
        comment_stats = ingest_comments(limit=10)
        logger.info(f"✓ Comment ingestion successful: {comment_stats}")

        return True

    except Exception as e:
        logger.error(f"✗ Ingestion failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Reddit Sentiment Tracker - Ingestion Test")
    logger.info("=" * 60)

    results = []

    # Test 1: Database connection
    results.append(("Database Connection", test_database_connection()))

    # Test 2: Reddit API connection
    results.append(("Reddit API Connection", test_reddit_connection()))

    # Test 3: Full ingestion pipeline
    results.append(("Ingestion Pipeline", test_ingestion()))

    # Print summary
    logger.info("=" * 60)
    logger.info("Test Summary:")
    logger.info("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {name}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        logger.info("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        logger.error("\n❌ Some tests failed. Please check your configuration.")
        sys.exit(1)


if __name__ == "__main__":
    main()
