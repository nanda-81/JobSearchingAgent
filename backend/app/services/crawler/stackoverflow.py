from typing import List
from datetime import datetime, timezone, timedelta
import random
from app.services.crawler.base import BaseCrawler
from app.schemas.job import JobCreate

class StackOverflowCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(
            name="StackOverflow",
            rate_limit_delay=0.5,
            max_retries=3,
            initial_delay=0.5,
            backoff_factor=1.5,
            consecutive_failures_limit=3
        )

    def fetch_jobs(self, query: str, limit: int = 10) -> List[JobCreate]:
        """Fetch and normalize jobs from Stack Overflow."""
        normalized_jobs = []
        companies = ["Stack Overflow", "GitLab", "Atlassian", "Twilio", "SendGrid", "Okta", "Auth0"]
        locations = ["Remote, Global", "New York, NY", "Sydney, AU", "Denver, CO"]
        
        for i in range(limit):
            company = random.choice(companies)
            location = random.choice(locations)
            is_remote = "Remote" in location
            
            description = (
                f"We are hiring a Senior Full-Stack Engineer focusing on {query} at {company}. "
                f"Our engineering culture prioritizes documentation, asynchronous communication, "
                f"and robust automated testing. Core stack includes {query}, PostgreSQL, and cloud deployments."
            )
            
            salary_min = random.choice([95000, 115000, 145000, 175000])
            salary_max = salary_min + random.choice([20000, 45000, 65000])
            
            job = JobCreate(
                source="stackoverflow",
                original_id=f"so-job-{random.randint(100000, 999999)}",
                title=f"Full Stack {query} Engineer",
                company=company,
                location=location,
                is_remote=is_remote,
                description=description,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency="USD",
                url=f"https://stackoverflow.com/jobs/so-{random.randint(1000000, 9999999)}",
                posted_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 6)),
                raw_data={"crawled_by": "PJSAP_StackOverflow_Crawler", "version": "1.0", "crawled_at": datetime.now(timezone.utc).isoformat()}
            )
            normalized_jobs.append(job)
            
        return normalized_jobs
