from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class UserProfileBase(BaseModel):
    target_titles: List[str] = Field(default_factory=list, description="Target job titles")
    target_locations: List[str] = Field(default_factory=list, description="Target geographical locations")
    salary_min: Optional[int] = Field(default=None, ge=0, description="Minimum desired salary")
    experience_level: str = Field(default="mid", description="Desired experience level: junior, mid, senior, lead")
    job_types: List[str] = Field(default_factory=list, description="Target employment types, e.g., Full-time, Contract")
    keywords: List[str] = Field(default_factory=list, description="Keywords to match")
    excluded_keywords: List[str] = Field(default_factory=list, description="Keywords to explicitly filter out")
    resume_url: Optional[str] = Field(default=None, max_length=512, description="Link to online resume/portfolio")

class UserProfileUpdate(UserProfileBase):
    pass

class UserProfileResponse(UserProfileBase):
    user_id: UUID
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            HttpUrl: lambda v: str(v)
        }
    )
