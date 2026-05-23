from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.match import JobMatch
from app.schemas.match import JobMatchResponse, JobMatchStatusUpdate
from app.api.deps import get_current_user
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

router = APIRouter()

@router.get("", response_model=List[JobMatchResponse])
def get_user_matches(
    status: Optional[str] = Query(None, description="Filter matches by status (pending, saved, applied, dismissed)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve ranked list of job matches tailored to the active user profile.
    Ordered by match_score in descending rank order.
    """
    query = db.query(JobMatch).filter(JobMatch.user_id == current_user.id)
    
    if status:
        # Validate status parameter
        valid_statuses = {"pending", "viewed", "saved", "applied", "dismissed"}
        if status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status value. Must be one of {valid_statuses}"
            )
        query = query.filter(JobMatch.status == status)
        
    matches = query.order_by(JobMatch.match_score.desc()).all()
    return matches

@router.put("/{job_id}/status", status_code=status.HTTP_200_OK)
def update_match_status(
    job_id: UUID,
    status_update: JobMatchStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user interaction status for a specific job match (e.g. saved, applied, dismissed)."""
    # Validate incoming status
    try:
        validated_status = JobMatchStatusUpdate.validate_status(status_update.status)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
        
    match = db.query(JobMatch).filter(
        JobMatch.user_id == current_user.id,
        JobMatch.job_id == job_id
    ).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job match record not found for this user."
        )
        
    match.status = validated_status
    match.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    return {"message": "Match status updated successfully."}
