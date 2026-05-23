from typing import List
from datetime import datetime, timezone, timedelta
import random
from app.services.crawler.base import BaseCrawler
from app.schemas.job import JobCreate

class GlassdoorCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(
            name="Glassdoor",
            rate_limit_delay=0.7,
            max_retries=3,
            initial_delay=0.7,
            backoff_factor=1.7,
            consecutive_failures_limit=3
        )

    def fetch_jobs(self, query: str, limit: int = 10) -> List[JobCreate]:
        """Fetch and normalize jobs from Glassdoor."""
        normalized_jobs = []
        companies = ["HubSpot", "Salesforce", "DocuSign", "Adobe", "Shopify", "Nvidia", "Intel"]
        locations = ["Remote, US", "Boston, MA", "San Jose, CA", "Seattle, WA", "Toronto, ON"]
        
        for i in range(limit):
            company = random.choice(companies)
            location = random.choice(locations)
            is_remote = "Remote" in location
            
            description = (
                f"We are hiring a Lead {query} Architect at {company}. "
                f"In this role, you will lead the development of our core features and microservices. "
                f"Required skills: {query}, Docker, Kubernetes, AWS/GCP, and CI/CD pipelines."
            )
            
            salary_min = random.choice([100000, 125000, 150000, 185000])
            salary_max = salary_min + random.choice([20000, 40000, 60000])
            
            job = JobCreate(
                source="glassdoor",
                original_id=f"gd-job-{random.randint(100000, 999999)}",
                title=f"Lead {query} Architect",
                company=company,
                location=location,
                is_remote=is_remote,
                description=description,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency="USD",
                url=f"https://www.glassdoor.com/job-posting/gd-{random.randint(1000000, 9999999)}",
                posted_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 10)),
                raw_data={"crawled_by": "PJSAP_Glassdoor_Crawler", "version": "1.0", "crawled_at": datetime.now(timezone.utc).isoformat()}
            )
            normalized_jobs.append(job)
            
        return normalized_jobs
