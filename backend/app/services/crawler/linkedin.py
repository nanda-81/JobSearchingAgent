import logging
import re
from typing import List
from datetime import datetime, timezone, timedelta
from app.services.crawler.base import BaseCrawler
from app.schemas.job import JobCreate

logger = logging.getLogger(__name__)

class LinkedInCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(
            name="LinkedIn",
            rate_limit_delay=1.0,
            max_retries=3,
            initial_delay=1.0,
            backoff_factor=2.0,
            consecutive_failures_limit=3
        )

    def fetch_jobs(self, query: str, limit: int = 10) -> List[JobCreate]:
        """Fetch and scrape jobs from the LinkedIn guest jobs search API."""
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={query}&location=Remote"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        try:
            response = self.request_with_retry(url, headers=headers)
            html = response.text
            
            # Extract list card HTML segments
            cards = re.findall(r'<div[^>]*class="[^"]*job-search-card[^"]*".*?</li>', html, re.DOTALL)
            if not cards:
                # Fallback: find div blocks if </li> tag structure differs
                cards = re.findall(r'<div[^>]*class="[^"]*job-search-card[^"]*".*?(?:</div>\s*</div>\s*</div>)', html, re.DOTALL)
                
            normalized_jobs = []
            current_time = datetime.now(timezone.utc)
            limit_date = current_time - timedelta(days=7)
            
            for card in cards:
                # 1. Parse URN Job ID
                urn_match = re.search(r'data-entity-urn="urn:li:jobPosting:(\d+)"', card)
                if not urn_match:
                    continue
                job_id = urn_match.group(1)
                
                # 2. Parse Title
                title_match = re.search(r'<h3 class="base-search-card__title">[\s\n]*([^<]+?)[\s\n]*</h3>', card)
                if not title_match:
                    continue
                title = title_match.group(1).strip()
                
                # 3. Parse Company
                company_match = re.search(r'<a class="hidden-nested-link"[^>]*>[\s\n]*([^<]+?)[\s\n]*</a>', card)
                if not company_match:
                    company_match = re.search(r'<h4 class="base-search-card__subtitle">[\s\n]*([^<]+?)[\s\n]*</h4>', card)
                company = company_match.group(1).strip() if company_match else "Undisclosed Company"
                
                # 4. Parse Location
                location_match = re.search(r'<span class="job-search-card__location">[\s\n]*([^<]+?)[\s\n]*</span>', card)
                location = location_match.group(1).strip() if location_match else "Remote"
                
                # 5. Parse Publication Date & Apply Time-Window Filter (Max 7 Days)
                date_match = re.search(r'<time[^>]*datetime="([^"]+)"', card)
                if date_match:
                    try:
                        posted_at = datetime.fromisoformat(date_match.group(1))
                        if posted_at.tzinfo is None:
                            posted_at = posted_at.replace(tzinfo=timezone.utc)
                    except Exception:
                        posted_at = current_time
                else:
                    posted_at = current_time
                
                # Check 7-day age hurdle
                if posted_at < limit_date:
                    logger.info(f"[{self.name}] Skipping job '{title}' - posted at {posted_at.isoformat()} (older than 7 days)")
                    continue
                
                # 6. Parse URL
                url_match = re.search(r'href="([^"]+)"', card)
                job_url = url_match.group(1).strip() if url_match else f"https://www.linkedin.com/jobs/view/{job_id}"
                # Clean query strings from URL
                job_url = job_url.split("?")[0]
                
                job = JobCreate(
                    source="linkedin",
                    original_id=job_id,
                    title=title,
                    company=company,
                    location=location,
                    is_remote="Remote" in location or "remote" in location.lower(),
                    description=f"Active Live Job Posting from LinkedIn for {title}. Check full details at application link.",
                    salary_min=None,
                    salary_max=None,
                    salary_currency="USD",
                    url=job_url,
                    posted_at=posted_at,
                    raw_data={
                        "crawled_by": "PJSAP_LinkedIn_Live_Scraper",
                        "crawled_at": current_time.isoformat()
                    }
                )
                normalized_jobs.append(job)
                if len(normalized_jobs) >= limit:
                    break
                    
            logger.info(f"[{self.name}] Crawled {len(normalized_jobs)} live active jobs under 7 days old.")
            return normalized_jobs
            
        except Exception as e:
            logger.error(f"Error scraping live jobs from LinkedIn guest API: {str(e)}")
            raise e

