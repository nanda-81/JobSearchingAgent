from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
import csv
import io
import os
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.match import JobMatch
from app.models.job import Job
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

@router.get("/export-csv")
def export_saved_matches_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export all saved job applications into a single downloadable CSV spreadsheet."""
    matches = db.query(JobMatch).filter(
        JobMatch.user_id == current_user.id,
        JobMatch.status == "saved"
    ).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Job Title", "Company", "Location", "Is Remote", 
        "Estimated Salary", "Match Score", "Matching Reasons", "Application Link", "Matched Date"
    ])
    
    for m in matches:
        job = db.query(Job).filter(Job.id == m.job_id).first()
        if job:
            salary_str = f"{job.salary_currency or 'USD'} {job.salary_min} - {job.salary_max}" if job.salary_min and job.salary_max else "Undisclosed"
            reasons_str = "; ".join(m.matching_details.get("reasons", []))
            writer.writerow([
                job.title,
                job.company,
                job.location,
                "Yes" if job.is_remote else "No",
                salary_str,
                f"{int(m.match_score * 100)}%",
                reasons_str,
                job.url,
                m.updated_at.isoformat() if m.updated_at else datetime.now(timezone.utc).isoformat()
            ])
            
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=pjsap_job_tracker.csv"}
    )

@router.post("/{job_id}/export-to-file", status_code=200)
def append_match_to_local_csv(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Append a specific job match to a local `jobs_tracker.csv` tracker file in your workspace."""
    match = db.query(JobMatch).filter(
        JobMatch.user_id == current_user.id,
        JobMatch.job_id == job_id
    ).first()
    
    if not match:
        raise HTTPException(
            status_code=404,
            detail="Job match record not found for this user."
        )
        
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Associated job posting not found."
        )
        
    # Determine path of the master tracker CSV in the root workspace
    current_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
    workspace_csv_path = os.path.join(workspace_dir, "jobs_tracker.csv")
    
    # Write header if file does not exist
    file_exists = os.path.exists(workspace_csv_path)
    
    try:
        with open(workspace_csv_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    "Date Tracked", "Job Title", "Company", "Location", "Is Remote", 
                    "Salary Bracket", "Match Score", "Application URL", "Status"
                ])
                
            salary_str = f"{job.salary_currency or 'USD'} {job.salary_min} - {job.salary_max}" if job.salary_min and job.salary_max else "Undisclosed"
            writer.writerow([
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                job.title,
                job.company,
                job.location,
                "Yes" if job.is_remote else "No",
                salary_str,
                f"{int(match.match_score * 100)}%",
                job.url,
                match.status
            ])
            
        return {
            "status": "success",
            "message": f"Successfully appended job '{job.title}' to your local spreadsheet tracker!",
            "file_path": workspace_csv_path
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to append to local CSV spreadsheet: {str(e)}"
        )
