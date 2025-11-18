"""Response schemas for API endpoints."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PriceSummary(BaseModel):
    """Price summary for an asset."""

    symbol: str
    price: float
    change_24h: Optional[float] = None
    timestamp: datetime


class SentimentMetrics(BaseModel):
    """Sentiment metrics for an entity."""

    entity: str
    mentions: int
    unique_authors: int
    mean_sentiment: float
    bull_ratio: float
    index_value: float


class SentimentWindow(BaseModel):
    """Sentiment for a specific time window."""

    window: str  # "1h", "24h", "7d"
    metrics: SentimentMetrics


class TopPost(BaseModel):
    """Top post summary."""

    post_id: str
    title: str
    author: str
    score: int
    num_comments: int
    sentiment: Optional[float]
    impact_score: float
    created_utc: datetime
    url: str


class SummaryResponse(BaseModel):
    """Summary endpoint response."""

    prices: Dict[str, PriceSummary]
    sentiment: Dict[str, Dict[str, SentimentMetrics]]  # entity -> window -> metrics
    top_posts: List[TopPost]
    timestamp: datetime


class SentimentSeriesPoint(BaseModel):
    """Single point in sentiment time series."""

    timestamp: datetime
    sentiment: float
    mentions: int
    bull_ratio: float


class SentimentResponse(BaseModel):
    """Sentiment endpoint response."""

    entity: str
    window: str
    current_metrics: SentimentMetrics
    series: List[SentimentSeriesPoint]


class LeaderboardEntry(BaseModel):
    """Leaderboard entry for an entity."""

    entity: str
    rank: int
    mentions: int
    mean_sentiment: float
    index_value: float
    change_vs_previous: Optional[float] = None


class LeaderboardResponse(BaseModel):
    """Leaderboard endpoint response."""

    bucket: str  # "metals", "etfs", "miners"
    window: str  # "1h", "24h", "7d"
    entries: List[LeaderboardEntry]
    timestamp: datetime


class PostComment(BaseModel):
    """Comment on a post."""

    comment_id: str
    author: str
    body: str
    score: int
    sentiment: Optional[float]
    created_utc: datetime


class PostDetailResponse(BaseModel):
    """Post detail endpoint response."""

    post_id: str
    subreddit: str
    author: str
    title: str
    selftext: Optional[str]
    url: str
    score: int
    num_comments: int
    sentiment: Optional[float]
    entities: List[str]
    created_utc: datetime
    comments: List[PostComment]
    comment_sentiment_breakdown: Dict[str, int]  # "bullish", "bearish", "neutral"


class BlocklistEntry(BaseModel):
    """Blocklist entry."""

    id: str
    type: str
    value: str
    reason: Optional[str]
    added_by: str
    added_at: datetime


class BlocklistResponse(BaseModel):
    """Blocklist endpoint response."""

    entries: List[BlocklistEntry]
    total: int
