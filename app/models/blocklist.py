"""Admin blocklist model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text

from app.db.database import Base


class AdminBlocklist(Base):
    """Admin blocklist for filtering content."""

    __tablename__ = "admin_blocklist"

    id = Column(String(36), primary_key=True)  # UUID
    type = Column(String(20), nullable=False, index=True)  # 'phrase', 'author', 'ticker'
    value = Column(String(200), nullable=False, index=True)
    reason = Column(Text)
    added_by = Column(String(50), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Blocklist {self.type}:{self.value}>"
