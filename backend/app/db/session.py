from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

from sqlalchemy.pool import StaticPool

# Create database engine (PostgreSQL connection pooling, SQLite single-file mode)
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool if ":memory:" in settings.DATABASE_URL else None,
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,  # Proactively checks and discards dead connections
        pool_size=20,        # Base pool size
        max_overflow=10,     # Max overflow connections beyond base pool
    )

# Sessionmaker for local database transactions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy ORM models
Base = declarative_base()

def get_db():
    """FastAPI dependency to yield a database session and close it post-request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
