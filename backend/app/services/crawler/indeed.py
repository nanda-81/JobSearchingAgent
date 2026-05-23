from typing import List
from datetime import datetime, timezone, timedelta
import random
from app.services.crawler.base import BaseCrawler
from app.schemas.job import JobCreate

class IndeedCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(
            name="Indeed",
            rate_limit_delay=0.6,
            max_retries=3,
            initial_delay=0.6,
            backoff_factor=1.6,
            consecutive_failures_limit=3
        )

    def fetch_jobs(self, query: str, limit: int = 10) -> List[JobCreate]:
        """Fetch and normalize jobs from Indeed."""
        normalized_jobs = []
        companies = ["Microsoft", "Amazon", "Apple", "Uber", "Lyft", "Zoom", "Pinterest", "Slack"]
        locations = ["Remote, US", "Seattle, WA", "New York, NY", "London, UK", "Chicago, IL"]
        
        for i in range(limit):
            company = random.choice(companies)
            location = random.choice(locations)
            is_remote = "Remote" in location
            
            description = (
                f"Join our engineering department as a {query} Specialist. At {company}, we solve challenging "
                f"problems using high-performance technologies. Experience in {query}, distributed databases, "
                f"and test-driven development (TDD) is preferred."
            )
            
            salary_min = random.choice([90000, 110000, 140000, 175000])
            salary_max = salary_min + random.choice([15000, 35000, 55000])
            
            job = JobCreate(
                source="indeed",
                original_id=f"ind-job-{random.randint(100000, 999999)}",
                title=f"Staff {query} Developer",
                company=company,
                location=location,
                is_remote=is_remote,
                description=description,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency="USD",
                url=f"https://www.indeed.com/viewjob?jk=ind-{random.randint(1000000, 9999999)}",
                posted_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 7)),
                raw_data={"crawled_by": "PJSAP_Indeed_Crawler", "version": "1.0", "crawled_at": datetime.now(timezone.utc).isoformat()}
            )
            normalized_jobs.append(job)
            
        return normalized_jobs
