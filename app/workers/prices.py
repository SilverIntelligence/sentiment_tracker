"""Price data fetching and storage."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.db.database import SessionLocal
from app.db.redis_client import cache_get, cache_set
from app.models import Price

logger = logging.getLogger(__name__)


class PriceClient:
    """Fetches price data from Yahoo Finance or other sources."""

    def __init__(self):
        """Initialize price client."""
        self.settings = get_settings()

        # Symbol mapping (Yahoo Finance uses different symbols)
        self.symbol_map = {
            "XAUUSD": "GC=F",  # Gold futures
            "XAGUSD": "SI=F",  # Silver futures
            "GLD": "GLD",  # SPDR Gold ETF
            "SLV": "SLV",  # iShares Silver ETF
            "PSLV": "PSLV",  # Sprott Physical Silver
            "PHYS": "PHYS",  # Sprott Physical Gold
        }

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def fetch_yahoo_finance(self, symbol: str) -> Optional[Dict]:
        """
        Fetch current price from Yahoo Finance.

        Args:
            symbol: Yahoo Finance symbol

        Returns:
            Dict with price data or None
        """
        try:
            # Use Yahoo Finance quote API
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                "interval": "1m",
                "range": "1d",
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if "chart" not in data or "result" not in data["chart"]:
                logger.error(f"Invalid response structure for {symbol}")
                return None

            result = data["chart"]["result"][0]

            # Get latest price data
            meta = result.get("meta", {})
            quote = result.get("indicators", {}).get("quote", [{}])[0]

            # Get the last available OHLCV
            if not quote:
                return None

            # Get last non-null values
            close_prices = [p for p in quote.get("close", []) if p is not None]
            open_prices = [p for p in quote.get("open", []) if p is not None]
            high_prices = [p for p in quote.get("high", []) if p is not None]
            low_prices = [p for p in quote.get("low", []) if p is not None]
            volumes = [v for v in quote.get("volume", []) if v is not None]

            if not close_prices:
                logger.warning(f"No price data available for {symbol}")
                return None

            return {
                "symbol": symbol,
                "timestamp": datetime.utcnow(),
                "open": open_prices[-1] if open_prices else close_prices[-1],
                "high": high_prices[-1] if high_prices else close_prices[-1],
                "low": low_prices[-1] if low_prices else close_prices[-1],
                "close": close_prices[-1],
                "volume": volumes[-1] if volumes else 0,
                "regular_market_price": meta.get("regularMarketPrice", close_prices[-1]),
                "previous_close": meta.get("previousClose"),
            }

        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None

    def fetch_price(self, symbol: str) -> Optional[Dict]:
        """
        Fetch price for a symbol (with caching).

        Args:
            symbol: Standard symbol (XAUUSD, etc)

        Returns:
            Price data dict or None
        """
        # Check cache first (1 minute TTL)
        cache_key = f"price:{symbol}"
        cached = cache_get(cache_key)

        if cached:
            logger.debug(f"Using cached price for {symbol}")
            import json

            return json.loads(cached)

        # Map symbol to Yahoo Finance
        yahoo_symbol = self.symbol_map.get(symbol, symbol)

        # Fetch from Yahoo Finance
        price_data = self.fetch_yahoo_finance(yahoo_symbol)

        if price_data:
            # Store original symbol
            price_data["symbol"] = symbol

            # Cache for 1 minute
            import json

            cache_set(cache_key, json.dumps(price_data), ttl=60)

        return price_data

    def fetch_all_prices(self) -> Dict[str, Dict]:
        """
        Fetch prices for all configured symbols.

        Returns:
            Dict mapping symbol -> price data
        """
        symbols = ["XAUUSD", "XAGUSD", "GLD", "SLV", "PSLV", "PHYS"]

        prices = {}

        for symbol in symbols:
            try:
                price_data = self.fetch_price(symbol)
                if price_data:
                    prices[symbol] = price_data
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
                continue

        return prices


def store_price(db: Session, price_data: Dict) -> Price:
    """
    Store price data in database.

    Args:
        db: Database session
        price_data: Price data dict

    Returns:
        Price model instance
    """
    # Round timestamp to minute
    timestamp = price_data["timestamp"].replace(second=0, microsecond=0)

    # Check if exists
    existing = (
        db.query(Price)
        .filter(
            Price.timestamp == timestamp,
            Price.symbol == price_data["symbol"],
        )
        .first()
    )

    data = {
        "timestamp": timestamp,
        "symbol": price_data["symbol"],
        "open": price_data["open"],
        "high": price_data["high"],
        "low": price_data["low"],
        "close": price_data["close"],
        "volume": price_data.get("volume", 0),
    }

    if existing:
        # Update
        for key, value in data.items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create
        price = Price(**data)
        db.add(price)
        db.commit()
        db.refresh(price)
        return price


def price_pull() -> Dict:
    """
    Pull latest prices and store in database.

    Returns:
        Dict with statistics
    """
    logger.info("Starting price pull")

    client = PriceClient()
    db = SessionLocal()

    try:
        prices_fetched = 0
        prices_stored = 0

        # Fetch all prices
        all_prices = client.fetch_all_prices()

        for symbol, price_data in all_prices.items():
            try:
                store_price(db, price_data)
                prices_fetched += 1
                prices_stored += 1

                logger.debug(
                    f"Stored {symbol}: ${price_data['close']:.2f}"
                )

            except Exception as e:
                logger.error(f"Error storing price for {symbol}: {e}")
                continue

        stats = {
            "prices_fetched": prices_fetched,
            "prices_stored": prices_stored,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"Price pull complete: {prices_stored} prices stored")
        return stats

    except Exception as e:
        logger.error(f"Error during price pull: {e}")
        raise
    finally:
        db.close()


def calculate_24h_change(db: Session, symbol: str) -> Optional[float]:
    """
    Calculate 24h price change percentage.

    Args:
        db: Database session
        symbol: Price symbol

    Returns:
        Change percentage or None
    """
    now = datetime.utcnow()
    day_ago = now - timedelta(hours=24)

    # Get current price
    current = (
        db.query(Price)
        .filter(Price.symbol == symbol, Price.timestamp <= now)
        .order_by(Price.timestamp.desc())
        .first()
    )

    # Get price from 24h ago
    past = (
        db.query(Price)
        .filter(Price.symbol == symbol, Price.timestamp <= day_ago)
        .order_by(Price.timestamp.desc())
        .first()
    )

    if not current or not past:
        return None

    change_pct = ((current.close - past.close) / past.close) * 100

    return change_pct


def get_latest_price(db: Session, symbol: str) -> Optional[Price]:
    """
    Get latest price for a symbol.

    Args:
        db: Database session
        symbol: Price symbol

    Returns:
        Price instance or None
    """
    return (
        db.query(Price)
        .filter(Price.symbol == symbol)
        .order_by(Price.timestamp.desc())
        .first()
    )


def get_price_history(
    db: Session, symbol: str, hours: int = 24
) -> List[Price]:
    """
    Get price history for a symbol.

    Args:
        db: Database session
        symbol: Price symbol
        hours: Number of hours of history

    Returns:
        List of Price instances
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    return (
        db.query(Price)
        .filter(Price.symbol == symbol, Price.timestamp >= cutoff)
        .order_by(Price.timestamp.asc())
        .all()
    )


def calculate_volatility(prices: List[Price]) -> float:
    """
    Calculate realized volatility (5-day ATR percent).

    Args:
        prices: List of Price instances

    Returns:
        Volatility as percentage
    """
    if len(prices) < 2:
        return 0.0

    # Calculate average true range
    atrs = []
    for i in range(1, len(prices)):
        high_low = prices[i].high - prices[i].low
        high_close = abs(prices[i].high - prices[i - 1].close)
        low_close = abs(prices[i].low - prices[i - 1].close)

        tr = max(high_low, high_close, low_close)
        atrs.append(tr)

    if not atrs:
        return 0.0

    atr = sum(atrs) / len(atrs)

    # Convert to percentage of price
    last_price = prices[-1].close
    atr_pct = (atr / last_price) * 100

    return atr_pct
