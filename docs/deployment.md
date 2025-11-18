# Deployment Guide

## Prerequisites

- Docker and Docker Compose
- Reddit App credentials (script type)
- PostgreSQL database (or use Docker)
- Redis instance (or use Docker)

## Environment Setup

1. **Clone the repository**:
```bash
git clone <repo-url>
cd sentiment_tracker
```

2. **Configure environment**:
```bash
cp .env.example .env
```

Edit `.env` and set:
- `REDDIT_CLIENT_ID`: Your Reddit app client ID
- `REDDIT_CLIENT_SECRET`: Your Reddit app secret
- `REDDIT_USERNAME`: Your Reddit username
- `REDDIT_PASSWORD`: Your Reddit password
- `TARGET_SUBREDDITS`: Comma-separated list of subreddits to monitor
- `SECRET_KEY`: Random secret key for security
- `ADMIN_TOKEN`: Token for admin API access

3. **Build and start services**:
```bash
docker-compose up -d
```

This starts:
- PostgreSQL database
- Redis cache
- FastAPI web service (port 8000)
- RQ worker for background jobs
- Scheduler for periodic tasks

4. **Run database migrations**:
```bash
docker-compose exec web alembic upgrade head
```

5. **Verify services**:
```bash
curl http://localhost:8000/healthz
```

## Production Deployment

### Fly.io

1. **Install Fly CLI**:
```bash
curl -L https://fly.io/install.sh | sh
```

2. **Login and launch**:
```bash
fly auth login
fly launch
```

3. **Set secrets**:
```bash
fly secrets set REDDIT_CLIENT_ID=xxx
fly secrets set REDDIT_CLIENT_SECRET=xxx
fly secrets set REDDIT_USERNAME=xxx
fly secrets set REDDIT_PASSWORD=xxx
fly secrets set SECRET_KEY=$(openssl rand -hex 32)
fly secrets set ADMIN_TOKEN=$(openssl rand -hex 16)
```

4. **Add Postgres**:
```bash
fly postgres create
fly postgres attach <postgres-app-name>
```

5. **Add Redis**:
```bash
fly redis create
```

6. **Deploy**:
```bash
fly deploy
```

7. **Run migrations**:
```bash
fly ssh console
alembic upgrade head
```

### Render

1. **Create Web Service**:
- Connect GitHub repo
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Add environment variables

2. **Create Worker Service**:
- Same repo
- Start command: `python -m app.worker`

3. **Create Scheduler Service**:
- Same repo
- Start command: `python -m app.scheduler`

4. **Add PostgreSQL**:
- Create PostgreSQL database
- Copy connection string to `DATABASE_URL`

5. **Add Redis**:
- Create Redis instance
- Copy connection string to `REDIS_URL`

## Monitoring

### Prometheus Metrics

Metrics are exposed at `/metrics`:

```bash
curl http://localhost:8000/metrics
```

Key metrics:
- `sentiment_tracker_ingestion_total`: Posts/comments ingested
- `sentiment_tracker_price_fetch_total`: Price data fetches
- `sentiment_tracker_api_requests_total`: API requests
- `sentiment_tracker_sentiment_score`: Current sentiment scores
- `sentiment_tracker_mentions`: Entity mention counts

### Grafana Dashboard

1. **Add Prometheus data source**:
   - URL: Your Prometheus server
   - Access: Server (default)

2. **Import dashboard**:
   - Use the provided `grafana_dashboard.json`
   - Or create custom panels for key metrics

3. **Key panels**:
   - Ingestion rate (posts/comments per minute)
   - Sentiment trends (gold/silver over time)
   - API request rate and latency
   - Cache hit rate
   - Entity mention volume

### Health Checks

The `/healthz` endpoint checks:
- Database connectivity
- Redis connectivity
- Recent ingestion activity

Set up monitoring to alert on unhealthy status.

### Logs

Structured JSON logs are written to stdout:

```bash
# View logs (Docker)
docker-compose logs -f web

# View logs (Fly.io)
fly logs

# View logs (Render)
# Check service logs in dashboard
```

## Scaling

### Horizontal Scaling

**Web Service**:
- Multiple instances behind load balancer
- Stateless design allows easy scaling
- API responses cached in Redis

**Workers**:
- Run multiple worker instances
- RQ handles job distribution
- Scale based on queue depth

**Database**:
- Use read replicas for queries
- Write to primary only
- Connection pooling (configured in `database.py`)

### Vertical Scaling

- Increase CPU/RAM for workers processing NLP
- Larger database instance for heavy query loads
- Redis with more memory for caching

## Backups

### Database

```bash
# Manual backup
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql
```

### Automated Backups

- Fly.io: Automatic daily backups
- Render: Configure backup schedule
- AWS RDS: Enable automated backups

## Troubleshooting

### High Memory Usage

- Reduce `BATCH_SIZE` for ingestion
- Decrease worker concurrency
- Check for memory leaks in NLP pipeline

### Slow API Responses

- Verify Redis cache is working
- Check database query performance
- Review Prometheus metrics for bottlenecks

### Ingestion Lag

- Increase worker instances
- Reduce `INGESTION_INTERVAL_*` settings
- Check Reddit API rate limits

### Missing Data

- Verify Reddit credentials
- Check worker logs for errors
- Ensure database migrations are current

## Security

### API Authentication

Admin endpoints require Bearer token:

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/api/v1/admin/blocklist
```

### Database Security

- Use strong passwords
- Enable SSL/TLS for connections
- Restrict network access
- Regular security updates

### Reddit API

- Keep credentials secure
- Use environment variables
- Rotate tokens regularly
- Monitor for unauthorized usage

## Performance Tuning

### Database

```sql
-- Add indexes for common queries
CREATE INDEX idx_posts_entities_gin ON posts USING GIN(entities);
CREATE INDEX idx_posts_created_sentiment ON posts(created_utc, sentiment);

-- Analyze query plans
EXPLAIN ANALYZE SELECT ...;
```

### Caching

Adjust cache TTL in `.env`:
```
CACHE_TTL_SECONDS=60
SNAPSHOT_TTL_SECONDS=30
```

### Workers

Configure RQ worker count:
```bash
# Run multiple workers
rq worker high default low --burst &
rq worker high default low --burst &
rq worker high default low --burst &
```

## Maintenance

### Database Cleanup

Remove old data:
```sql
DELETE FROM posts WHERE created_utc < NOW() - INTERVAL '90 days';
DELETE FROM comments WHERE created_utc < NOW() - INTERVAL '90 days';
```

### Cache Cleanup

Redis keys expire automatically. To flush manually:
```bash
redis-cli FLUSHDB
```

### Updates

```bash
git pull
docker-compose build
docker-compose up -d
alembic upgrade head
```
