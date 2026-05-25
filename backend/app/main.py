from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import redis
from app.core.config import settings
from app.api.v1.endpoints import auth, profile, jobs, matches, gdpr, social
from app.db.session import get_db, engine
from sqlalchemy.sql import text

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Personalized Job Search Automation Platform (PJSAP) Gateway",
    version="1.0.0",
    docs_url="/docs",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """Ensure database schema is dynamically created on startup."""
    from app.db.session import Base, engine
    # Import all models to ensure they are registered on the Base metadata
    from app.models.user import User
    from app.models.profile import UserProfile
    from app.models.job import Job
    from app.models.match import JobMatch
    from app.models.social import SocialCredentials
    from app.models.audit import AuditLog
    
    Base.metadata.create_all(bind=engine)

# Register Endpoints
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(profile.router, prefix=f"{settings.API_V1_STR}/profile", tags=["profile"])
app.include_router(jobs.router, prefix=f"{settings.API_V1_STR}/jobs", tags=["jobs"])
app.include_router(matches.router, prefix=f"{settings.API_V1_STR}/matches", tags=["matches"])
app.include_router(social.router, prefix=f"{settings.API_V1_STR}/social", tags=["social"])
app.include_router(gdpr.router, prefix=f"{settings.API_V1_STR}/gdpr", tags=["gdpr"])

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint that verifies connectivity to downstream services."""
    health_status = {
        "status": "healthy",
        "postgres": "unknown",
        "redis": "unknown"
    }
    
    # 1. Verify PostgreSQL
    try:
        db.execute(text("SELECT 1"))
        health_status["postgres"] = "ok"
    except Exception as e:
        health_status["postgres"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
        
    # 2. Verify Redis
    try:
        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        health_status["redis"] = "ok"
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
        
    if health_status["status"] == "unhealthy":
        from fastapi import Response
        return Response(
            content=str(health_status),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json"
        )
        
    return health_status

@app.get("/")
def read_root():
    return {"message": "Welcome to PJSAP API Gateway. Go to /docs for interactive Swagger UI documentation."}
