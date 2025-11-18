# Deployment Checklist

Use this checklist to ensure a successful deployment of the Sentiment Tracker.

## ✅ Pre-Deployment Validation

### 1. Code Validation
- [x] All pre-flight checks passed (`python scripts/preflight_check.py`)
- [x] File structure complete
- [x] Dependencies listed in requirements.txt
- [x] Docker Compose configuration valid
- [x] All API endpoints present

### 2. Environment Configuration
- [ ] Copy `.env.example` to `.env`
  ```bash
  cp .env.example .env
  ```

- [ ] Configure Reddit API credentials:
  - [ ] `REDDIT_CLIENT_ID` (from https://www.reddit.com/prefs/apps)
  - [ ] `REDDIT_CLIENT_SECRET`
  - [ ] `REDDIT_USERNAME`
  - [ ] `REDDIT_PASSWORD`
  - [ ] `REDDIT_USER_AGENT` (default is fine)

- [ ] Configure target subreddits:
  - [ ] `TARGET_SUBREDDITS` (comma-separated list)

- [ ] Generate secure secrets:
  ```bash
  # Generate SECRET_KEY
  openssl rand -hex 32

  # Generate ADMIN_TOKEN
  openssl rand -hex 16
  ```
  - [ ] `SECRET_KEY` (paste generated value)
  - [ ] `ADMIN_TOKEN` (paste generated value)

- [ ] Review optional settings:
  - [ ] `LOG_LEVEL` (default: INFO)
  - [ ] `BATCH_SIZE` (default: 100)
  - [ ] `CACHE_TTL_SECONDS` (default: 60)

### 3. Local Validation
- [ ] Pull latest code:
  ```bash
  git pull origin claude/reddit-metals-sentiment-app-01PmT4tvZqmbLMRManqVwHKC
  ```

- [ ] Run validation script:
  ```bash
  ./scripts/validate_deployment.sh
  ```

- [ ] Verify all services started:
  ```bash
  docker-compose ps
  ```
  Expected services: postgres, redis, web, worker, scheduler

### 4. Health Checks
- [ ] API health endpoint:
  ```bash
  curl http://localhost:8000/healthz
  ```
  Expected: `{"status":"healthy","redis":"connected","database":"connected"}`

- [ ] Root endpoint:
  ```bash
  curl http://localhost:8000/
  ```
  Expected: `{"app":"Sentiment Tracker","version":"1.0.0","status":"running"}`

- [ ] Metrics endpoint:
  ```bash
  curl http://localhost:8000/metrics | grep sentiment_tracker
  ```
  Expected: Multiple Prometheus metrics

- [ ] API summary:
  ```bash
  curl http://localhost:8000/api/v1/summary
  ```
  Expected: JSON with prices, sentiment, top_posts

### 5. Functional Tests
- [ ] Test Reddit ingestion (requires valid credentials):
  ```bash
  docker-compose exec web python scripts/test_ingestion.py
  ```

- [ ] Test NLP pipeline:
  ```bash
  docker-compose exec web python scripts/test_nlp.py
  ```

- [ ] Test price fetching:
  ```bash
  docker-compose exec web python scripts/test_prices.py
  ```

- [ ] Test daily thread generation:
  ```bash
  docker-compose exec web python scripts/test_publish.py
  ```

### 6. Database Validation
- [ ] Run migrations:
  ```bash
  docker-compose exec web alembic upgrade head
  ```

- [ ] Verify tables created:
  ```bash
  docker-compose exec postgres psql -U sentiment -d sentiment_tracker -c "\dt"
  ```
  Expected tables: posts, comments, entities_daily, prices, snapshots, admin_blocklist

- [ ] Check indexes:
  ```bash
  docker-compose exec postgres psql -U sentiment -d sentiment_tracker -c "\di"
  ```

### 7. Worker Validation
- [ ] Check worker logs:
  ```bash
  docker-compose logs worker
  ```
  Expected: "Worker listening on queues: ['default', 'high', 'low']"

- [ ] Check scheduler logs:
  ```bash
  docker-compose logs scheduler
  ```
  Expected: "Jobs scheduled successfully"

- [ ] Verify Redis queue:
  ```bash
  docker-compose exec redis redis-cli KEYS "*"
  ```

### 8. Monitoring Setup
- [ ] Access API documentation:
  - http://localhost:8000/docs (Swagger UI)
  - http://localhost:8000/redoc (ReDoc)

- [ ] Verify Prometheus metrics:
  - http://localhost:8000/metrics

- [ ] Review logs for errors:
  ```bash
  docker-compose logs -f web | grep -i error
  ```

## 🚀 Production Deployment

### Option A: Fly.io

1. [ ] Install Fly CLI:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. [ ] Login and initialize:
   ```bash
   fly auth login
   fly launch --no-deploy
   ```

3. [ ] Create Postgres database:
   ```bash
   fly postgres create
   fly postgres attach <postgres-app-name>
   ```

4. [ ] Create Redis instance:
   ```bash
   fly redis create
   ```

5. [ ] Set secrets:
   ```bash
   fly secrets set REDDIT_CLIENT_ID=xxx \
     REDDIT_CLIENT_SECRET=xxx \
     REDDIT_USERNAME=xxx \
     REDDIT_PASSWORD=xxx \
     SECRET_KEY=xxx \
     ADMIN_TOKEN=xxx \
     TARGET_SUBREDDITS=wallstreetsilver,gold,silverbugs
   ```

6. [ ] Deploy application:
   ```bash
   fly deploy
   ```

7. [ ] Run migrations:
   ```bash
   fly ssh console
   alembic upgrade head
   exit
   ```

8. [ ] Verify deployment:
   ```bash
   fly status
   fly logs
   ```

### Option B: Render

1. [ ] Connect GitHub repository to Render

2. [ ] Create PostgreSQL database:
   - Plan: Starter ($7/month minimum)
   - Note connection string

3. [ ] Create Redis instance:
   - Plan: Starter (free tier available)
   - Note connection string

4. [ ] Create Web Service:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Add environment variables from `.env.example`

5. [ ] Create Worker Service:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python -m app.worker`
   - Use same environment variables

6. [ ] Create Scheduler Service:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python -m app.scheduler`
   - Use same environment variables

7. [ ] Run migrations (via Web Service shell):
   ```bash
   alembic upgrade head
   ```

## 📊 Post-Deployment Verification

### 1. Service Health
- [ ] All services are "healthy" status
- [ ] No errors in logs (past 10 minutes)
- [ ] CPU usage < 50%
- [ ] Memory usage < 80%
- [ ] Database connections stable

### 2. Data Flow
- [ ] Posts being ingested (check `posts` table)
  ```sql
  SELECT COUNT(*), MAX(created_utc) FROM posts;
  ```

- [ ] Comments being ingested (check `comments` table)
  ```sql
  SELECT COUNT(*), MAX(created_utc) FROM comments;
  ```

- [ ] Entities being extracted (check posts.entities)
  ```sql
  SELECT entities FROM posts WHERE entities IS NOT NULL LIMIT 10;
  ```

- [ ] Prices being updated (check `prices` table)
  ```sql
  SELECT * FROM prices ORDER BY timestamp DESC LIMIT 10;
  ```

### 3. API Performance
- [ ] Summary endpoint responding < 200ms
- [ ] Cache hit rate > 80% (check metrics)
- [ ] No 500 errors in past hour
- [ ] All endpoints returning valid JSON

### 4. Background Jobs
- [ ] Ingestion jobs running every 60s (posts) and 30s (comments)
- [ ] Aggregation jobs completing successfully
- [ ] Price updates happening every minute
- [ ] Daily thread scheduled correctly

## 📱 Reddit App Integration

### 1. Create Reddit App (if not already done)
- [ ] Visit https://www.reddit.com/prefs/apps
- [ ] Create new "web app"
- [ ] Note Client ID and Secret (already in .env)

### 2. Build App Views
- [ ] Create HTML/JS views for each tab (see `docs/reddit_app.md`)
- [ ] Host on GitHub Pages or same server as API
- [ ] Test views locally first

### 3. Configure Reddit App Manifest
- [ ] Create app manifest JSON
- [ ] Set tab URLs to your hosted views
- [ ] Configure permissions (identity, read)

### 4. Install on Subreddit
- [ ] Must have moderator permissions
- [ ] Go to subreddit settings → Apps
- [ ] Add your Reddit App
- [ ] Pin to sidebar or tabs

## 🔐 Security Checklist

- [ ] All secrets in environment variables (not in code)
- [ ] ADMIN_TOKEN is strong (16+ characters)
- [ ] SECRET_KEY is strong (32+ characters)
- [ ] Database password is strong
- [ ] Redis password set (if using managed Redis)
- [ ] CORS origins configured appropriately (not wildcard in production)
- [ ] Rate limiting enabled
- [ ] HTTPS enabled for production

## 📦 Backup & Maintenance

### Initial Setup
- [ ] Take initial database snapshot:
  ```bash
  # Docker
  docker-compose exec postgres pg_dump -U sentiment sentiment_tracker > backup_initial.sql

  # Fly.io
  fly postgres db backup <postgres-app-name>
  ```

- [ ] Export configuration for documentation:
  ```bash
  cp IMPLEMENTATION_SUMMARY.md ~/documentation/
  cp .env .env.backup
  ```

### Ongoing Maintenance
- [ ] Schedule daily database backups
- [ ] Monitor disk usage (especially Postgres)
- [ ] Review logs weekly for errors
- [ ] Update dependencies monthly
- [ ] Check for Reddit API changes

## 🎯 Success Criteria

Before considering deployment complete, verify:

- [x] All pre-flight checks pass
- [ ] All services running healthy for 1 hour
- [ ] At least 10 posts ingested successfully
- [ ] NLP processing working (entities + sentiment)
- [ ] API endpoints returning valid data
- [ ] Prometheus metrics being collected
- [ ] No critical errors in logs
- [ ] Daily thread posts successfully (test manually first)

## 📞 Troubleshooting

If you encounter issues:

1. **Check logs**:
   ```bash
   docker-compose logs -f web
   docker-compose logs -f worker
   docker-compose logs -f scheduler
   ```

2. **Verify environment variables**:
   ```bash
   docker-compose exec web env | grep REDDIT
   ```

3. **Test database connection**:
   ```bash
   docker-compose exec web python -c "from app.db import get_db; next(get_db())"
   ```

4. **Test Redis connection**:
   ```bash
   docker-compose exec redis redis-cli PING
   ```

5. **Review troubleshooting guide**: `docs/deployment.md`

## 📝 Notes

- Estimated setup time: 30-60 minutes
- Initial data population: 1-2 hours
- First daily thread: Next scheduled time (18:00 UTC)
- Aggregates available: After first 1-hour window

## ✅ Final Sign-Off

Date: _______________
Environment: [ ] Local [ ] Staging [ ] Production
Deployed by: _______________
Verified by: _______________

All checks completed: [ ]
Ready for users: [ ]
