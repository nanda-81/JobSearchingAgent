from fastapi import status

def _get_auth_headers(client, email="profile@example.com", password="mypassword123"):
    register_payload = {
        "email": email,
        "password": password,
        "full_name": "Profile User"
    }
    client.post("/api/v1/auth/register", json=register_payload)
    
    login_response = client.post("/api/v1/auth/token", data={
        "username": email,
        "password": password
    })
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_get_profile_default(client):
    headers = _get_auth_headers(client)
    
    response = client.get("/api/v1/profile", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["target_titles"] == []
    assert data["target_locations"] == []
    assert data["salary_min"] is None
    assert data["experience_level"] == "mid"

def test_update_profile_success(client):
    headers = _get_auth_headers(client, email="update@example.com")
    
    update_payload = {
        "target_titles": ["Software Engineer", "Tech Lead"],
        "target_locations": ["Remote", "San Francisco"],
        "salary_min": 120000,
        "experience_level": "senior",
        "job_types": ["Full-time"],
        "keywords": ["Python", "FastAPI"],
        "excluded_keywords": ["COBOL"],
        "resume_url": "https://portfolio.me/resume.pdf"
    }
    
    response = client.put("/api/v1/profile", json=update_payload, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["target_titles"] == ["Software Engineer", "Tech Lead"]
    assert data["target_locations"] == ["Remote", "San Francisco"]
    assert data["salary_min"] == 120000
    assert data["experience_level"] == "senior"
    assert data["keywords"] == ["Python", "FastAPI"]
    assert data["resume_url"] == "https://portfolio.me/resume.pdf"
    
    # Confirm it gets persisted by retrieving it
    get_response = client.get("/api/v1/profile", headers=headers)
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()["experience_level"] == "senior"

def test_update_profile_invalid_salary(client):
    headers = _get_auth_headers(client, email="invalid@example.com")
    
    # Send a negative salary
    update_payload = {
        "salary_min": -5000
    }
    response = client.put("/api/v1/profile", json=update_payload, headers=headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_profile_endpoints_unauthorized(client):
    response1 = client.get("/api/v1/profile")
    assert response1.status_code == status.HTTP_401_UNAUTHORIZED
    
    response2 = client.put("/api/v1/profile", json={})
    assert response2.status_code == status.HTTP_401_UNAUTHORIZED
