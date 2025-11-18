"""RQ Scheduler for cron jobs."""

import logging
import sys
import time
from datetime import datetime, timedelta

from rq import Queue
from rq.job import Job

from app.core.config import get_settings
from app.db.redis_client import get_redis

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class JobScheduler:
    """Simple job scheduler for periodic tasks."""

    def __init__(self):
        self.settings = get_settings()
        self.redis = get_redis()
        self.queue = Queue(connection=self.redis)
        logger.info("Scheduler initialized")

    def schedule_jobs(self):
        """Schedule periodic jobs."""
        logger.info("Scheduling periodic jobs...")

        # Schedule ingestion jobs
        from app.workers.aggregation import (
            compute_daily_aggregates,
            compute_hourly_aggregates,
        )
        from app.workers.ingestion import ingest_comments, ingest_posts

        # Ingest posts every 60 seconds
        self.queue.enqueue_in(
            timedelta(seconds=self.settings.ingestion_interval_posts),
            ingest_posts,
            limit=self.settings.batch_size,
        )

        # Ingest comments every 30 seconds
        self.queue.enqueue_in(
            timedelta(seconds=self.settings.ingestion_interval_comments),
            ingest_comments,
            limit=self.settings.batch_size,
        )

        # Schedule aggregation jobs
        # 1h rolling window every 5 minutes
        self.queue.enqueue_in(
            timedelta(minutes=5),
            compute_hourly_aggregates,
            hours=1,
        )

        # 24h rolling window every 15 minutes
        self.queue.enqueue_in(
            timedelta(minutes=15),
            compute_hourly_aggregates,
            hours=24,
        )

        # 7d rolling window every 30 minutes
        self.queue.enqueue_in(
            timedelta(minutes=30),
            compute_hourly_aggregates,
            hours=168,
        )

        # Daily aggregates once per day
        self.queue.enqueue_in(
            timedelta(hours=24),
            compute_daily_aggregates,
        )

        # Schedule price updates every minute
        from app.workers.prices import price_pull

        self.queue.enqueue_in(
            timedelta(minutes=1),
            price_pull,
        )

        logger.info("Jobs scheduled successfully")

    def run(self):
        """Run scheduler loop."""
        logger.info("Starting scheduler...")

        try:
            while True:
                self.schedule_jobs()
                # Sleep for 1 minute before next scheduling cycle
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Scheduler interrupted, shutting down...")
            sys.exit(0)


def main():
    """Run scheduler."""
    scheduler = JobScheduler()
    scheduler.run()


if __name__ == "__main__":
    main()
