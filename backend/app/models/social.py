from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.session import Base

class SocialCredentials(Base):
    __tablename__ = "social_credentials"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    twitter_token = Column(Text, nullable=True)          # Encrypted at-rest
    telegram_chat_id = Column(String(255), nullable=True)  # Encrypted at-rest
    whatsapp_phone = Column(String(255), nullable=True)    # Encrypted at-rest
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="social_credentials")
