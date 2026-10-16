"""
Phase 12: Production Readiness, Security Hardening, and Subsystem Integrity Tests.
Tests health probes, security response headers, error masking, auth handling,
end-to-end integration, and database migration integrity.
"""

import io
import fitz
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

def create_synthetic_pdf(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    data = doc.tobytes()
    doc.close()
    return data

def test_health_check_endpoint_and_subsystem_readiness(client: TestClient):
    """Verifies that the /health endpoint returns HTTP 200, status, version, and component probes."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert data["version"] == settings.VERSION
    assert "environment" in data
    
    # Subsystem readiness probes
    assert "components" in data
    components = data["components"]
    assert "database" in components
    assert "status" in components["database"]
    assert "pdf_parser" in components
    assert components["pdf_parser"]["available"] is True
    assert "docx_parser" in components
    assert components["docx_parser"]["available"] is True
    assert "ai_provider" in components
    assert "active" in components["ai_provider"]
    assert "auth" in components
    assert "engine" in components["auth"]

def test_security_response_headers(client: TestClient):
    """Verifies security hardening headers are injected across all API responses."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    headers = response.headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("x-xss-protection") == "1; mode=block"
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"

def test_root_endpoint_metadata(client: TestClient):
    """Verifies root API descriptor returns valid metadata and docs configuration."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == settings.PROJECT_NAME
    assert data["version"] == settings.VERSION
    assert "api_v1" in data

def test_validation_error_handler_structure(client: TestClient):
    """Verifies 422 validation errors return standardized structured responses without sensitive data."""
    # Send empty body to an endpoint requiring structured JSON
    response = client.post("/api/v1/jobs/match", json={})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "errors" in data
    assert isinstance(data["errors"], list)
    assert len(data["errors"]) > 0
    assert "field" in data["errors"][0]
    assert "message" in data["errors"][0]

def test_cors_options_preflight(client: TestClient):
    """Verifies CORS preflight handling allows configured origins."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type,Authorization"
    }
    response = client.options("/api/v1/health", headers=headers)
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"

def test_unauthenticated_protected_route_rejection(client: TestClient):
    """Verifies strictly protected endpoints reject requests with missing or malformed auth tokens."""
    # Missing Authorization header
    resp_missing = client.get("/api/v1/profile/me")
    assert resp_missing.status_code == 401
    assert "detail" in resp_missing.json()

    # Invalid token format / garbage token
    resp_invalid = client.get("/api/v1/profile/me", headers={"Authorization": "Bearer invalid.mock.jwt.token"})
    assert resp_invalid.status_code == 401
    assert "detail" in resp_invalid.json()

def test_database_migrations_integrity():
    """Verifies that all versioned SQL migrations exist and contain RLS policies and table definitions."""
    migrations_dir = Path(__file__).resolve().parent.parent / "migrations"
    assert migrations_dir.exists(), "Migrations directory must exist"
    
    migration_files = sorted(list(migrations_dir.glob("*.sql")))
    assert len(migration_files) >= 3, "Expected at least 3 SQL migrations"
    
    filenames = [f.name for f in migration_files]
    assert "001_initial_schema.sql" in filenames
    assert "002_learning_roadmap.sql" in filenames
    assert "003_reports_and_analytics.sql" in filenames
    
    # Check that Row Level Security (RLS) is enforced across migrations
    full_sql = " ".join([f.read_text(encoding="utf-8") for f in migration_files])
    assert "ENABLE ROW LEVEL SECURITY" in full_sql
    assert "CREATE POLICY" in full_sql
    assert "auth.uid()" in full_sql

def test_end_to_end_resume_to_report_pipeline(client: TestClient):
    """
    Simulates complete candidate pipeline:
    1. Upload resume PDF
    2. Run ATS analysis
    3. Run Job Match
    4. Generate Learning Roadmap
    5. Save and preview Progress Report
    """
    resume_text = (
        "Jane Doe\n"
        "jane.doe@example.com | San Francisco, CA\n\n"
        "PROFESSIONAL SUMMARY\n"
        "Software Engineer with 3 years experience building scalable backend services.\n\n"
        "EDUCATION\n"
        "BS in Computer Science, State University\n\n"
        "TECHNICAL SKILLS\n"
        "Python, React, PostgreSQL, Docker, AWS, Git, REST APIs\n\n"
        "WORK EXPERIENCE\n"
        "Software Engineer at Acme Tech (2022 - Present)\n"
        "Built microservices in Python and improved latency by 35%.\n"
    )
    pdf_bytes = create_synthetic_pdf(resume_text)

    # 1. Upload resume
    upload_resp = client.post(
        "/api/v1/resume/upload",
        files={"file": ("jane_resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    )
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    resume_id = upload_data["resume_id"]
    assert resume_id is not None
    assert upload_data["extraction_status"] == "success"
    assert upload_data["word_count"] > 10
    assert len(upload_data["detected_sections"]) > 0


    # 2. Run ATS Analysis
    analyze_resp = client.post(f"/api/v1/resume/{resume_id}/analyze")
    assert analyze_resp.status_code == 200
    analysis_data = analyze_resp.json()
    assert analysis_data["overall_score"] > 0
    assert "extracted_skills" in analysis_data
    
    # Flatten extracted skill names
    skills_flat = []
    for category_skills in analysis_data["extracted_skills"].values():
        skills_flat.extend([s["name"] for s in category_skills])
    assert any("python" in s.lower() for s in skills_flat)

    # 3. Match Job
    job_payload = {
        "resume_id": resume_id,
        "company": "Tech Corp",
        "role": "Full Stack Developer",
        "job_description": "Seeking Full Stack Engineer skilled in Python, React, PostgreSQL, Kubernetes, and GraphQL."
    }
    match_resp = client.post("/api/v1/jobs/match", json=job_payload)
    assert match_resp.status_code == 200
    match_data = match_resp.json()
    assert match_data["overall_match_score"] > 0
    missing_skill_names = [m["name"] for m in match_data.get("missing_evidence", [])]

    # 4. Generate Learning Roadmap
    roadmap_payload = {
        "target_role": "Full Stack Developer",
        "target_company": "Tech Corp",
        "resume_skills": skills_flat,
        "target_skills": ["Python", "React", "PostgreSQL", "Kubernetes", "GraphQL"],
        "missing_skills": missing_skill_names or ["Kubernetes"],
        "target_duration_weeks": 6,
        "weekly_study_hours": 10
    }
    roadmap_resp = client.post("/api/v1/learning/roadmap/generate", json=roadmap_payload)
    assert roadmap_resp.status_code == 200
    roadmap_data = roadmap_resp.json()
    assert len(roadmap_data["milestones"]) > 0

    # 5. Save and verify report snapshot
    report_save_payload = {
        "resume_id": resume_id,
        "report_title": "Jane Doe Evaluation Report",
        "target_role": "Full Stack Developer",
        "job_match_id": match_data.get("match_id")
    }
    save_resp = client.post("/api/v1/reports/save", json=report_save_payload)
    assert save_resp.status_code == 201
    saved_report = save_resp.json()
    assert saved_report["id"] is not None
    assert saved_report["overall_score"] == analysis_data["overall_score"]
    assert saved_report["match_score"] == match_data["overall_match_score"]


