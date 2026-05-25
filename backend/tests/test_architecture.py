import os
import json
import yaml

def test_sql_schema_existence_and_contents():
    schema_path = os.path.join(
        os.path.dirname(__file__), "..", "app", "db", "schema.sql"
    )
    assert os.path.exists(schema_path), f"Schema file not found at {schema_path}"
    
    with open(schema_path, "r", encoding="utf-8") as f:
        content = f.read().lower()
        
    # Check that crucial tables are defined
    assert "create table if not exists users" in content
    assert "create table if not exists user_profiles" in content
    assert "create table if not exists jobs" in content
    assert "create table if not exists job_matches" in content
    assert "create table if not exists social_credentials" in content
    assert "create table if not exists audit_logs" in content
    
    # Check that crucial indices are defined
    assert "create index if not exists idx_users_email" in content
    assert "create index if not exists idx_jobs_posted_at" in content
    assert "create index if not exists idx_job_matches_user_status" in content

def test_openapi_spec_validity():
    openapi_path = os.path.join(
        os.path.dirname(__file__), "..", "openapi.json"
    )
    assert os.path.exists(openapi_path), f"OpenAPI file not found at {openapi_path}"
    
    with open(openapi_path, "r", encoding="utf-8") as f:
        spec = json.load(f)
        
    assert spec["openapi"].startswith("3.")
    assert "paths" in spec
    assert "/auth/register" in spec["paths"]
    assert "/auth/token" in spec["paths"]
    assert "/profile" in spec["paths"]
    assert "/jobs" in spec["paths"]
    assert "/matches" in spec["paths"]
    assert "/social/credentials" in spec["paths"]
    assert "/gdpr/export" in spec["paths"]
    assert "/gdpr/delete" in spec["paths"]

def test_docker_compose_validity():
    compose_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "docker-compose.yml"
    )
    assert os.path.exists(compose_path), f"docker-compose.yml not found at {compose_path}"
    
    with open(compose_path, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)
        
    assert "services" in compose_data
    services = compose_data["services"]
    
    assert "postgres" in services
    assert "redis" in services
    assert "elasticsearch" in services
    assert "rabbitmq" in services
    assert "backend" in services
    assert "frontend" in services

def test_health_check_endpoint(client):
    response = client.get("/health")
    assert response.status_code in [200, 503]
    
def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to PJSAP" in response.json()["message"]

