from pydantic import BaseModel, Field, HttpUrl, model_validator, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class JobBase(BaseModel):
    source: str = Field(..., description="The platform or crawler that sourced this job")
    original_id: str = Field(..., description="Unique job ID from the source system")
    title: str = Field(..., description="Job Title")
    company: str = Field(..., description="Company Name")
    location: str = Field(..., description="Job Location description")
    is_remote: bool = Field(default=False, description="Is the job Remote?")
    description: str = Field(..., description="Full text description of the job posting")
    salary_min: Optional[int] = Field(default=None, ge=0, description="Minimum salary bracket")
    salary_max: Optional[int] = Field(default=None, ge=0, description="Maximum salary bracket")
    salary_currency: str = Field(default="USD", max_length=10, description="Salary Currency")
    url: str = Field(..., description="Direct application link url")
    posted_at: datetime = Field(..., description="Timestamp when the job was posted")

    @model_validator(mode="after")
    def validate_salary_range(self) -> "JobBase":
        """Verify that salary_max is greater than or equal to salary_min if both are defined."""
        s_min = self.salary_min
        s_max = self.salary_max
        if s_min is not None and s_max is not None and s_max < s_min:
            raise ValueError("salary_max must be greater than or equal to salary_min")
        return self

class JobCreate(JobBase):
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Raw crawled payload for historical audits")

class JobResponse(JobBase):
    id: UUID
    processed_at: datetime
    hash_key: str

    model_config = ConfigDict(from_attributes=True)
