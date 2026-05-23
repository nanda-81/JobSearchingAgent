from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import uuid
from app.db.session import get_db
from app.models.user import User
from app.core.config import settings
from app.core.security import verify_access_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/token"
)

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """FastAPI dependency to extract JWT access token and retrieve current User context."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify JWT Token (returns sub claim as a string)
    user_id_str = verify_access_token(token)
    if user_id_str is None:
        raise credentials_exception
    
    # Parse string user_id into a native uuid.UUID object for cross-DB compatibility
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception
        
    # Query database for user
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
        
    return user
