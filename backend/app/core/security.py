from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hashed value."""
    # Truncate password to 72 characters to ensure safety against bcrypt length limits
    truncated_password = plain_password[:72]
    return pwd_context.verify(truncated_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a plaintext password using BCrypt."""
    # Truncate password to 72 characters to ensure safety against bcrypt length limits
    truncated_password = password[:72]
    return pwd_context.hash(truncated_password)

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create a signed JWT access token for a subject."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_access_token(token: str) -> Optional[str]:
    """Verify a JWT access token and return its subject (sub claim) if valid."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload.get("sub")
    except (jwt.PyJWTError, ValueError):
        return None
