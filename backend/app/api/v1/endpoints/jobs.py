from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.job import JobResponse
from app.services.matching.search_client import JobSearchClient
from app.api.deps import get_current_user
from typing import List, Optional

router = APIRouter()
search_client = JobSearchClient()

@router.get("", response_model=List[JobResponse])
def search_jobs(
    q: Optional[str] = Query(None, description="Fuzzy full-text search query string"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search and retrieve crawled job postings.
    Utilizes high-speed Elasticsearch indexes, falling back to PostgreSQL ILIKE matching if down.
    """
    jobs = search_client.search_jobs(query=q, db=db, limit=limit, offset=offset)
    return jobs

@router.post("/crawl", status_code=200)
def trigger_crawl(
    query: str = Query(..., description="Job role query to search and crawl (e.g. 'Python', 'React')"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger aggregators to fetch, normalize, and match jobs in real-time.
    Runs synchronously if in SQLite/Standalone mode or if Celery is offline.
    """
    from app.tasks.jobs import crawl_and_normalize_jobs
    from app.core.config import settings
    import redis
    
    celery_is_active = False
    try:
        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        r.ping()
        celery_is_active = True
    except Exception:
        pass
        
    if celery_is_active and not settings.DATABASE_URL.startswith("sqlite"):
        # Celery background dispatch
        crawl_and_normalize_jobs.delay(query=query, limit_per_source=5)
        return {
            "status": "success",
            "mode": "celery_async",
            "message": f"Crawling task for '{query}' queued successfully in the Celery background cluster."
        }
    else:
        # Standalone synchronous crawl execution
        results = crawl_and_normalize_jobs(query=query, limit_per_source=5, db_session=db)
        return {
            "status": "success",
            "mode": "standalone_sync",
            "message": f"Aggregators completed crawling and matching for '{query}'.",
            "details": results
        }
