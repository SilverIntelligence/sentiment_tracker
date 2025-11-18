"""RQ Worker for background jobs."""

import logging
import sys

from redis import Redis
from rq import Worker

from app.core.config import get_settings
from app.db.redis_client import get_redis

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    """Run RQ worker."""
    settings = get_settings()
    logger.info(f"Starting worker with Redis at {settings.redis_url}")

    redis_conn = get_redis()

    # Listen on multiple queues
    queues = ["default", "high", "low"]

    worker = Worker(queues, connection=redis_conn)
    logger.info(f"Worker listening on queues: {queues}")

    try:
        worker.work(with_scheduler=False)
    except KeyboardInterrupt:
        logger.info("Worker interrupted, shutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
