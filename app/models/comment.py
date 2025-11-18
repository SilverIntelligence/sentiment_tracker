"""Comment model."""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


class Comment(Base):
    """Reddit comment model."""

    __tablename__ = "comments"

    comment_id = Column(String(20), primary_key=True, index=True)
    post_id = Column(String(20), ForeignKey("posts.post_id"), nullable=False, index=True)
    author = Column(String(50), nullable=False, index=True)
    created_utc = Column(DateTime, nullable=False, index=True)
    body = Column(Text, nullable=False)
    score = Column(Integer, default=0)
    sentiment = Column(Float)
    entities = Column(JSON)
    processed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    post = relationship("Post", back_populates="comments")

    def __repr__(self) -> str:
        return f"<Comment {self.comment_id} on {self.post_id}>"
