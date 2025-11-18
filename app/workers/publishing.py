"""Publishing worker jobs for posting threads and comments."""

import logging
from datetime import datetime, timedelta
from typing import Dict

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import SessionLocal
from app.reddit import RedditClient
from app.workers.aggregation import compute_entity_window
from app.workers.prices import calculate_24h_change, get_latest_price

logger = logging.getLogger(__name__)


def format_price(price: float) -> str:
    """Format price for display."""
    return f"${price:,.2f}"


def format_percentage(pct: float) -> str:
    """Format percentage with sign."""
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"


def generate_daily_digest() -> Dict:
    """
    Generate daily digest content.

    Returns:
        Dict with digest data
    """
    db = SessionLocal()

    try:
        # Get prices
        xau = get_latest_price(db, "XAUUSD")
        xag = get_latest_price(db, "XAGUSD")

        xau_change = calculate_24h_change(db, "XAUUSD")
        xag_change = calculate_24h_change(db, "XAGUSD")

        # Get 24h sentiment for gold and silver
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)

        gold_sentiment = compute_entity_window(db, "gold", start_time, end_time)
        silver_sentiment = compute_entity_window(db, "silver", start_time, end_time)

        return {
            "timestamp": datetime.utcnow(),
            "prices": {
                "gold": {
                    "price": xau.close if xau else 0,
                    "change_24h": xau_change or 0,
                },
                "silver": {
                    "price": xag.close if xag else 0,
                    "change_24h": xag_change or 0,
                },
            },
            "sentiment": {
                "gold": {
                    "mentions": gold_sentiment["mentions"],
                    "mean_sentiment": gold_sentiment["mean_sentiment"],
                    "bull_ratio": gold_sentiment["bull_ratio"],
                },
                "silver": {
                    "mentions": silver_sentiment["mentions"],
                    "mean_sentiment": silver_sentiment["mean_sentiment"],
                    "bull_ratio": silver_sentiment["bull_ratio"],
                },
            },
        }

    finally:
        db.close()


def format_daily_thread(digest: Dict) -> str:
    """
    Format daily thread post content.

    Args:
        digest: Digest data from generate_daily_digest()

    Returns:
        Markdown formatted thread content
    """
    prices = digest["prices"]
    sentiment = digest["sentiment"]

    # Format prices
    gold_price = format_price(prices["gold"]["price"])
    gold_change = format_percentage(prices["gold"]["change_24h"])

    silver_price = format_price(prices["silver"]["price"])
    silver_change = format_percentage(prices["silver"]["change_24h"])

    # Format sentiment
    gold_mentions = sentiment["gold"]["mentions"]
    gold_sent = sentiment["gold"]["mean_sentiment"]
    gold_bull = sentiment["gold"]["bull_ratio"] * 100

    silver_mentions = sentiment["silver"]["mentions"]
    silver_sent = sentiment["silver"]["mean_sentiment"]
    silver_bull = sentiment["silver"]["bull_ratio"] * 100

    # Sentiment emoji
    def sentiment_emoji(score: float) -> str:
        if score > 0.2:
            return "📈"
        elif score < -0.2:
            return "📉"
        else:
            return "📊"

    thread = f"""# Daily Precious Metals Discussion - {digest['timestamp'].strftime('%B %d, %Y')}

## Market Prices (24h)

**Gold (XAUUSD)**: {gold_price} ({gold_change}) {sentiment_emoji(gold_sent)}

**Silver (XAGUSD)**: {silver_price} ({silver_change}) {sentiment_emoji(silver_sent)}

---

## Community Sentiment (Last 24 Hours)

### 🥇 Gold
- **Mentions**: {gold_mentions}
- **Sentiment**: {gold_sent:.2f} ({sentiment_emoji(gold_sent)})
- **Bullish Ratio**: {gold_bull:.0f}%

### 🥈 Silver
- **Mentions**: {silver_mentions}
- **Sentiment**: {silver_sent:.2f} ({sentiment_emoji(silver_sent)})
- **Bullish Ratio**: {silver_bull:.0f}%

---

## Discussion

What's your take on today's precious metals market? Share your thoughts, DD, and positions below!

**Rules Reminder:**
- Be respectful and civil
- No spam or pump & dump
- Back up claims with sources when possible

---

*This is an automated daily thread. Sentiment data is computed from community posts and comments. Not financial advice.*
"""

    return thread


