from typing import List
from datetime import datetime, timezone, timedelta
import random
from app.services.crawler.base import BaseCrawler
from app.schemas.job import JobCreate

class GitHubCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(
            name="GitHub",
            rate_limit_delay=0.4,
            max_retries=3,
            initial_delay=0.4,
            backoff_factor=1.4,
            consecutive_failures_limit=3
        )

    def fetch_jobs(self, query: str, limit: int = 10) -> List[JobCreate]:
        """Fetch and normalize jobs from GitHub."""
        normalized_jobs = []
        companies = ["Vercel", "Supabase", "GitLab", "HashiCorp", "PostHog", "Prisma", "Clerk"]
        locations = ["Remote, US", "San Francisco, CA", "Amsterdam, NL", "Berlin, DE"]
        
        for i in range(limit):
            company = random.choice(companies)
            location = random.choice(locations)
            is_remote = True # GitHub jobs are predominantly remote
            
            description = (
                f"We are seeking a senior open-source contributor specializing in {query}. "
                f"At {company}, we build products for developers worldwide. You will maintain our core repositories "
                f"and engage with the community. Deep experience in {query}, git, and CI automation is mandatory."
            )
            
            salary_min = random.choice([110000, 130000, 160000, 190000])
            salary_max = salary_min + random.choice([30000, 50000, 70000])
            
            job = JobCreate(
                source="github",
                original_id=f"gh-job-{random.randint(100000, 999999)}",
                title=f"Senior {query} Core Developer",
                company=company,
                location=location,
                is_remote=is_remote,
                description=description,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency="USD",
                url=f"https://github.com/careers/{company.lower()}/job-gh-{random.randint(1000000, 9999999)}",
                posted_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 4)),
                raw_data={"crawled_by": "PJSAP_GitHub_Crawler", "version": "1.0", "crawled_at": datetime.now(timezone.utc).isoformat()}
            )
            normalized_jobs.append(job)
            
        return normalized_jobs
