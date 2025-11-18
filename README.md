# Reddit Precious Metals Sentiment Tracker

A near-real-time sentiment tracking application for precious metals discussions on Reddit. Ingests posts and comments, extracts entities (gold, silver, miners, ETFs), computes sentiment scores, and surfaces insights through a Reddit App UI with leaderboards, charts, and market context.

## Features

- **Home Dashboard**: Current gold/silver prices, 24h change, sentiment heat bars, top posts
- **Sentiment Analysis**: Rolling 1h/24h/7d sentiment scores, mention volumes, bull/bear ratios
- **Post Leaderboards**: Posts/comments driving sentiment with impact scores
- **Market Context**: Price tiles for XAUUSD/XAGUSD, futures basis, volatility metrics
- **Admin Tools**: Manual reprocessing, blocklists, alert thresholds

## Architecture

- **Backend**: FastAPI + Python 3.11+
- **Database**: PostgreSQL 15+ (with optional TimescaleDB)
- **Cache/Queue**: Redis + RQ (Redis Queue)
- **NLP**: spaCy + VADER sentiment + custom rule layers
- **Ingestion**: PRAW (Reddit API) with rate limiting
- **Price Data**: Yahoo Finance or metals API
- **Deployment**: Docker + Fly.io/Render

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Reddit App credentials (script type)

### Setup

1. **Clone and configure**:
```bash
git clone <repo-url>
cd sentiment_tracker
cp .env.example .env
# Edit .env with your credentials
```

2. **Start services with Docker**:
```bash
docker-compose up -d
```

This starts:
- PostgreSQL on port 5432
- Redis on port 6379
- FastAPI web service on port 8000
- RQ worker for background jobs
- Scheduler for periodic tasks

3. **Access the API**:
```bash
curl http://localhost:8000
curl http://localhost:8000/healthz
```

### Local Development

1. **Install dependencies**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

2. **Run migrations**:
```bash
alembic upgrade head
```

3. **Start the API server**:
```bash
uvicorn app.main:app --reload
```

4. **Run worker (separate terminal)**:
```bash
python -m app.worker
```

5. **Run scheduler (separate terminal)**:
```bash
python -m app.scheduler
```

## Configuration

Edit `.env` or set environment variables:

### Required Settings

- `REDDIT_CLIENT_ID`: Your Reddit app client ID
- `REDDIT_CLIENT_SECRET`: Your Reddit app secret
- `REDDIT_USERNAME`: Reddit account username
- `REDDIT_PASSWORD`: Reddit account password
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string

### Optional Settings

- `TARGET_SUBREDDITS`: Comma-separated list of subreddits (default: wallstreetsilver,gold,silverbugs)
- `PRICE_API_KEY`: API key for price data (if not using Yahoo Finance)
- `CACHE_TTL_SECONDS`: Cache expiration in seconds (default: 60)
- `LOG_LEVEL`: Logging level (default: INFO)

## Database Schema

- `posts`: Reddit posts with entities and sentiment
- `comments`: Reddit comments with entities and sentiment
- `entities_daily`: Daily aggregates per entity (mentions, sentiment, bull ratio)
- `prices`: OHLCV price data for metals/instruments
- `snapshots`: Precomputed API responses for caching
- `admin_blocklist`: Admin-managed blocklists

## API Endpoints

### Public Endpoints

- `GET /`: Service info
- `GET /healthz`: Health check
- `GET /api/v1/summary`: Current summary (prices, sentiment, top posts)
- `GET /api/v1/sentiment?entity=xag&window=24h`: Sentiment time series
- `GET /api/v1/top-posts?window=24h&limit=20`: Top posts by impact
- `GET /api/v1/leaderboard?bucket=miners&window=7d`: Entity rankings
- `GET /api/v1/post/{id}`: Post details with comment sentiment

### Admin Endpoints

- `POST /api/v1/admin/blocklist`: Add/remove blocklist entries
- `POST /api/v1/admin/reprocess`: Manually reprocess content

## Development

### Code Quality

```bash
make format  # Format with black
make lint    # Lint with ruff + mypy
make test    # Run tests
```

### Database Migrations

```bash
make migrate msg="description"  # Create migration
make db-upgrade                 # Apply migrations
make db-downgrade              # Rollback migration
```

### Docker Commands

```bash
make docker-build  # Build images
make docker-up     # Start containers
make docker-down   # Stop containers
```

## NLP Pipeline

1. **Normalization**: Lowercase, strip URLs/code
2. **Filtering**: English, min karma/length, spam removal
3. **Entity Tagging**: Metals (gold/silver), instruments (ETFs/futures/miners)
4. **Sentiment Scoring**: VADER base + rule layer for directional verbs
5. **Aggregation**: Volume-weighted mean per entity per window

### Entities

- **Metals**: gold, xau, silver, xag, bullion, coins
- **ETFs**: SLV, GLD, PSLV, PHYS
- **Futures**: GC, SI
- **Miners**: PAAS, AG, AEM, NEM, MAG, HL, CDE

## Metrics

- **Sentiment Index**: `S_t = z(mean_sentiment) * log(1 + mentions)`
- **Divergence**: `D_t = z(Δsentiment_24h) - z(Δprice_24h)`
- **Attention Spike**: `A_t = mentions / EMA_7d(mentions)`
- **Bull/Bear Skew**: `P(compound > 0.5) / P(compound < -0.5)`
- **Post Impact**: `normalized_score * engagement * recency_decay`

## Worker Jobs

- `ingest_posts()`: Fetch new/updated posts
- `ingest_comments()`: Fetch new/updated comments
- `compute_windows()`: Compute 1h/24h/7d rollups
- `refresh_snapshots()`: Materialize API responses
- `price_pull()`: Fetch latest prices
- `daily_digest()`: Generate and post daily summary

## Testing

```bash
pytest tests/ -v
pytest tests/ --cov=app --cov-report=html
```

## Deployment

### Fly.io

```bash
fly launch
fly deploy
```

### Render

Connect GitHub repo and configure:
- Web Service: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Worker Service: `python -m app.worker`
- Scheduler Service: `python -m app.scheduler`

## Observability

- Prometheus metrics at `/metrics`
- Structured logging to stdout
- Health checks at `/healthz`

## License

AGPLv3 (server code with network use disclosure)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run `make format lint test`
5. Submit a pull request

## Support

For issues or questions, please open a GitHub issue.
