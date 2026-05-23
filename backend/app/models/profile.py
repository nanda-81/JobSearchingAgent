from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.session import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    target_titles = Column(JSON, nullable=False, default=list)  # e.g., ["Software Engineer", "Solutions Architect"]
    target_locations = Column(JSON, nullable=False, default=list)  # e.g., ["Remote", "New York"]
    salary_min = Column(Integer, nullable=True)
    experience_level = Column(String(50), nullable=False, default="mid")
    job_types = Column(JSON, nullable=False, default=list)  # e.g., ["Full-time", "Contract"]
    keywords = Column(JSON, nullable=False, default=list)  # e.g., ["python", "fastapi"]
    excluded_keywords = Column(JSON, nullable=False, default=list)  # e.g., ["php", "cobol"]
    resume_url = Column(String(512), nullable=True)
    consent_given = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="profile")
