import jwt
import time
from fastapi.testclient import TestClient
from app.core.config import settings


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "CareerLens API"
    assert "version" in data
    assert data["documentation"] == "/docs"

def test_health_endpoint(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data

def test_dashboard_endpoint(client: TestClient):
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["is_demo"] is True
    assert "demo_notice" in data
    assert data["candidate_name"] == "Alex Rivera"
    assert data["overall_readiness_score"] == 78
    assert "ats_compatibility" in data["metrics"]
    assert len(data["skill_coverage"]) > 0
    assert len(data["recent_reports"]) > 0

def test_resume_status_endpoint(client: TestClient):
    response = client.get("/api/v1/resume/status")
    assert response.status_code == 200
    data = response.json()
    assert data["services_configured"] is True
    assert data["pdf_parser_available"] is True
    assert data["docx_parser_available"] is True
    assert "status_message" in data
    assert "Phase 4" in data["roadmap_phase"]

def test_resume_analyze_valid_payload_not_implemented(client: TestClient):
    payload = {
        "file_name": "alex_rivera_resume.pdf",
        "file_type": "pdf",
        "target_role": "Full Stack Engineer"
    }
    response = client.post("/api/v1/resume/analyze", json=payload)
    assert response.status_code == 501
    data = response.json()
    assert data["status"] == "not_implemented"
    assert data["request_validated"] is True
    assert data["file_name"] == "alex_rivera_resume.pdf"
    assert "scheduled_phase" in data

def test_resume_analyze_invalid_payload_validation_error(client: TestClient):
    payload = {
        "file_name": "resume.pdf"
    }
    response = client.post("/api/v1/resume/analyze", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["detail"] == "Request validation failed"
    assert len(data["errors"]) > 0

def test_jobs_match_valid_payload_returns_match(client: TestClient):
    payload = {
        "company": "FinTech Velocity Labs",
        "role": "Full Stack Software Engineer",
        "job_description": "We are looking for a Python and React engineer to build financial telemetry platforms with high throughput and reliable APIs."
    }
    response = client.post("/api/v1/jobs/match", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["company"] == "FinTech Velocity Labs"
    assert data["role"] == "Full Stack Software Engineer"
    assert "overall_match_score" in data
    assert "hard_skill_match_score" in data

def test_jobs_match_invalid_short_description(client: TestClient):
    payload = {
        "company": "Stripe",
        "role": "Engineer",
        "job_description": "Too short"
    }
    response = client.post("/api/v1/jobs/match", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "too brief" in data["detail"].lower()

def test_reports_returns_empty_list(client: TestClient):
    response = client.get("/api/v1/reports")
    assert response.status_code == 200
    data = response.json()
    assert data["reports"] == []
    assert data["total"] == 0
    assert "No stored reports found" in data["message"]

def test_cors_headers_allowed_origin(client: TestClient):
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

# ====================================================================
# PHASE 3: AUTHENTICATION & SECURITY BOUNDARY TESTS
# ====================================================================

def test_auth_status_endpoint(client: TestClient):
    response = client.get("/api/v1/auth/status")
    assert response.status_code == 200
    data = response.json()
    assert data["auth_provider"] == "Supabase Auth"
    assert "supabase_configured" in data

def test_auth_me_unauthenticated_blocked_with_401(client: TestClient):
    # Calling protected endpoint without Bearer token must be rejected with 401
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "Missing Bearer access token" in response.json()["detail"]

def test_auth_me_invalid_token_blocked_with_401(client: TestClient):
    # Calling with malformed token must be rejected with 401
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer totally-invalid-garbage-token"}
    )
    assert response.status_code == 401

def test_auth_me_valid_token_resolves_identity(client: TestClient):
    # Construct a test JWT for candidate "user-student-123"
    test_user_id = "00000000-0000-0000-0000-000000000001"
    token = jwt.encode(
        {"sub": test_user_id, "email": "candidate@example.com", "role": "authenticated", "exp": int(time.time()) + 3600},
        key=settings.SUPABASE_JWT_SECRET or "test-dev-secret",
        algorithm="HS256"
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user_id
    assert data["email"] == "candidate@example.com"
    assert data["role"] == "authenticated"

def test_profile_me_unauthenticated_blocked(client: TestClient):
    response = client.get("/api/v1/profile/me")
    assert response.status_code == 401

def test_profile_me_authenticated_returns_user_profile(client: TestClient):
    test_user_id = "00000000-0000-0000-0000-000000000002"
    token = jwt.encode(
        {"sub": test_user_id, "email": "student2@example.com", "role": "authenticated"},
        key=settings.SUPABASE_JWT_SECRET or "test-dev-secret",
        algorithm="HS256"
    )
    response = client.get(
        "/api/v1/profile/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    # The profile ID is guaranteed to match the token sub
    assert data["id"] == test_user_id
    assert data["email"] == "student2@example.com"

def test_reports_user_unauthenticated_blocked(client: TestClient):
    response = client.get("/api/v1/reports/user")
    assert response.status_code == 401

def test_reports_user_authenticated_isolated(client: TestClient):
    test_user_id = "00000000-0000-0000-0000-000000000003"
    token = jwt.encode(
        {"sub": test_user_id, "email": "student3@example.com"},
        key=settings.SUPABASE_JWT_SECRET or "test-dev-secret",
        algorithm="HS256"
    )
    response = client.get(
        "/api/v1/reports/user",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "reports" in data
    assert isinstance(data["reports"], list)
