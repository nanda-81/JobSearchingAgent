
import pytest
from datetime import datetime, timezone
import requests
import random
from pydantic import ValidationError
from app.schemas.job import JobCreate
from app.services.crawler.base import BaseCrawler, CircuitBreakerOpenException
from app.services.crawler.linkedin import LinkedInCrawler
from app.services.crawler.github import GitHubCrawler
from app.services.crawler.indeed import IndeedCrawler
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
def test_linkedin_crawler_normalization(monkeypatch):
    crawler = LinkedInCrawler()
    
    mock_html = """
    <div class="job-search-card" data-entity-urn="urn:li:jobPosting:101">
        <h3 class="base-search-card__title">Python Engineer</h3>
        <a class="hidden-nested-link">LinkedInCorp1</a>
        <span class="job-search-card__location">Remote</span>
        <time datetime="2026-05-25">2026-05-25</time>
        <a href="https://www.linkedin.com/jobs/view/101">Link</a>
    </li>
    <div class="job-search-card" data-entity-urn="urn:li:jobPosting:102">
        <h3 class="base-search-card__title">Python Dev</h3>
        <a class="hidden-nested-link">LinkedInCorp2</a>
        <span class="job-search-card__location">Remote</span>
        <time datetime="2026-05-25">2026-05-25</time>
        <a href="https://www.linkedin.com/jobs/view/102">Link</a>
    </li>
    <div class="job-search-card" data-entity-urn="urn:li:jobPosting:103">
        <h3 class="base-search-card__title">Senior Python Architect</h3>
        <a class="hidden-nested-link">LinkedInCorp3</a>
        <span class="job-search-card__location">Remote</span>
        <time datetime="2026-05-25">2026-05-25</time>
        <a href="https://www.linkedin.com/jobs/view/103">Link</a>
    </li>
    """
    
    def mock_request(method, url, **kwargs):
        response = requests.Response()
        response.status_code = 200
        response._content = mock_html.encode("utf-8")
        return response
        
    monkeypatch.setattr(requests, "request", mock_request)
    
    jobs = crawler.fetch_jobs("Python", limit=3)
    assert len(jobs) == 3
    for job in jobs:
        assert job.source == "linkedin"
        if job.salary_max is not None and job.salary_min is not None:
            assert job.salary_max >= job.salary_min
        assert job.posted_at is not None

def test_github_crawler_normalization(monkeypatch):
    crawler = GitHubCrawler()
    
    mock_xml = """
    <rss xmlns:dc="http://purl.org/dc/elements/1.1/">
        <channel>
            <item>
                <title>ReactCorp1: React Engineer</title>
                <dc:creator>ReactCorp1</dc:creator>
                <description>A React role</description>
                <pubDate>Mon, 25 May 2026 12:00:00 +0000</pubDate>
                <link>https://weworkremotely.com/jobs/101</link>
                <guid>wwr-101</guid>
            </item>
            <item>
                <title>ReactCorp2: React Architect</title>
                <dc:creator>ReactCorp2</dc:creator>
                <description>Another React role</description>
                <pubDate>Mon, 25 May 2026 12:00:00 +0000</pubDate>
                <link>https://weworkremotely.com/jobs/102</link>
                <guid>wwr-102</guid>
            </item>
        </channel>
    </rss>
    """
    
    def mock_request(method, url, **kwargs):
        response = requests.Response()
        response.status_code = 200
        response._content = mock_xml.encode("utf-8")
        return response
        
    monkeypatch.setattr(requests, "request", mock_request)
    
    jobs = crawler.fetch_jobs("React", limit=2)
    assert len(jobs) == 2
    for job in jobs:
        assert job.source == "github"
        assert job.is_remote is True
        assert "weworkremotely.com" in job.url or job.url.startswith("https://")

# 4. Celery background task integration test (SQLite testing database)
def test_crawl_and_normalize_jobs_task(db, monkeypatch):
    # Seed user profile and user to cover matching engine and career digests notification paths
    import uuid
    from app.models.user import User
    from app.models.profile import UserProfile
    
    test_user = User(
        id=uuid.uuid4(),
        email="test_notify@example.com",
        hashed_password="hashed_password",
        full_name="Notify User",
        is_active=True
    )
    db.add(test_user)
    db.flush()
    
    test_profile = UserProfile(
        user_id=test_user.id,
        target_titles=["Django", "Developer"],
        target_locations=["Remote"],
        experience_level="mid",
        consent_given=True
    )
    db.add(test_profile)
    db.commit()

    # Mock the live crawlers to avoid non-deterministic live network dependencies
    def mock_fetch_linkedin(self, query: str, limit: int = 10):
        return [
            JobCreate(
                source="linkedin",
                original_id="li-mock-1",
                title=f"Mock LinkedIn Django Developer",
                company="LinkedInCorp",
                location="Remote",
                is_remote=True,
                description="Mock Django description",
                salary_min=100000,
                salary_max=120000,
                salary_currency="USD",
                url="https://linkedin.com/jobs/mock-1",
                posted_at=datetime.now(timezone.utc)
            )
        ]

    def mock_fetch_github(self, query: str, limit: int = 10):
        return [
            JobCreate(
                source="github",
                original_id="gh-mock-1",
                title=f"Mock GitHub Django Developer",
                company="GitHubCorp",
                location="Remote",
                is_remote=True,
                description="Mock Django description",
                salary_min=110000,
                salary_max=130000,
                salary_currency="USD",
                url="https://weworkremotely.com/jobs/mock-1",
                posted_at=datetime.now(timezone.utc)
            )
        ]

    def mock_fetch_indeed(self, query: str, limit: int = 10):
        return [
            JobCreate(
                source="indeed",
                original_id="id-mock-1",
                title=f"Mock Indeed Django Developer",
                company="IndeedCorp",
                location="Remote",
                is_remote=True,
                description="Mock Django description",
                salary_min=105000,
                salary_max=125000,
                salary_currency="USD",
                url="https://indeed.com/jobs/mock-1",
                posted_at=datetime.now(timezone.utc)
            )
        ]

    monkeypatch.setattr(LinkedInCrawler, "fetch_jobs", mock_fetch_linkedin)
    monkeypatch.setattr(GitHubCrawler, "fetch_jobs", mock_fetch_github)
    monkeypatch.setattr(IndeedCrawler, "fetch_jobs", mock_fetch_indeed)

    # Seed random generator to ensure exact duplicate outputs on second crawl
    random.seed(42)
    results = crawl_and_normalize_jobs(query="Django", limit_per_source=2, db_session=db)
    
    assert results["status"] == "success"
    crawled_count = results["jobs_crawled_count"]
    assert crawled_count > 0
    assert results["new_jobs_saved"] == crawled_count
    
    # Assert database persisted crawled jobs
    db_jobs = db.query(Job).all()
    assert len(db_jobs) == crawled_count
    
    # Seed random generator with the exact same seed to generate identical mock postings
    random.seed(42)
    results_dup = crawl_and_normalize_jobs(query="Django", limit_per_source=2, db_session=db)
    
    # Because of deduplication, new_jobs_saved must be exactly 0
    assert results_dup["new_jobs_saved"] == 0
    
    # Confirm DB size remains identical
    assert len(db.query(Job).all()) == crawled_count


