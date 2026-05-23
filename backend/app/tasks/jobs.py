import hashlib
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
from celery.utils.log import get_task_logger
from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.job import Job
from app.models.profile import UserProfile
from app.models.match import JobMatch
from app.schemas.job import JobCreate
from app.services.crawler.linkedin import LinkedInCrawler
from app.services.crawler.indeed import IndeedCrawler
from app.services.crawler.glassdoor import GlassdoorCrawler
from app.services.crawler.github import GitHubCrawler
from app.services.crawler.stackoverflow import StackOverflowCrawler
from app.services.crawler.base import CircuitBreakerOpenException
from app.services.matching.search_client import JobSearchClient
from app.services.matching.engine import calculate_match_score

logger = get_task_logger(__name__)

def generate_job_hash(title: str, company: str, location: str) -> str:
    """Generate a unique SHA-256 hash string for job posting deduplication."""
    norm_title = title.lower().strip()
    norm_company = company.lower().strip()
    norm_location = location.lower().strip()
    
    hash_raw = f"{norm_title}|{norm_company}|{norm_location}"
    return hashlib.sha256(hash_raw.encode("utf-8")).hexdigest()

@celery_app.task(name="app.tasks.jobs.crawl_and_normalize_jobs")
def crawl_and_normalize_jobs(query: str, limit_per_source: int = 5, db_session: Any = None) -> Dict[str, Any]:
    """
    Background worker task to aggregate jobs from 5 platforms simultaneously.
    Validates, deduplicates, and saves newly discovered jobs into PostgreSQL.
    Indices new jobs in Elasticsearch and computes matches against all User Profiles.
    """
    logger.info(f"[Task] Starting crawl, index, and match pipeline for query: '{query}'")
    
    crawlers = [
        LinkedInCrawler(),
        IndeedCrawler(),
        GlassdoorCrawler(),
        GitHubCrawler(),
        StackOverflowCrawler()
    ]
    
    results_summary = {
        "status": "success",
        "processed_crawlers": [],
        "errors": {},
        "jobs_crawled_count": 0,
        "new_jobs_saved": 0,
        "matches_generated": 0
    }
    
    # Use injected session for testing, otherwise instantiate SessionLocal
    db = db_session if db_session is not None else SessionLocal()
    should_close = db_session is None
    
    # Initialize search client (gracefully handles Elasticsearch connection offline)
    search_client = JobSearchClient()
    
    try:
        # Fetch consented user profiles for real-time matching
        active_profiles = db.query(UserProfile).filter(UserProfile.consent_given == True).all()
        
        for crawler in crawlers:
            try:
                results_summary["processed_crawlers"].append(crawler.name)
                logger.info(f"[Task] Crawling '{crawler.name}'...")
                
                # Fetch raw jobs
                crawled_jobs: List[JobCreate] = crawler.fetch_jobs(query, limit=limit_per_source)
                results_summary["jobs_crawled_count"] += len(crawled_jobs)
                
                for job_data in crawled_jobs:
                    # 1. Generate unique hash key for deduplication
                    hash_key = generate_job_hash(job_data.title, job_data.company, job_data.location)
                    
                    # 2. Check if job already exists in database
                    existing_job = db.query(Job).filter(
                        (Job.hash_key == hash_key) | (Job.url == job_data.url)
                    ).first()
                    
                    if not existing_job:
                        # 3. Save new job
                        new_job = Job(
                            source=job_data.source,
                            original_id=job_data.original_id,
                            title=job_data.title,
                            company=job_data.company,
                            location=job_data.location,
                            is_remote=job_data.is_remote,
                            description=job_data.description,
                            salary_min=job_data.salary_min,
                            salary_max=job_data.salary_max,
                            salary_currency=job_data.salary_currency,
                            url=job_data.url,
                            posted_at=job_data.posted_at,
                            raw_data=job_data.raw_data,
                            hash_key=hash_key
                        )
                        db.add(new_job)
                        db.flush()  # Generate primary key ID for new_job
                        results_summary["new_jobs_saved"] += 1
                        
                        # 4. Index in Elasticsearch
                        search_client.index_job(new_job)
                        
                        # 5. Real-Time Relevancy Scoring & Matching
                        for profile in active_profiles:
                            score, details = calculate_match_score(new_job, profile)
                            if score >= 0.30:  # 30% match hurdle limit
                                match_record = JobMatch(
                                    user_id=profile.user_id,
                                    job_id=new_job.id,
                                    match_score=score,
                                    matching_details=details,
                                    status="pending"
                                )
                                db.add(match_record)
                                results_summary["matches_generated"] += 1
                
                # Commit crawler batch atomically
                db.commit()
                logger.info(f"[Task] Finished '{crawler.name}' cleanly.")
                
            except CircuitBreakerOpenException as cbe:
                logger.error(f"[Task] Circuit breaker open for '{crawler.name}': {str(cbe)}")
                results_summary["errors"][crawler.name] = "CircuitBreakerOpen"
            except Exception as e:
                db.rollback()
                logger.error(f"[Task] Failed crawling '{crawler.name}': {str(e)}")
                results_summary["errors"][crawler.name] = str(e)
                results_summary["status"] = "partial_failure"
                
    finally:
        if should_close:
            db.close()
        
    logger.info(f"[Task] Crawl and match process completed. Summary: {results_summary}")
    return results_summary