def post_daily_thread(subreddit: str = None) -> Dict:
    """
    Post daily discussion thread to subreddit.

    Args:
        subreddit: Subreddit to post to (defaults to first configured)

    Returns:
        Dict with post info
    """
    logger.info("Generating daily thread...")

    settings = get_settings()

    if not subreddit:
        if not settings.subreddit_list:
            logger.error("No subreddits configured")
            return {"status": "error", "message": "No subreddits configured"}
        subreddit = settings.subreddit_list[0]

    try:
        # Generate digest
        digest = generate_daily_digest()

        # Format thread
        title = f"Daily Precious Metals Discussion - {digest['timestamp'].strftime('%B %d, %Y')}"
        content = format_daily_thread(digest)

        # Post to Reddit
        client = RedditClient()
        sub = client.reddit.subreddit(subreddit)

        submission = sub.submit(title, selftext=content)

        # Sticky the post (requires mod permissions)
        try:
            submission.mod.sticky()
            logger.info(f"Stickied daily thread in r/{subreddit}")
        except Exception as e:
            logger.warning(f"Could not sticky post (might lack mod permissions): {e}")

        logger.info(f"Posted daily thread to r/{subreddit}: {submission.id}")

        return {
            "status": "success",
            "post_id": submission.id,
            "subreddit": subreddit,
            "title": title,
            "url": submission.url,
        }

    except Exception as e:
        logger.error(f"Error posting daily thread: {e}")
        return {"status": "error", "message": str(e)}


def generate_post_comment(post_id: str) -> str:
    """
    Generate sentiment comment for a post.

    Args:
        post_id: Reddit post ID

    Returns:
        Markdown formatted comment
    """
    db = SessionLocal()

    try:
        from app.models import Post

        # Get post
        post = db.query(Post).filter(Post.post_id == post_id).first()

        if not post:
            return None

        # Get entities mentioned
        entities = []
        if post.entities and "entities" in post.entities:
            entities = post.entities["entities"][:5]  # Top 5

        if not entities:
            return None

        # Build comment
        lines = ["**Sentiment Tracker Analysis**\n"]

        lines.append(f"**Post Sentiment**: {post.sentiment:.2f}")

        if entities:
            lines.append(f"\n**Entities Mentioned**: {', '.join(entities)}")

        # Get recent sentiment for mentioned entities
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)

        lines.append("\n**1h Community Sentiment**:")

        for entity in entities[:3]:  # Top 3 entities
            metrics = compute_entity_window(db, entity, start_time, end_time)

            if metrics["mentions"] > 0:
                lines.append(
                    f"- **{entity}**: {metrics['mean_sentiment']:.2f} "
                    f"({metrics['mentions']} mentions, {metrics['bull_ratio']*100:.0f}% bullish)"
                )

        lines.append(
            "\n\n---\n*^(Automated sentiment analysis. Not financial advice.)*"
        )

        return "\n".join(lines)

    finally:
        db.close()


def comment_on_post(post_id: str) -> Dict:
    """
    Post sentiment comment on a Reddit post.

    Args:
        post_id: Reddit post ID

    Returns:
        Dict with result
    """
    logger.info(f"Generating comment for post {post_id}...")

    try:
        # Generate comment
        comment_text = generate_post_comment(post_id)

        if not comment_text:
            logger.info(f"No comment needed for post {post_id}")
            return {"status": "skipped", "reason": "No entities or sentiment"}

        # Post comment
        client = RedditClient()
        submission = client.reddit.submission(id=post_id)

        comment = submission.reply(comment_text)

        logger.info(f"Posted comment on {post_id}: {comment.id}")

        return {
            "status": "success",
            "comment_id": comment.id,
            "post_id": post_id,
        }

    except Exception as e:
        logger.error(f"Error commenting on post {post_id}: {e}")
        return {"status": "error", "message": str(e)}
