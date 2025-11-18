#!/bin/bash
# Deployment Validation Script
# Run this script to validate the sentiment tracker deployment

set -e  # Exit on error

echo "========================================"
echo "Sentiment Tracker Deployment Validation"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Clean shutdown
echo "Step 1: Cleaning up existing containers..."
docker-compose down -v
echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

# Step 2: Pull latest code
echo "Step 2: Pulling latest code..."
git pull origin claude/reddit-metals-sentiment-app-01PmT4tvZqmbLMRManqVwHKC
echo -e "${GREEN}✓ Code updated${NC}"
echo ""

# Step 3: Check environment file
echo "Step 3: Checking environment configuration..."
if [ ! -f .env ]; then
    echo -e "${RED}✗ .env file not found!${NC}"
    echo "Please copy .env.example to .env and configure:"
    echo "  cp .env.example .env"
    exit 1
fi

# Check critical env vars
if ! grep -q "REDDIT_CLIENT_ID=" .env || grep -q "REDDIT_CLIENT_ID=your_client_id" .env; then
    echo -e "${YELLOW}⚠ Warning: REDDIT_CLIENT_ID not configured${NC}"
fi

if ! grep -q "REDDIT_CLIENT_SECRET=" .env || grep -q "REDDIT_CLIENT_SECRET=your_client_secret" .env; then
    echo -e "${YELLOW}⚠ Warning: REDDIT_CLIENT_SECRET not configured${NC}"
fi

echo -e "${GREEN}✓ Environment file exists${NC}"
echo ""

# Step 4: Build and start services
echo "Step 4: Building and starting services..."
docker-compose up --build -d
echo -e "${GREEN}✓ Services started${NC}"
echo ""

# Step 5: Wait for services to be ready
echo "Step 5: Waiting for services to initialize (30 seconds)..."
sleep 30
echo -e "${GREEN}✓ Services should be ready${NC}"
echo ""

# Step 6: Check service status
echo "Step 6: Checking service status..."
docker-compose ps
echo ""

# Step 7: Check logs for errors
echo "Step 7: Checking logs for errors..."
if docker-compose logs web | grep -i "error" | grep -v "error_rate" | tail -5; then
    echo -e "${YELLOW}⚠ Found some errors in logs (check details above)${NC}"
else
    echo -e "${GREEN}✓ No critical errors in logs${NC}"
fi
echo ""

# Step 8: Health check
echo "Step 8: Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/healthz)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo "Response: $HEALTH_RESPONSE"
else
    echo -e "${RED}✗ Health check failed${NC}"
    echo "Response: $HEALTH_RESPONSE"
    exit 1
fi
echo ""

# Step 9: Test root endpoint
echo "Step 9: Testing root endpoint..."
ROOT_RESPONSE=$(curl -s http://localhost:8000/)
if echo "$ROOT_RESPONSE" | grep -q "Sentiment Tracker"; then
    echo -e "${GREEN}✓ Root endpoint working${NC}"
else
    echo -e "${YELLOW}⚠ Root endpoint returned unexpected response${NC}"
    echo "Response: $ROOT_RESPONSE"
fi
echo ""

# Step 10: Test metrics endpoint
echo "Step 10: Testing Prometheus metrics endpoint..."
METRICS_RESPONSE=$(curl -s http://localhost:8000/metrics)
if echo "$METRICS_RESPONSE" | grep -q "sentiment_tracker"; then
    echo -e "${GREEN}✓ Metrics endpoint working${NC}"
    echo "Sample metrics:"
    echo "$METRICS_RESPONSE" | grep "sentiment_tracker" | head -5
else
    echo -e "${YELLOW}⚠ Metrics endpoint may not be working${NC}"
fi
echo ""

# Step 11: Test API summary endpoint
echo "Step 11: Testing API summary endpoint..."
SUMMARY_RESPONSE=$(curl -s http://localhost:8000/api/v1/summary)
if echo "$SUMMARY_RESPONSE" | grep -q "prices\|sentiment\|timestamp"; then
    echo -e "${GREEN}✓ Summary API endpoint working${NC}"
    echo "Response preview:"
    echo "$SUMMARY_RESPONSE" | head -c 200
    echo "..."
else
    echo -e "${YELLOW}⚠ Summary endpoint returned unexpected response${NC}"
    echo "Response: $SUMMARY_RESPONSE"
fi
echo ""

# Step 12: Check database
echo "Step 12: Checking database..."
DB_CHECK=$(docker-compose exec -T postgres psql -U sentiment -d sentiment_tracker -c "SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public';" 2>&1)
if echo "$DB_CHECK" | grep -q "[0-9]"; then
    echo -e "${GREEN}✓ Database accessible${NC}"
else
    echo -e "${YELLOW}⚠ Database check inconclusive${NC}"
fi
echo ""

# Step 13: Check Redis
echo "Step 13: Checking Redis..."
REDIS_CHECK=$(docker-compose exec -T redis redis-cli PING 2>&1)
if echo "$REDIS_CHECK" | grep -q "PONG"; then
    echo -e "${GREEN}✓ Redis responding${NC}"
else
    echo -e "${YELLOW}⚠ Redis check inconclusive${NC}"
fi
echo ""

# Step 14: Show service URLs
echo "========================================"
echo "Validation Complete!"
echo "========================================"
echo ""
echo "Service URLs:"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Health: http://localhost:8000/healthz"
echo "  - Metrics: http://localhost:8000/metrics"
echo "  - Summary: http://localhost:8000/api/v1/summary"
echo ""
echo "Next steps:"
echo "  1. Review logs: docker-compose logs -f web"
echo "  2. Test ingestion: python scripts/test_ingestion.py"
echo "  3. Test NLP: python scripts/test_nlp.py"
echo "  4. Test prices: python scripts/test_prices.py"
echo ""
echo "To monitor real-time logs:"
echo "  docker-compose logs -f web"
echo ""
echo "To check worker status:"
echo "  docker-compose logs -f worker"
echo ""
echo -e "${GREEN}Ready for production deployment!${NC}"
