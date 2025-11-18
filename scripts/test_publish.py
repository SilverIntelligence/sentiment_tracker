#!/usr/bin/env python3
"""Test script for publishing functionality."""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import init_db
from app.workers.publishing import format_daily_thread, generate_daily_digest

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_digest_generation():
    """Test daily digest generation."""
    logger.info("Testing digest generation...")

    try:
        init_db()

        # Generate digest
        digest = generate_daily_digest()

        logger.info("✓ Digest generated successfully")
        logger.info(f"  Gold price: ${digest['prices']['gold']['price']:.2f}")
        logger.info(f"  Silver price: ${digest['prices']['silver']['price']:.2f}")
        logger.info(f"  Gold mentions: {digest['sentiment']['gold']['mentions']}")
        logger.info(
            f"  Silver mentions: {digest['sentiment']['silver']['mentions']}"
        )

        return True, digest

    except Exception as e:
        logger.error(f"✗ Digest generation failed: {e}")
        import traceback

        traceback.print_exc()
        return False, None


def test_thread_formatting(digest):
    """Test thread formatting."""
    logger.info("Testing thread formatting...")

    try:
        if not digest:
            logger.error("No digest data available")
            return False

        # Format thread
        thread_content = format_daily_thread(digest)

        logger.info("✓ Thread formatted successfully")
        logger.info("\n" + "=" * 60)
        logger.info("THREAD PREVIEW:")
        logger.info("=" * 60)
        logger.info(thread_content)
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"✗ Thread formatting failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all publishing tests."""
    logger.info("=" * 60)
    logger.info("Reddit Sentiment Tracker - Publishing Test")
    logger.info("=" * 60)

    results = []

    # Test 1: Generate digest
    passed, digest = test_digest_generation()
    results.append(("Digest Generation", passed))

    # Test 2: Format thread
    results.append(("Thread Formatting", test_thread_formatting(digest)))

    # Print summary
    logger.info("=" * 60)
    logger.info("Test Summary:")
    logger.info("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {name}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        logger.info("\n🎉 All publishing tests passed!")
        logger.info(
            "\nNote: Actual posting to Reddit requires valid credentials and permissions."
        )
        sys.exit(0)
    else:
        logger.error("\n❌ Some tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
