import hashlib
import logging
import re
import requests
from typing import List, Dict, Any, Optional
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

COMPANY_CAREERS_MAP = {
    "hubspot": "https://www.hubspot.com/careers",
    "salesforce": "https://careers.salesforce.com",
    "docusign": "https://www.docusign.com/careers",
    "adobe": "https://www.adobe.com/careers.html",
    "shopify": "https://www.shopify.com/careers",
    "nvidia": "https://www.nvidia.com/en-us/about-nvidia/careers",
    "intel": "https://www.intel.com/content/www/us/en/jobs/careers.html",
    "google": "https://careers.google.com",
    "microsoft": "https://careers.microsoft.com",
    "apple": "https://www.apple.com/careers",
    "meta": "https://www.metacareers.com",
    "netflix": "https://jobs.netflix.com",
    "amazon": "https://www.amazon.jobs"
}

def get_company_careers_url(company: str) -> Optional[str]:
    comp_key = company.lower().strip()
    if comp_key in COMPANY_CAREERS_MAP:
        return COMPANY_CAREERS_MAP[comp_key]
    
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', company).lower()
    fallback_urls = [
        f"https://www.{clean_name}.com/careers",
        f"https://careers.{clean_name}.com",
        f"https://www.{clean_name}.com/about/careers"
    ]
    
    for url in fallback_urls:
        try:
            res = requests.head(url, timeout=3, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
            if res.status_code < 400:
                return url
        except Exception:
            continue
            
    return None

def get_alternative_portal_url(title: str, company: str) -> str:
    """Generate a high-relevancy active search query link on standard alternative portals (LinkedIn Jobs)."""
    import urllib.parse
    query_str = urllib.parse.quote(f"{title} {company}")
    return f"https://www.linkedin.com/jobs/search/?keywords={query_str}"

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
        from app.models.user import User
        active_profiles = db.query(UserProfile).filter(UserProfile.consent_given == True).all()
        
        # Map user_id to email and matched jobs for email notification
        user_matches_map = {}
        for profile in active_profiles:
            user = db.query(User).filter(User.id == profile.user_id).first()
            if user:
                user_matches_map[profile.user_id] = {
                    "email": user.email,
                    "matches": []
                }
        
        for crawler in crawlers:
            try:
                results_summary["processed_crawlers"].append(crawler.name)
                logger.info(f"[Task] Crawling '{crawler.name}'...")
                
                # Fetch raw jobs
                crawled_jobs: List[JobCreate] = crawler.fetch_jobs(query, limit=limit_per_source)
                results_summary["jobs_crawled_count"] += len(crawled_jobs)
                
                for job_data in crawled_jobs:
                    # Validate crawled job URL. Check if it's a simulated Glassdoor link or similar
                    is_active = True
                    url_check_needed = "glassdoor.com" in job_data.url.lower() or "indeed.com" in job_data.url.lower()
                    
                    if url_check_needed:
                        try:
                            # Perform a GET request to verify the link
                            res = requests.get(job_data.url, timeout=4, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True)
                            if res.status_code == 404 or "page not found" in res.text.lower() or "404 error" in res.text.lower():
                                is_active = False
                        except Exception:
                            is_active = False
                    
                    if not is_active:
                        logger.info(f"[LinkFix] Dead job link detected for {job_data.company}: {job_data.url}. Searching for company career site...")
                        career_url = get_company_careers_url(job_data.company)
                        if career_url:
                            logger.info(f"[LinkFix] Resolved official careers URL for {job_data.company}: {career_url}. Updating listing link.")
                            job_data.url = career_url
                        else:
                            # Fallback 2: Construct live search link on alternative portal (e.g. LinkedIn Jobs)
                            alt_url = get_alternative_portal_url(job_data.title, job_data.company)
                            logger.info(f"[LinkFix] Career page missing. Resolved cross-portal search URL for {job_data.company}: {alt_url}. Updating listing link.")
                            job_data.url = alt_url

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
                                
                                # Add to matched list for notification email
                                if profile.user_id in user_matches_map:
                                    user_matches_map[profile.user_id]["matches"].append({
                                        "job": new_job,
                                        "match_score": score
                                    })
                
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
                
        # Send career digest email alerts for compiled matches
        try:
            from app.services.notification.email import send_job_match_notification
            for user_id, user_data in user_matches_map.items():
                if user_data["matches"]:
                    logger.info(f"[Task] Dispatching career digest email to user: {user_data['email']}")
                    send_job_match_notification(
                        email_to=user_data["email"],
                        query=query,
                        matches=user_data["matches"]
                    )
        except Exception as mail_err:
            logger.error(f"[Task] Careers digest mail dispatch failed: {str(mail_err)}")
                
    finally:
        if should_close:
            db.close()
        
    logger.info(f"[Task] Crawl and match process completed. Summary: {results_summary}")
    return results_summary
