import logging
import xml.etree.ElementTree as ET
from typing import List
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from app.services.crawler.base import BaseCrawler
from app.schemas.job import JobCreate

logger = logging.getLogger(__name__)

class GitHubCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(
            name="GitHub",
            rate_limit_delay=1.0,
            max_retries=3,
            initial_delay=1.0,
            backoff_factor=2.0,
            consecutive_failures_limit=3
        )

    def fetch_jobs(self, query: str, limit: int = 10) -> List[JobCreate]:
        """Fetch and scrape remote developer jobs matching the query from the WeWorkRemotely RSS feed."""
        url = "https://weworkremotely.com/remote-jobs.rss"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        try:
            response = self.request_with_retry(url, headers=headers)
            xml_data = response.text
            
            # Parse XML root
            root = ET.fromstring(xml_data.encode("utf-8"))
            items = root.findall(".//item")
            
            normalized_jobs = []
            current_time = datetime.now(timezone.utc)
            limit_date = current_time - timedelta(days=7)
            query_lower = query.lower().strip()
            
            for item in items:
                # Parse title & company
                title_raw = item.find("title")
                title_text = title_raw.text.strip() if title_raw is not None else ""
                if not title_text:
                    continue
                
                company = "Undisclosed Company"
                title = title_text
                if ":" in title_text:
                    parts = title_text.split(":", 1)
                    company = parts[0].strip()
                    title = parts[1].strip()
                
                # Check dc:creator namespace for company name
                creator = item.find("{http://purl.org/dc/elements/1.1/}creator")
                if creator is not None and creator.text:
                    company = creator.text.strip()
                
                description_raw = item.find("description")
                description = description_raw.text if description_raw is not None else "No description provided."
                
                # 1. TIME-WINDOW FILTERING: Normalize posted_at date & drop entries older than 7 days
                pub_date_raw = item.find("pubDate")
                pub_date_str = pub_date_raw.text.strip() if pub_date_raw is not None else ""
                try:
                    posted_at = parsedate_to_datetime(pub_date_str)
                    if posted_at.tzinfo is None:
                        posted_at = posted_at.replace(tzinfo=timezone.utc)
                except Exception:
                    posted_at = current_time
                    
                if posted_at < limit_date:
                    logger.debug(f"[{self.name}] Skipping old job '{title}' - posted at {posted_at.isoformat()}")
                    continue
                
                # 2. LOCAL SEARCH FILTERING: Verify query matching in title or description
                title_desc_lower = f"{title.lower()} {description.lower()}"
                if query_lower not in title_desc_lower:
                    continue
                
                # Parse link & guid
                link_raw = item.find("link")
                job_url = link_raw.text.strip() if link_raw is not None else "https://weworkremotely.com"
                
                guid_raw = item.find("guid")
                original_id = guid_raw.text.strip() if guid_raw is not None else f"wwr-{posted_at.timestamp()}"
                
                job = JobCreate(
                    source="github",
                    original_id=original_id,
                    title=title,
                    company=company,
                    location="Remote",
                    is_remote=True,
                    description=description,
                    salary_min=None,
                    salary_max=None,
                    salary_currency="USD",
                    url=job_url,
                    posted_at=posted_at,
                    raw_data={
                        "crawled_by": "PJSAP_WeWorkRemotely_RSS_Scraper",
                        "crawled_at": current_time.isoformat()
                    }
                )
                normalized_jobs.append(job)
                if len(normalized_jobs) >= limit:
                    break
                    
            logger.info(f"[{self.name}] Crawled {len(normalized_jobs)} live active jobs under 7 days old.")
            return normalized_jobs
            
        except Exception as e:
            logger.error(f"Error parsing live RSS feeds from WeWorkRemotely: {str(e)}")
            raise e
