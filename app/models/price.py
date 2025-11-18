"""Price data model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, String

from app.db.database import Base


class Price(Base):
    """Price OHLCV data."""

    __tablename__ = "prices"

    timestamp = Column(DateTime, primary_key=True)
    symbol = Column(String(20), primary_key=True, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float)

    def __repr__(self) -> str:
        return f"<Price {self.symbol} at {self.timestamp}: {self.close}>"
