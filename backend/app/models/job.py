from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from app.db.session import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(100), nullable=False)
    original_id = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    is_remote = Column(Boolean, nullable=False, default=False)
    description = Column(Text, nullable=False)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    salary_currency = Column(String(10), nullable=False, default="USD")
    url = Column(String(1024), unique=True, nullable=False)
    posted_at = Column(DateTime(timezone=True), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    raw_data = Column(JSON, nullable=False, default=dict)
    hash_key = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    matches = relationship("JobMatch", back_populates="job", cascade="all, delete-orphan")
