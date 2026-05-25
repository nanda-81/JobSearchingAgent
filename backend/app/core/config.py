from typing import List, Optional
from pydantic import AnyHttpUrl, EmailStr, BeforeValidator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "PJSAP"
    API_V1_STR: str = "/api/v1"
    
    # Cryptographic keys
    SECRET_KEY: str = "38bde564177d4c885c3b0eb6190f898394e3328e18efc8db67d93dcb0653c9f2"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # AES-256 Symmetric key (must be 32-byte base64-encoded URL-safe key)
    # Default is a pre-generated valid Fernet key
    ENCRYPTION_KEY: str = "Wk1oQU5hV1ZoWTNScFlqVXdOamMzT0Rsak16VTFOVFJqT1Rnd01URXk="
    
    # Databases & Services
    DATABASE_URL: str = "postgresql://pjsap_user:pjsap_secure_password@localhost:5432/pjsap_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    RABBITMQ_URL: str = "amqp://pjsap_rabbit:rabbit_secure_password@localhost:5672//"
    
    # SMTP / Email Notification settings
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: str = "no-reply@pjsap.com"
    
    # Allow CORS domains
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://localhost:8000"
    ]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
