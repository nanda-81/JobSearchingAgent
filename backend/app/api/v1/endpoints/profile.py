from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.profile import UserProfile
from app.schemas.profile import UserProfileUpdate, UserProfileResponse
from app.api.deps import get_current_user
from datetime import datetime, timezone

router = APIRouter()

@router.get("", response_model=UserProfileResponse)
def get_user_profile(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Retrieve active user's targeting profile settings."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found."
        )
    return profile

@router.put("", response_model=UserProfileResponse)
def update_user_profile(
    profile_in: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update targeting preferences for the authenticated user."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found."
        )
    
    # Update fields from the payload dynamically
    update_data = profile_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    profile.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(profile)
    return profile
