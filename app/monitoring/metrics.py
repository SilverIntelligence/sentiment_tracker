"""Prometheus metrics for monitoring."""

from prometheus_client import Counter, Gauge, Histogram

# Ingestion metrics
ingestion_counter = Counter(
    "sentiment_tracker_ingestion_total",
    "Total number of items ingested",
    ["type", "status"],  # type=post/comment, status=created/updated/error
)

ingestion_duration = Histogram(
    "sentiment_tracker_ingestion_duration_seconds",
    "Time spent ingesting data",
    ["type"],
)

# NLP metrics
nlp_duration = Histogram(
    "sentiment_tracker_nlp_duration_seconds",
    "Time spent on NLP processing",
    ["stage"],  # stage=entity_extraction/sentiment_analysis
)

entity_extraction_counter = Counter(
    "sentiment_tracker_entities_extracted_total",
    "Total number of entities extracted",
    ["entity"],
)

# Price fetching metrics
price_fetch_counter = Counter(
    "sentiment_tracker_price_fetch_total",
    "Total number of price fetches",
    ["symbol", "status"],  # status=success/error
)

price_fetch_duration = Histogram(
    "sentiment_tracker_price_fetch_duration_seconds",
    "Time spent fetching prices",
    ["symbol"],
)

# API metrics
api_request_counter = Counter(
    "sentiment_tracker_api_requests_total",
    "Total API requests",
    ["endpoint", "method", "status"],
)

api_request_duration = Histogram(
    "sentiment_tracker_api_request_duration_seconds",
    "API request duration",
    ["endpoint"],
)

# Cache metrics
cache_hit_counter = Counter(
    "sentiment_tracker_cache_hits_total",
    "Total cache hits",
    ["key_prefix"],
)

cache_miss_counter = Counter(
    "sentiment_tracker_cache_misses_total",
    "Total cache misses",
    ["key_prefix"],
)

# Database metrics
db_query_duration = Histogram(
    "sentiment_tracker_db_query_duration_seconds",
    "Database query duration",
    ["operation"],
)

# Aggregation metrics
aggregation_duration = Histogram(
    "sentiment_tracker_aggregation_duration_seconds",
    "Time spent computing aggregates",
    ["window"],
)

entities_processed_gauge = Gauge(
    "sentiment_tracker_entities_processed",
    "Number of entities processed in last aggregation",
    ["window"],
)

# Sentiment metrics
sentiment_score_gauge = Gauge(
    "sentiment_tracker_sentiment_score",
    "Current sentiment score",
    ["entity", "window"],
)

mention_count_gauge = Gauge(
    "sentiment_tracker_mentions",
    "Number of mentions",
    ["entity", "window"],
)
