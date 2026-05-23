from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional
from datetime import datetime
from app.schemas.job import JobResponse

class JobMatchStatusUpdate(BaseModel):
    status: str = Field(..., description="Match Status: pending, viewed, saved, applied, dismissed")

    @classmethod
    def validate_status(cls, value: str) -> str:
        valid_statuses = {"pending", "viewed", "saved", "applied", "dismissed"}
        if value not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return value

class JobMatchResponse(BaseModel):
    job: JobResponse
    match_score: float = Field(..., ge=0.0, le=1.0)
    matching_details: Dict[str, Any] = Field(default_factory=dict)
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SocialCredentialsUpsert(BaseModel):
    twitter_token: Optional[str] = Field(default=None, description="Plaintext Twitter OAuth token to encrypt")
    telegram_chat_id: Optional[str] = Field(default=None, description="Plaintext Telegram chat ID to encrypt")
    whatsapp_phone: Optional[str] = Field(default=None, description="Plaintext WhatsApp phone to encrypt")
