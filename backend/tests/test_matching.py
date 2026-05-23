import pytest
from datetime import datetime, timezone
from fastapi import status
from app.models.job import Job
from app.models.profile import UserProfile
from app.models.match import JobMatch
from app.services.matching.engine import calculate_match_score
from app.services.matching.search_client import JobSearchClient

# 1. Matching Engine Unit Tests
def test_matching_exact_match():
    # Setup highly compatible job and profile
    job = Job(
        title="Senior Python Developer",
        company="FastAPI Corp",
        location="Remote",
        is_remote=True,
        description="We are seeking a senior expert who loves coding in Python and FastAPI.",
        salary_max=160000,
        salary_min=140000,
        salary_currency="USD",
        url="http://corp.com/job/1"
    )
    
    profile = UserProfile(
        target_titles=["Python Developer", "Software Engineer"],
        target_locations=["Remote"],
        salary_min=130000,
        experience_level="senior",
        job_types=["Full-time"],
        keywords=["Python", "FastAPI"],
        excluded_keywords=["PHP", "Java"]
    )
    
    score, details = calculate_match_score(job, profile)
    assert score > 0.80  # Should be extremely high match
    assert details["title_match"] > 0.0
    assert details["location_match"] > 0.0
    assert details["salary_match"] > 0.0
    assert details["experience_match"] > 0.0
    assert "FastAPI" in details["matched_keywords"]

def test_matching_excluded_keywords():
    job = Job(
        title="PHP & Python Engineer",
        company="Legacy Systems",
        location="Remote",
        description="We are updating our PHP codebase to Python.",
        salary_max=120000,
        url="http://corp.com/job/2"
    )
    
    profile = UserProfile(
        target_titles=["Python Engineer"],
        target_locations=["Remote"],
        salary_min=100000,
        keywords=["Python"],
        excluded_keywords=["PHP"]  # Should trigger strict block
    )
    
    score, details = calculate_match_score(job, profile)
    assert score == 0.0
    assert details.get("blocked") is True
    assert "PHP" in details.get("reason", "")

def test_matching_salary_mismatch():
    job = Job(
        title="Junior Python Coder",
        company="Startup Inc",
        location="Remote",
        description="Join us for a junior role.",
        salary_max=70000,
        url="http://corp.com/job/3"
    )
    
    profile = UserProfile(
        target_titles=["Python Coder"],
        target_locations=["Remote"],
        salary_min=100000,  # Min salary too high
        experience_level="junior"
    )
    
    score, details = calculate_match_score(job, profile)
    assert details["salary_match"] == 0.0  # Mismatch penalty
    assert "Salary too low" in " ".join(details["reasons"])

# 2. Search Client Graceful Fallback Tests
def test_search_client_database_fallback(db):
    # Seed database with jobs
    job1 = Job(
        source="linkedin",
        original_id="111",
        title="Vue Frontend Developer",
        company="VueCorp",
        location="San Francisco, CA",
        description="We are building Vue SPAs.",
        url="http://vuecorp.com/1",
        posted_at=datetime.now(timezone.utc),
        hash_key="hash-1"
    )
    job2 = Job(
        source="github",
        original_id="222",
        title="Kubernetes SRE Engineer",
        company="CloudTech",
        location="Remote",
        description="Kubernetes orchestration expert.",
        url="http://cloudtech.com/2",
        posted_at=datetime.now(timezone.utc),
        hash_key="hash-2"
    )
    db.add(job1)
    db.add(job2)
    db.commit()
    
    # Initialize search client (which falls back to SQL because Elasticsearch is offline)
    client = JobSearchClient()
    assert client.es is None
    
    # Perform search using fallback logic
    results = client.search_jobs("Vue", db=db)
    assert len(results) == 1
    assert results[0].title == "Vue Frontend Developer"
    
    results_sre = client.search_jobs("Kubernetes", db=db)
    assert len(results_sre) == 1
    assert results_sre[0].company == "CloudTech"

# 3. HTTP Endpoint Integration Tests
def _get_auth_token(client):
    register_payload = {
        "email": "matching@example.com",
        "password": "mypassword123",
        "full_name": "Matching User"
    }
    client.post("/api/v1/auth/register", json=register_payload)
    
    login_response = client.post("/api/v1/auth/token", data={
        "username": "matching@example.com",
        "password": "mypassword123"
    })
    return login_response.json()["access_token"]

def test_jobs_api_endpoint(client, db):
    token = _get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    job = Job(
        source="indeed",
        original_id="333",
        title="AWS DevOps Lead",
        company="AWS Partners",
        location="Remote",
        description="AWS DevOps Lead role.",
        url="http://awspartners.com/3",
        posted_at=datetime.now(timezone.utc),
        hash_key="hash-3"
    )
    db.add(job)
    db.commit()
    
    response = client.get("/api/v1/jobs?q=DevOps", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "AWS DevOps Lead"

def test_matches_api_endpoints(client, db):
    token = _get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Query current user ID from DB
    from app.models.user import User
    user = db.query(User).filter(User.email == "matching@example.com").first()
    
    job = Job(
        source="github",
        original_id="444",
        title="Django backend engineer",
        company="PythonShop",
        location="Remote",
        description="Django backend engineer.",
        url="http://pythonshop.com/4",
        posted_at=datetime.now(timezone.utc),
        hash_key="hash-4"
    )
    db.add(job)
    db.flush()
    
    match = JobMatch(
        user_id=user.id,
        job_id=job.id,
        match_score=0.85,
        matching_details={"reason": "Matched keyword Django"},
        status="pending"
    )
    db.add(match)
    db.commit()
    
    # 1. Retrieve matches
    response = client.get("/api/v1/matches", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["match_score"] == 0.85
    assert response.json()[0]["job"]["title"] == "Django backend engineer"
    
    # 2. Update status
    response_update = client.put(
        f"/api/v1/matches/{job.id}/status",
        json={"status": "saved"},
        headers=headers
    )
    assert response_update.status_code == status.HTTP_200_OK
    
    # 3. Verify status persisted
    db.refresh(match)
    assert match.status == "saved"
