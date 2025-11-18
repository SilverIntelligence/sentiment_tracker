"""Post model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


class Post(Base):
    """Reddit post model."""

    __tablename__ = "posts"

    post_id = Column(String(20), primary_key=True, index=True)
    subreddit = Column(String(50), nullable=False, index=True)
    author = Column(String(50), nullable=False, index=True)
    created_utc = Column(DateTime, nullable=False, index=True)
    title = Column(Text, nullable=False)
    selftext = Column(Text)
    score = Column(Integer, default=0)
    num_comments = Column(Integer, default=0)
    url = Column(Text)
    is_self = Column(Boolean, default=True)
    removed = Column(Boolean, default=False)
    entities = Column(JSON)
    sentiment = Column(Float)
    processed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Post {self.post_id}: {self.title[:50]}>"
