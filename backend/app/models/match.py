from sqlalchemy import Column, Double, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.session import Base

class JobMatch(Base):
    __tablename__ = "job_matches"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    match_score = Column(Double, nullable=False, default=0.0)
    matching_details = Column(JSON, nullable=False, default=dict)
    status = Column(String(50), nullable=False, default="pending")  # pending, viewed, saved, applied, dismissed
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="matches")
    job = relationship("Job", back_populates="matches")
