"""Application configuration."""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    environment: str = "development"
    log_level: str = "INFO"
    api_port: int = 8000
    app_name: str = "Sentiment Tracker"
    version: str = "1.0.0"

    # Database
    database_url: str = Field(
        default="postgresql://sentiment:sentiment@localhost:5432/sentiment_tracker"
    )
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Reddit API
    reddit_client_id: str = Field(default="")
    reddit_client_secret: str = Field(default="")
    reddit_username: str = Field(default="")
    reddit_password: str = Field(default="")
    reddit_user_agent: str = Field(default="sentiment_tracker/1.0")
    target_subreddits: str = Field(default="wallstreetsilver,gold,silverbugs")

    # Price APIs
    price_api_key: str = Field(default="")
    use_yahoo_finance: bool = True

    # Security
    secret_key: str = Field(default="change-me-in-production")
    admin_token: str = Field(default="admin-token")

    # Processing
    batch_size: int = 100
    ingestion_interval_posts: int = 60
    ingestion_interval_comments: int = 30

    # Caching
    cache_ttl_seconds: int = 60
    snapshot_ttl_seconds: int = 60

    # Retention
    raw_data_retention_days: int = 90

    @property
    def subreddit_list(self) -> List[str]:
        """Parse target subreddits into list."""
        return [s.strip() for s in self.target_subreddits.split(",") if s.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
