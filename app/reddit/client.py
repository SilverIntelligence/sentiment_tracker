"""Reddit API client using PRAW."""

import logging
import time
from datetime import datetime, timedelta
from typing import Generator, List, Optional

import praw
from praw.models import Comment, Submission
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class RedditClient:
    """Reddit API client with rate limiting and error handling."""

    def __init__(self):
        """Initialize Reddit client."""
        settings = get_settings()

        if not all(
            [
                settings.reddit_client_id,
                settings.reddit_client_secret,
                settings.reddit_username,
                settings.reddit_password,
            ]
        ):
            logger.warning(
                "Reddit credentials not fully configured. Client may not work properly."
            )

        self.reddit = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            username=settings.reddit_username,
            password=settings.reddit_password,
            user_agent=settings.reddit_user_agent,
        )

        self.subreddits = settings.subreddit_list
        self.rate_limit_delay = 1.0  # 60 requests per minute = 1 request per second

        logger.info(f"Reddit client initialized for subreddits: {self.subreddits}")

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def get_new_posts(
        self, subreddit: str, limit: int = 100, since: Optional[datetime] = None
    ) -> List[Submission]:
        """
        Fetch new posts from a subreddit.

        Args:
            subreddit: Subreddit name
            limit: Maximum number of posts to fetch
            since: Only fetch posts after this timestamp

        Returns:
            List of submissions
        """
        try:
            logger.info(f"Fetching new posts from r/{subreddit} (limit={limit})")

            sub = self.reddit.subreddit(subreddit)
            posts = []

            for post in sub.new(limit=limit):
                # Check if post is newer than since timestamp
                if since:
                    post_time = datetime.fromtimestamp(post.created_utc)
                    if post_time <= since:
                        break

                posts.append(post)
                time.sleep(self.rate_limit_delay)

            logger.info(f"Fetched {len(posts)} posts from r/{subreddit}")
            return posts

        except Exception as e:
            logger.error(f"Error fetching posts from r/{subreddit}: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def get_post_by_id(self, post_id: str) -> Optional[Submission]:
        """
        Fetch a specific post by ID.

        Args:
            post_id: Reddit post ID

        Returns:
            Submission or None if not found
        """
        try:
            return self.reddit.submission(id=post_id)
        except Exception as e:
            logger.error(f"Error fetching post {post_id}: {e}")
            return None

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def get_comments(
        self, post_id: str, limit: Optional[int] = None
    ) -> List[Comment]:
        """
        Fetch comments from a post.

        Args:
            post_id: Reddit post ID
            limit: Maximum number of comments to fetch (None = all)

        Returns:
            List of comments
        """
        try:
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)  # Don't fetch "more comments"

            comments = []
            for comment in submission.comments.list():
                if isinstance(comment, Comment):
                    comments.append(comment)
                    if limit and len(comments) >= limit:
                        break

            logger.debug(f"Fetched {len(comments)} comments from post {post_id}")
            return comments

        except Exception as e:
            logger.error(f"Error fetching comments for post {post_id}: {e}")
            return []

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def get_recent_comments(
        self, subreddit: str, limit: int = 100
    ) -> List[Comment]:
        """
        Fetch recent comments from a subreddit.

        Args:
            subreddit: Subreddit name
            limit: Maximum number of comments to fetch

        Returns:
            List of comments
        """
        try:
            logger.info(f"Fetching recent comments from r/{subreddit} (limit={limit})")

            sub = self.reddit.subreddit(subreddit)
            comments = []

            for comment in sub.comments(limit=limit):
                if isinstance(comment, Comment):
                    comments.append(comment)
                time.sleep(self.rate_limit_delay)

            logger.info(f"Fetched {len(comments)} comments from r/{subreddit}")
            return comments

        except Exception as e:
            logger.error(f"Error fetching comments from r/{subreddit}: {e}")
            raise

    def get_all_new_posts(
        self, limit_per_sub: int = 100, since: Optional[datetime] = None
    ) -> Generator[Submission, None, None]:
        """
        Fetch new posts from all configured subreddits.

        Args:
            limit_per_sub: Maximum posts per subreddit
            since: Only fetch posts after this timestamp

        Yields:
            Submissions from all subreddits
        """
        for subreddit in self.subreddits:
            try:
                posts = self.get_new_posts(subreddit, limit=limit_per_sub, since=since)
                for post in posts:
                    yield post
            except Exception as e:
                logger.error(f"Error processing subreddit r/{subreddit}: {e}")
                continue

    def get_all_recent_comments(
        self, limit_per_sub: int = 100
    ) -> Generator[Comment, None, None]:
        """
        Fetch recent comments from all configured subreddits.

        Args:
            limit_per_sub: Maximum comments per subreddit

        Yields:
            Comments from all subreddits
        """
        for subreddit in self.subreddits:
            try:
                comments = self.get_recent_comments(subreddit, limit=limit_per_sub)
                for comment in comments:
                    yield comment
            except Exception as e:
                logger.error(f"Error processing subreddit r/{subreddit}: {e}")
                continue