def test_get_company_careers_url(monkeypatch):
    from app.tasks.jobs import get_company_careers_url
    
    # 1. Test mapped company
    assert get_company_careers_url("Google") == "https://careers.google.com"
    
    # 2. Test fallback urls with mock requests.head
    calls = []
    def mock_head(url, **kwargs):
        calls.append(url)
        response = requests.Response()
        if "microsoft" in url:
            response.status_code = 200
        else:
            response.status_code = 404
        return response
        
    monkeypatch.setattr(requests, "head", mock_head)
    assert get_company_careers_url("Microsoft") == "https://careers.microsoft.com"
    
def test_get_alternative_portal_url():
    from app.tasks.jobs import get_alternative_portal_url
    url = get_alternative_portal_url("Python Developer", "Tech Corp")
    assert "linkedin.com" in url
    assert "Python%20Developer%20Tech%20Corp" in url

def test_indeed_crawler_normalization(monkeypatch):
    crawler = IndeedCrawler()
    
    # Mock successful JSON response from Arbeitnow API
    def mock_request(method, url, **kwargs):
        response = requests.Response()
        response.status_code = 200
        response._content = b'{"data": [{"slug": "indeed-job-1", "title": "Indeed Engineer", "company_name": "IndeedCorp", "location": "Remote", "remote": true, "description": "Django role", "created_at": 1715000000, "url": "https://arbeitnow.com/job/1", "tags": ["python"], "job_types": ["full-time"]}]}'
        return response
        
    monkeypatch.setattr(requests, "request", mock_request)
    
    jobs = crawler.fetch_jobs("Django", limit=1)
    assert len(jobs) == 1
    assert jobs[0].source == "arbeitnow"
    assert jobs[0].title == "Indeed Engineer"
    assert jobs[0].company == "IndeedCorp"

def test_linkedin_crawler_mocked_normalization(monkeypatch):
    crawler = LinkedInCrawler()
    
    mock_html = """
    <div class="job-search-card" data-entity-urn="urn:li:jobPosting:12345">
        <h3 class="base-search-card__title">LinkedIn Mock Engineer</h3>
        <a class="hidden-nested-link">LinkedInCorp</a>
        <span class="job-search-card__location">Remote</span>
        <time datetime="2026-05-25">2026-05-25</time>
        <a href="https://www.linkedin.com/jobs/view/12345?refId=1">Link</a>
    </li>
    """
    
    def mock_request(method, url, **kwargs):
        response = requests.Response()
        response.status_code = 200
        response._content = mock_html.encode("utf-8")
        return response
        
    monkeypatch.setattr(requests, "request", mock_request)
    
    jobs = crawler.fetch_jobs("Django", limit=1)
    assert len(jobs) == 1
    assert jobs[0].source == "linkedin"
    assert jobs[0].title == "LinkedIn Mock Engineer"
    assert jobs[0].company == "LinkedInCorp"

def test_github_crawler_mocked_normalization(monkeypatch):
    crawler = GitHubCrawler()
    
    mock_xml = """
    <rss xmlns:dc="http://purl.org/dc/elements/1.1/">
        <channel>
            <item>
                <title>Speechify Inc: Senior Software Engineer (Web)</title>
                <dc:creator>Speechify Inc</dc:creator>
                <description>A Django description</description>
                <pubDate>Mon, 25 May 2026 12:00:00 +0000</pubDate>
                <link>https://weworkremotely.com/jobs/1</link>
                <guid>wwr-1</guid>
            </item>
        </channel>
    </rss>
    """
    
    def mock_request(method, url, **kwargs):
        response = requests.Response()
        response.status_code = 200
        response._content = mock_xml.encode("utf-8")
        return response
        
    monkeypatch.setattr(requests, "request", mock_request)
    
    jobs = crawler.fetch_jobs("Django", limit=1)
    assert len(jobs) == 1
    assert jobs[0].source == "github"
    assert jobs[0].title == "Senior Software Engineer (Web)"
    assert jobs[0].company == "Speechify Inc"


