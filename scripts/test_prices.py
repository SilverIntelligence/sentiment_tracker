#!/usr/bin/env python3
"""Test script for price data fetching."""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import SessionLocal, init_db
from app.workers.prices import (
    PriceClient,
    calculate_24h_change,
    get_latest_price,
    price_pull,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_price_fetch():
    """Test fetching prices from Yahoo Finance."""
    logger.info("Testing price fetching...")

    client = PriceClient()

    symbols = ["XAUUSD", "XAGUSD", "GLD", "SLV"]

    passed = True

    for symbol in symbols:
        try:
            price_data = client.fetch_price(symbol)

            if price_data:
                logger.info(f"  ✓ {symbol}: ${price_data['close']:.2f}")
                logger.info(f"    Open: ${price_data['open']:.2f}")
                logger.info(f"    High: ${price_data['high']:.2f}")
                logger.info(f"    Low: ${price_data['low']:.2f}")

                if price_data.get("previous_close"):
                    change = (
                        (price_data["close"] - price_data["previous_close"])
                        / price_data["previous_close"]
                        * 100
                    )
                    logger.info(f"    Change: {change:+.2f}%")
            else:
                logger.error(f"  ✗ Failed to fetch {symbol}")
                passed = False

        except Exception as e:
            logger.error(f"  ✗ Error fetching {symbol}: {e}")
            passed = False

    return passed


def test_price_storage():
    """Test storing prices in database."""
    logger.info("Testing price storage...")

    try:
        init_db()

        # Pull and store prices
        stats = price_pull()

        logger.info(f"  ✓ Stored {stats['prices_stored']} prices")

        # Verify by reading back
        db = SessionLocal()

        try:
            for symbol in ["XAUUSD", "XAGUSD"]:
                latest = get_latest_price(db, symbol)

                if latest:
                    logger.info(
                        f"  ✓ {symbol} in DB: ${latest.close:.2f} at {latest.timestamp}"
                    )
                else:
                    logger.warning(f"  ⚠ {symbol} not found in database")

        finally:
            db.close()

        return True

    except Exception as e:
        logger.error(f"  ✗ Price storage failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_price_calculations():
    """Test price calculations."""
    logger.info("Testing price calculations...")

    db = SessionLocal()

    try:
        # First ensure we have data
        stats = price_pull()

        symbols = ["XAUUSD", "XAGUSD"]

        for symbol in symbols:
            # Get latest price
            latest = get_latest_price(db, symbol)

            if latest:
                logger.info(f"  {symbol}:")
                logger.info(f"    Latest: ${latest.close:.2f}")

                # Calculate 24h change (may not have enough data yet)
                change = calculate_24h_change(db, symbol)
                if change is not None:
                    logger.info(f"    24h Change: {change:+.2f}%")
                else:
                    logger.info(f"    24h Change: Not enough data yet")

        logger.info("✓ Price calculations complete")
        return True

    except Exception as e:
        logger.error(f"✗ Price calculations failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        db.close()


def main():
    """Run all price tests."""
    logger.info("=" * 60)
    logger.info("Reddit Sentiment Tracker - Price Data Test")
    logger.info("=" * 60)

    results = []

    # Test 1: Fetch prices
    results.append(("Price Fetching", test_price_fetch()))

    # Test 2: Store prices
    results.append(("Price Storage", test_price_storage()))

    # Test 3: Price calculations
    results.append(("Price Calculations", test_price_calculations()))

    # Print summary
    logger.info("=" * 60)
    logger.info("Test Summary:")
    logger.info("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {name}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        logger.info("\n🎉 All price tests passed!")
        sys.exit(0)
    else:
        logger.error("\n❌ Some tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
