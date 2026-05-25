import logging
from typing import List
from datetime import datetime, timezone
from app.services.crawler.base import BaseCrawler
from app.schemas.job import JobCreate

logger = logging.getLogger(__name__)

class IndeedCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(
            name="Indeed (via Arbeitnow)",
            rate_limit_delay=1.0,
            max_retries=3,
            initial_delay=1.0,
            backoff_factor=2.0,
            consecutive_failures_limit=3
        )

    def fetch_jobs(self, query: str, limit: int = 10) -> List[JobCreate]:
        """Fetch and normalize jobs from the Arbeitnow API."""
        url = f"https://arbeitnow.com/api/job-board-api?search={query}"
        
        try:
            response = self.request_with_retry(url)
            data = response.json()
            raw_jobs = data.get("data", [])
            
            normalized_jobs = []
            for raw_job in raw_jobs[:limit]:
                # Parse created_at timestamp (unix epoch integer)
                created_at_val = raw_job.get("created_at")
                try:
                    posted_at = datetime.fromtimestamp(int(created_at_val), tz=timezone.utc)
                except Exception:
                    posted_at = datetime.now(timezone.utc)
                
                job = JobCreate(
                    source="arbeitnow",
                    original_id=raw_job.get("slug", f"an-{raw_job.get('title')}-{raw_job.get('company_name')}"[:50]),
                    title=raw_job.get("title", f"Software Engineer ({query})"),
                    company=raw_job.get("company_name", "Undisclosed Company"),
                    location=raw_job.get("location", "Remote"),
                    is_remote=raw_job.get("remote", True),
                    description=raw_job.get("description", "No description provided."),
                    salary_min=None,
                    salary_max=None,
                    salary_currency="USD",
                    url=raw_job.get("url"),
                    posted_at=posted_at,
                    raw_data={
                        "crawled_by": "PJSAP_Arbeitnow_Crawler",
                        "tags": raw_job.get("tags", []),
                        "job_types": raw_job.get("job_types", []),
                        "crawled_at": datetime.now(timezone.utc).isoformat()
                    }
                )
                normalized_jobs.append(job)
                
            return normalized_jobs
        except Exception as e:
            logger.error(f"Error fetching jobs from Arbeitnow API: {str(e)}")
            raise e
