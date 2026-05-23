from fastapi import status
from app.models.user import User
from app.models.profile import UserProfile

def test_register_user_success(client, db):
    payload = {
        "email": "test@example.com",
        "password": "securepassword123",
        "full_name": "Test User"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "password" not in data
    
    # Check that a User record was indeed written
    user = db.query(User).filter(User.email == "test@example.com").first()
    assert user is not None
    assert user.full_name == "Test User"
    
    # Check that a default empty UserProfile was automatically initialized
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    assert profile is not None
    assert profile.target_titles == []
    assert profile.experience_level == "mid"

def test_register_duplicate_email(client):
    payload = {
        "email": "dup@example.com",
        "password": "securepassword123",
        "full_name": "Original User"
    }
    # Register first time
    response1 = client.post("/api/v1/auth/register", json=payload)
    assert response1.status_code == status.HTTP_201_CREATED
    
    # Register second time
    response2 = client.post("/api/v1/auth/register", json=payload)
    assert response2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response2.json()["detail"]

def test_login_and_token_generation(client):
    register_payload = {
        "email": "login@example.com",
        "password": "mypassword123",
        "full_name": "Login User"
    }
    client.post("/api/v1/auth/register", json=register_payload)
    
    # Authenticate
    login_payload = {
        "username": "login@example.com",
        "password": "mypassword123"
    }
    response = client.post("/api/v1/auth/token", data=login_payload)
    assert response.status_code == status.HTTP_200_OK
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

def test_login_incorrect_password(client):
    register_payload = {
        "email": "wrong@example.com",
        "password": "mypassword123",
        "full_name": "Wrong User"
    }
    client.post("/api/v1/auth/register", json=register_payload)
    
    login_payload = {
        "username": "wrong@example.com",
        "password": "incorrectpassword"
    }
    response = client.post("/api/v1/auth/token", data=login_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_me_endpoint(client):
    # Register and login to get JWT
    register_payload = {
        "email": "me@example.com",
        "password": "mypassword123",
        "full_name": "Me User"
    }
    client.post("/api/v1/auth/register", json=register_payload)
    
    login_response = client.post("/api/v1/auth/token", data={
        "username": "me@example.com",
        "password": "mypassword123"
    })
    token = login_response.json()["access_token"]
    
    # Access endpoint with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == "me@example.com"

def test_get_me_unauthorized(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
