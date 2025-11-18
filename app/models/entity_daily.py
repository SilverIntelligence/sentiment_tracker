"""Entity daily aggregates model."""

from datetime import date

from sqlalchemy import JSON, Column, Date, Float, Integer, String

from app.db.database import Base


class EntityDaily(Base):
    """Daily entity sentiment aggregates."""

    __tablename__ = "entities_daily"

    dt = Column(Date, primary_key=True)
    entity = Column(String(50), primary_key=True, index=True)
    mentions = Column(Integer, default=0)
    unique_authors = Column(Integer, default=0)
    mean_sentiment = Column(Float)
    bull_ratio = Column(Float)
    index_value = Column(Float)  # S_t = z(mean_sentiment) * log(1 + mentions)
    top_posts = Column(JSON)  # Array of top post IDs with scores

    def __repr__(self) -> str:
        return f"<EntityDaily {self.entity} on {self.dt}>"
