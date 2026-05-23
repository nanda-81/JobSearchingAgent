import pytest
from datetime import datetime, timezone
import requests
import random
from pydantic import ValidationError
from app.schemas.job import JobCreate
from app.services.crawler.base import BaseCrawler, CircuitBreakerOpenException
from app.services.crawler.linkedin import LinkedInCrawler
from app.services.crawler.github import GitHubCrawler
from app.tasks.jobs import crawl_and_normalize_jobs, generate_job_hash, Job

# 1. Pydantic validation tests
def test_job_create_validation_success():
    job = JobCreate(
        source="test",
        original_id="123",
        title="Software Engineer",
        company="Tech Inc",
        location="Remote",
        description="A great Python role.",
        salary_min=100000,
        salary_max=150000,
        url="https://tech.inc/jobs/123",
        posted_at=datetime.now(timezone.utc)
    )
    assert job.title == "Software Engineer"
    assert job.salary_min == 100000

def test_job_create_invalid_salary_range():
    with pytest.raises(ValidationError):
        JobCreate(
            source="test",
            original_id="123",
            title="Software Engineer",
            company="Tech Inc",
            location="Remote",
            description="A great Python role.",
            salary_min=150000,
            salary_max=100000,  # Invalid: max < min
            url="https://tech.inc/jobs/123",
            posted_at=datetime.now(timezone.utc)
        )

# 2. BaseCrawler Resilience tests (Exponential Backoff & Circuit Breaker)
class FailingCrawler(BaseCrawler):
    def __init__(self, failure_limit=2):
        super().__init__(
            name="FailingCrawler",
            rate_limit_delay=0.0,
            max_retries=3,
            initial_delay=0.01,
            backoff_factor=1.5,
            consecutive_failures_limit=failure_limit,
            circuit_breaker_cooldown=2
        )
        self.call_count = 0

    def fetch_jobs(self, query: str, limit: int = 10):
        # Trigger requests inside to test backoff and retries
        self.call_count += 1
        return self.request_with_retry("http://localhost:12345/dummy")

def test_exponential_backoff_success_on_retry(monkeypatch):
    crawler = FailingCrawler(failure_limit=3)
    attempts = []

    # Mock requests.request to fail twice and then succeed
    def mock_request(method, url, **kwargs):
        attempts.append(url)
        if len(attempts) < 3:
            raise requests.RequestException("Temporary server error")
        
        # Return a mock successful response
        response = requests.Response()
        response.status_code = 200
        return response

    monkeypatch.setattr(requests, "request", mock_request)
    
    response = crawler.fetch_jobs("Python")
    assert response.status_code == 200
    assert len(attempts) == 3  # Failed 2 times, succeeded on 3rd attempt

def test_circuit_breaker_tripping(monkeypatch):
    crawler = FailingCrawler(failure_limit=2)
    
    def mock_request(method, url, **kwargs):
        raise requests.RequestException("Fatal network error")
        
    monkeypatch.setattr(requests, "request", mock_request)
    
    # 1. First execution fails, triggering consecutive failures up to limit (2)
    with pytest.raises(requests.RequestException):
        crawler.fetch_jobs("Python")
        
    # 2. Second execution fails, reaching the limit of 2 failures and tripping the circuit
    with pytest.raises(requests.RequestException):
        crawler.fetch_jobs("Python")
        
    # 3. Third execution should fast-fail with CircuitBreakerOpenException immediately without making a request
    with pytest.raises(CircuitBreakerOpenException):
        crawler.fetch_jobs("Python")

# 3. Job crawler implementations test
def test_linkedin_crawler_normalization():
    random.seed(42)
    crawler = LinkedInCrawler()
    jobs = crawler.fetch_jobs("Python", limit=3)
    assert len(jobs) == 3
    for job in jobs:
        assert job.source == "linkedin"
        assert job.salary_max >= job.salary_min
        assert job.posted_at is not None

def test_github_crawler_normalization():
    random.seed(42)
    crawler = GitHubCrawler()
    jobs = crawler.fetch_jobs("React", limit=2)
    assert len(jobs) == 2
    for job in jobs:
        assert job.source == "github"
        assert job.is_remote is True
        assert job.url.startswith("https://github.com/careers/")

# 4. Celery background task integration test (SQLite testing database)
def test_crawl_and_normalize_jobs_task(db):
    # Seed random generator to ensure exact duplicate outputs on second crawl
    random.seed(42)
    results = crawl_and_normalize_jobs(query="Django", limit_per_source=2, db_session=db)
    
    assert results["status"] == "success"
    assert results["jobs_crawled_count"] == 10  # 5 crawlers * 2 jobs = 10
    assert results["new_jobs_saved"] == 10
    
    # Assert database persisted 10 jobs
    db_jobs = db.query(Job).all()
    assert len(db_jobs) == 10
    
    # Seed random generator with the exact same seed to generate identical mock postings
    random.seed(42)
    results_dup = crawl_and_normalize_jobs(query="Django", limit_per_source=2, db_session=db)
    
    # Because of deduplication, new_jobs_saved must be exactly 0
    assert results_dup["new_jobs_saved"] == 0
    
    # Confirm DB size remains 10
    assert len(db.query(Job).all()) == 10
