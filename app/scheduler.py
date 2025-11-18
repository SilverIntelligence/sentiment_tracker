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
        # These will be implemented in the ingestion module
        # self.queue.enqueue_in(timedelta(seconds=60), 'app.workers.ingestion.ingest_posts')
        # self.queue.enqueue_in(timedelta(seconds=30), 'app.workers.ingestion.ingest_comments')

        # Schedule aggregation jobs
        # self.queue.enqueue_in(timedelta(minutes=5), 'app.workers.aggregation.compute_windows')

        # Schedule price updates
        # self.queue.enqueue_in(timedelta(minutes=1), 'app.workers.prices.price_pull')

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
