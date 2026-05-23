from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.profile import UserProfile
from app.models.match import JobMatch
from app.models.audit import AuditLog
from app.api.deps import get_current_user
from datetime import datetime, timezone
import logging
import hashlib

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/export", status_code=status.HTTP_200_OK)
def export_user_data(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    GDPR Subject Access Request (SAR) - Data Portability.
    Retrieves and exports all personal, target, match, and credential history as a JSON download.
    """
    # 1. Compile User Details
    user_data = {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }
    
    # 2. Compile Targeting Profile
    profile_data = {}
    if current_user.profile:
        profile = current_user.profile
        profile_data = {
            "target_titles": profile.target_titles,
            "target_locations": profile.target_locations,
            "salary_min": profile.salary_min,
            "experience_level": profile.experience_level,
            "job_types": profile.job_types,
            "keywords": profile.keywords,
            "excluded_keywords": profile.excluded_keywords,
            "resume_url": profile.resume_url,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
        }
        
    # 3. Compile Job Matches
    matches_data = []
    matches = db.query(JobMatch).filter(JobMatch.user_id == current_user.id).all()
    for match in matches:
        matches_data.append({
            "job_title": match.job.title if match.job else "Unknown",
            "company": match.job.company if match.job else "Unknown",
            "job_url": match.job.url if match.job else None,
            "match_score": match.match_score,
            "status": match.status,
            "created_at": match.created_at.isoformat()
        })
        
    # 4. Compile Audit History
    audit_data = []
    audits = db.query(AuditLog).filter(AuditLog.user_id == current_user.id).all()
    for audit in audits:
        audit_data.append({
            "action": audit.action,
            "ip_address": audit.ip_address,
            "payload": audit.payload,
            "timestamp": audit.created_at.isoformat()
        })
        
    # 5. Record GDPR Action in Audit Log
    gdpr_log = AuditLog(
        user_id=current_user.id,
        action="gdpr_data_export",
        ip_address=request.client.host if request.client else "127.0.0.1",
        user_agent=request.headers.get("user-agent", "Unknown"),
        payload={"export_time": datetime.now(timezone.utc).isoformat()}
    )
    db.add(gdpr_log)
    db.commit()
    
    return {
        "export_metadata": {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "regulatory_framework": "GDPR / CCPA Data Portability"
        },
        "user_profile": user_data,
        "targeting_preferences": profile_data,
        "job_matches_history": matches_data,
        "system_audit_logs": audit_data
    }

@router.delete("/delete", status_code=status.HTTP_200_OK)
def delete_user_account(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    GDPR Right to be Forgotten (Account Deletion).
    Recursively cascades and purges all personal targeting, social credentials, and matches.
    """
    logger.warning(f"!!! GDPR Account Deletion triggered for User ID: {current_user.id} !!!")
    
    # 1. Log GDPR Purge Action *before* cascade wiping user record
    # Since foreign key is ON DELETE SET NULL, this audit log persists, maintaining a compliant system log
    gdpr_delete_log = AuditLog(
        user_id=current_user.id,
        action="gdpr_account_deletion",
        ip_address=request.client.host if request.client else "127.0.0.1",
        user_agent=request.headers.get("user-agent", "Unknown"),
        payload={
            "deleted_email_hash": hashlib.sha256(current_user.email.encode()).hexdigest(),
            "purged_at": datetime.now(timezone.utc).isoformat()
        }
    )
    db.add(gdpr_delete_log)
    db.flush()  # Flushes log to tie user ID before it gets cascadingly wiped
    
    # 2. Execute cascading DB deletion of the User record
    db.delete(current_user)
    db.commit()
    
    return {
        "message": "Right to be Forgotten exercised successfully. All personal profiles, target rules, match rankings, and API credentials have been permanently deleted from PJSAP systems."
    }
