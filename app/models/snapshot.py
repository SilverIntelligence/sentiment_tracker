"""Snapshot model for precomputed API responses."""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, String

from app.db.database import Base


class Snapshot(Base):
    """Precomputed API response snapshots."""

    __tablename__ = "snapshots"

    timestamp = Column(DateTime, primary_key=True)
    key = Column(String(100), primary_key=True, index=True)
    payload = Column(JSON, nullable=False)

    def __repr__(self) -> str:
        return f"<Snapshot {self.key} at {self.timestamp}>"
