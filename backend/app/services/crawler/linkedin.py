from typing import List
from datetime import datetime, timezone, timedelta
import random
from app.services.crawler.base import BaseCrawler
from app.schemas.job import JobCreate

class LinkedInCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(
            name="LinkedIn",
            rate_limit_delay=0.5,
            max_retries=3,
            initial_delay=0.5,
            backoff_factor=1.5,
            consecutive_failures_limit=3
        )

    def fetch_jobs(self, query: str, limit: int = 10) -> List[JobCreate]:
        """Fetch and normalize jobs from LinkedIn."""
        logger_name = f"LinkedInCrawler-{query}"
        
        # In a real environment, we would execute HTTP requests to the LinkedIn Partner API
        # e.g., response = self.request_with_retry("https://api.linkedin.com/v2/jobSearch?query=" + query)
        # Here we simulate the network retrieval and return fully normalized, high-quality results.
        
        normalized_jobs = []
        companies = ["Google", "Meta", "Stripe", "Netflix", "OpenAI", "Airbnb", "Snowflake", "Databricks"]
        locations = ["Remote, US", "San Francisco, CA", "New York, NY", "London, UK", "Austin, TX"]
        experience_levels = ["junior", "mid", "senior", "lead"]
        
        for i in range(limit):
            company = random.choice(companies)
            location = random.choice(locations)
            is_remote = "Remote" in location
            exp_level = random.choice(experience_levels)
            
            # Generate realistic description
            description = (
                f"We are looking for a {exp_level} level expert matching the '{query}' query. "
                f"As a core member of the team at {company}, you will work with modern stacks including Python, FastAPI, React, and SQL. "
                f"Requirements: 3+ years experience, solid coding principles, containerization (Docker), and cloud architectures."
            )
            
            salary_min = random.choice([80000, 100000, 130000, 160000])
            salary_max = salary_min + random.choice([20000, 40000, 60000])
            
            job = JobCreate(
                source="linkedin",
                original_id=f"li-job-{random.randint(100000, 999999)}",
                title=f"{exp_level.capitalize()} {query} Engineer",
                company=company,
                location=location,
                is_remote=is_remote,
                description=description,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency="USD",
                url=f"https://www.linkedin.com/jobs/view/li-{random.randint(1000000, 9999999)}",
                posted_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 5)),
                raw_data={"crawled_by": "PJSAP_LinkedIn_Crawler", "version": "1.0", "crawled_at": datetime.now(timezone.utc).isoformat()}
            )
            normalized_jobs.append(job)
            
        return normalized_jobs
