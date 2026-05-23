from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.social import SocialCredentials
from app.models.audit import AuditLog
from app.schemas.match import SocialCredentialsUpsert
from app.core.crypto import encrypt_string
from app.api.deps import get_current_user
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Note: SocialCredentialsUpsert is imported from schemas.match which matches the openapi specification mapping

@router.post("/credentials", status_code=status.HTTP_200_OK)
def save_social_credentials(
    payload: SocialCredentialsUpsert,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Encrypt and store User credentials for Twitter OAuth, Telegram, or WhatsApp alerts.
    Dynamically encrypts tokens using AES-256 at-rest prior to database commit.
    """
    # Query or initialize SocialCredentials
    creds = db.query(SocialCredentials).filter(SocialCredentials.user_id == current_user.id).first()
    
    if not creds:
        creds = SocialCredentials(user_id=current_user.id)
        db.add(creds)
        
    # Dynamically encrypt tokens using AES-256
    if payload.twitter_token is not None:
        creds.twitter_token = encrypt_string(payload.twitter_token)
    if payload.telegram_chat_id is not None:
        creds.telegram_chat_id = encrypt_string(payload.telegram_chat_id)
    if payload.whatsapp_phone is not None:
        creds.whatsapp_phone = encrypt_string(payload.whatsapp_phone)
        
    creds.updated_at = datetime.now(timezone.utc)
    
    # Write security audit record
    audit_log = AuditLog(
        user_id=current_user.id,
        action="update_social_credentials",
        ip_address=request.client.host if request.client else "127.0.0.1",
        user_agent=request.headers.get("user-agent", "Unknown"),
        payload={"encrypted_fields": [field for field, val in payload.model_dump().items() if val is not None]}
    )
    db.add(audit_log)
    
    db.commit()
    logger.info(f"[Security] Securely encrypted and updated social credentials for User: {current_user.id}")
    return {"message": "Tokens and credentials securely encrypted and stored."}
