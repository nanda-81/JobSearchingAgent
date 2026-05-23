from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")

class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
