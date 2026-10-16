import pytest
import jwt
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
import httpx

from app.main import app
from app.core.config import settings
from app.services.github_service import github_service
from app.services.profile_connection_service import profile_connection_service
from app.services.evidence_extractor import evidence_extractor
from app.services.claim_evidence_matcher import claim_evidence_matcher
from app.services.evidence_verification_service import evidence_verification_service
import fitz

@pytest.fixture
def client():
    return TestClient(app)

def make_test_token(user_id: str, email: str = "student@example.com") -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": "authenticated",
        "aud": "authenticated",
    }
    secret = settings.SUPABASE_JWT_SECRET or "test_secret_for_jwt_validation_32_bytes_long"
    return jwt.encode(payload, secret, algorithm="HS256")

def create_synthetic_pdf(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    data = doc.tobytes()
    doc.close()
    return data

# Mock GitHub responses
MOCK_USER_PAYLOAD = {
    "login": "octocat",
    "name": "The Octocat",
    "public_repos": 8,
    "followers": 4200,
    "html_url": "https://github.com/octocat",
    "created_at": "2011-01-25T18:44:36Z",
}

MOCK_REPOS_PAYLOAD = [
    {
        "name": "careerlens",
        "full_name": "octocat/careerlens",
        "description": "AI-powered resume and career readiness analyzer built with Python, FastAPI, and React.",
        "language": "Python",
        "html_url": "https://github.com/octocat/careerlens",
        "stargazers_count": 45,
        "forks_count": 12,
        "default_branch": "main",
        "topics": ["career", "resume-analyzer", "fastapi"],
    },
    {
        "name": "distributed-cache",
        "full_name": "octocat/distributed-cache",
        "description": "High throughput distributed caching system implemented in Go and Redis.",
        "language": "Go",
        "html_url": "https://github.com/octocat/distributed-cache",
        "stargazers_count": 88,
        "forks_count": 19,
        "default_branch": "main",
        "topics": ["go", "distributed-systems", "redis"],
    }
]

def make_mock_github_get(status_code=200, user_not_found=False, rate_limited=False):
    def mock_get(url, *args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.headers = {}

        if rate_limited:
            mock_resp.status_code = 403
            mock_resp.headers = {"x-ratelimit-reset": "1735689600"}
            mock_resp.json.return_value = {"message": "API rate limit exceeded"}
            return mock_resp

        if user_not_found:
            mock_resp.status_code = 404
            mock_resp.json.return_value = {"message": "Not Found"}
            return mock_resp

        url_str = str(url)
        if "/users/octocat/repos" in url_str:
            mock_resp.json.return_value = MOCK_REPOS_PAYLOAD
        elif "/users/octocat" in url_str:
            mock_resp.json.return_value = MOCK_USER_PAYLOAD
        elif "/languages" in url_str:
            if "careerlens" in url_str:
                mock_resp.json.return_value = {"Python": 50000, "TypeScript": 20000, "HTML": 2000}
            else:
                mock_resp.json.return_value = {"Go": 35000}
        elif "/readme" in url_str:
            mock_resp.text = "# CareerLens\nAn AI-powered resume and career readiness platform with automated test suite."
        elif "/contents" in url_str:
            mock_resp.json.return_value = [
                {"name": "test_api.py", "type": "file"},
                {"name": "requirements.txt", "type": "file"},
                {"name": "package.json", "type": "file"},
                {"name": "README.md", "type": "file"},
            ]
        else:
            mock_resp.json.return_value = {}
        return mock_resp
    return mock_get

MOCK_GITHUB_PROFILE_DATA = {
    "username": "octocat",
    "name": "The Octocat",
    "html_url": "https://github.com/octocat",
    "avatar_url": "",
    "bio": "Coding",
    "public_repos_count": 2,
    "followers_count": 4200,
    "created_at": "2011-01-25T18:44:36Z",
    "repositories": [
        {
            "name": "careerlens",
            "full_name": "octocat/careerlens",
            "description": "AI-powered resume analyzer with Python, FastAPI, and React.",
            "html_url": "https://github.com/octocat/careerlens",
            "primary_language": "Python",
            "languages": {"Python": 50000, "TypeScript": 20000},
            "stars": 45,
            "forks": 12,
            "default_branch": "main",
            "updated_at": "2026-10-15T12:00:00Z",
            "readme_excerpt": "# CareerLens\nAn AI-powered resume and career readiness platform with automated test suite.",
            "has_test_suite": True,
            "test_artifacts": ["test_api.py"],
            "config_artifacts": ["requirements.txt", "package.json"],
            "topics": ["career", "resume-analyzer", "fastapi"],
        }
    ],
    "language_breakdown": {"Python": 71.4, "TypeScript": 28.6},
    "retrieved_at": "2026-10-16T12:00:00Z",
    "status": "connected",
}

# ----------------------------------------------------------------------
# 1. GitHub Service Validation & Security (SSRF & Host Blocking)
# ----------------------------------------------------------------------
def test_github_service_validation_success():
    assert github_service.extract_and_validate_username("octocat") == "octocat"
    assert github_service.extract_and_validate_username("https://github.com/octocat") == "octocat"
    assert github_service.extract_and_validate_username("http://github.com/octocat/careerlens") == "octocat"
    assert github_service.extract_and_validate_username("@octocat") == "octocat"

def test_github_service_rejects_ssrf_and_malicious_hosts():
    with pytest.raises(HTTPException) as exc1:
        github_service.extract_and_validate_username("https://evil-phishing.com/octocat")
    assert exc1.value.status_code == 400
    assert "security violation" in exc1.value.detail.lower()

    with pytest.raises(HTTPException) as exc2:
        github_service.extract_and_validate_username("http://127.0.0.1/admin")
    assert exc2.value.status_code == 400

    with pytest.raises(HTTPException) as exc3:
        github_service.extract_and_validate_username("invalid..username--!")
    assert exc3.value.status_code == 400

def test_github_service_handles_rate_limiting():
    with patch("httpx.Client.get", side_effect=make_mock_github_get(rate_limited=True)):
        with pytest.raises(HTTPException) as exc:
            github_service.fetch_user_profile_and_repos("octocat", force_refresh=True)
        assert exc.value.status_code == 429
        assert "rate limit" in exc.value.detail.lower()

def test_github_service_handles_missing_user():
    with patch("httpx.Client.get", side_effect=make_mock_github_get(user_not_found=True)):
        with pytest.raises(HTTPException) as exc:
            github_service.fetch_user_profile_and_repos("octocat", force_refresh=True)
        assert exc.value.status_code == 404
        assert "not found" in exc.value.detail.lower()

def test_github_service_discovers_repos_languages_and_tests():
    with patch("httpx.Client.get", side_effect=make_mock_github_get()):
        data = github_service.fetch_user_profile_and_repos("octocat", force_refresh=True)
        assert data["username"] == "octocat"
        assert len(data["repositories"]) == 2
        repo1 = data["repositories"][0]
        assert repo1["name"] == "careerlens"
        assert repo1["has_test_suite"] is True
        assert "test_api.py" in repo1["test_artifacts"]
        assert "Python" in repo1["languages"]
        assert "Python" in data["language_breakdown"]

# ----------------------------------------------------------------------
# 2. Provider Adapters (LeetCode, Portfolio, LinkedIn)
# ----------------------------------------------------------------------
def test_leetcode_adapter_validation():
    conn = profile_connection_service.connect_profile("leetcode", "student_coder")
    assert conn["status"] == "connected"
    assert "leetcode.com/u/student_coder" in conn["username_or_url"]

def test_portfolio_adapter_validation_and_ssrf():
    # Loopback must be rejected with 400
    with pytest.raises(HTTPException) as exc:
        profile_connection_service.connect_profile("portfolio", "http://127.0.0.1:8000/private")
    assert exc.value.status_code == 400

def test_linkedin_adapter_reviewable_notice():
    conn = profile_connection_service.connect_profile("linkedin", "https://linkedin.com/in/studentdev")
    assert conn["status"] == "connected"
    assert "automated scraping restricted" in conn["retrieval_status"].lower()

def test_unsupported_provider_rejected():
    with pytest.raises(HTTPException) as exc:
        profile_connection_service.connect_profile("unsupported_platform", "handle")
    assert exc.value.status_code == 400
    assert "unsupported" in exc.value.detail.lower()

# ----------------------------------------------------------------------
# 3. Evidence Claim Extraction from Resume
# ----------------------------------------------------------------------
def test_evidence_extractor_finds_projects_and_skills():
    synthetic_resume = {
        "raw_text": (
            "Alex Student\nalex@example.com\n\n"
            "PROJECTS\n"
            "- CareerLens: Built an AI-powered resume and career readiness analyzer with React, Python, and FastAPI.\n"
            "- Distributed Cache: High throughput cache system in Go and Redis.\n\n"
            "SKILLS\n"
            "Python, FastAPI, React, Docker, Go, Redis"
        ),
        "sections": {
            "projects": (
                "- CareerLens: Built an AI-powered resume and career readiness analyzer with React, Python, and FastAPI.\n"
                "- Distributed Cache: High throughput cache system in Go and Redis."
            ),
            "skills": "Python, FastAPI, React, Docker, Go, Redis"
        }
    }

    claims = evidence_extractor.extract_resume_claims(synthetic_resume)
    assert len(claims) >= 2
    proj_claims = [c for c in claims if c["claim_type"] == "project"]
    proj_names = [c["project_name"].lower() for c in proj_claims if c["project_name"]]
    assert any("careerlens" in p for p in proj_names)
    assert any("distributed cache" in p for p in proj_names)

# ----------------------------------------------------------------------
# 4. Claim Evidence Matcher: Supported, Partial, Unverified, Inaccessible
# ----------------------------------------------------------------------
def test_claim_evidence_matcher_evaluates_verdicts():
    claims = [
        {
            "claim_id": "c1",
            "claim_type": "project",
            "project_name": "CareerLens",
            "original_claim": "Built CareerLens with Python and React",
            "claimed_technologies": ["Python", "React", "FastAPI"],
        },
        {
            "claim_id": "c2",
            "claim_type": "project",
            "project_name": "SecretInternalTool",
            "original_claim": "Built proprietary internal tool",
            "claimed_technologies": ["Java"],
        },
        {
            "claim_id": "c3",
            "claim_type": "technical_skill",
            "project_name": None,
            "original_claim": "Python",
            "claimed_technologies": ["Python"],
        }
    ]

    mock_connections = [
        {
            "id": "github",
            "status": "connected",
            "username_or_url": "https://github.com/octocat",
            "metadata": {
                "repositories": [
                    {
                        "name": "careerlens",
                        "full_name": "octocat/careerlens",
                        "languages": {"Python": 45000, "TypeScript": 10000},
                        "readme_excerpt": "CareerLens: React and Python application with tests.",
                        "has_test_suite": True,
                        "test_artifacts": ["test_api.py"],
                        "html_url": "https://github.com/octocat/careerlens"
                    }
                ],
                "language_breakdown": {"Python": 75.0, "TypeScript": 25.0}
            }
        }
    ]

    result = claim_evidence_matcher.match_claims(claims, mock_connections)
    assert result["total_claims"] == 3
    assert result["supported_claims"] >= 1  # CareerLens matches
    assert result["unverified_claims"] >= 1  # SecretInternalTool not on GitHub
    assert result["verification_score"] > 0
    assert result["disclaimer"] != ""

    # Check limitations field
    for claim in result["claims"]:
        assert claim["evidence_limitations"] != ""
        assert claim["reason"] != ""

# ----------------------------------------------------------------------
# 5. Full End-to-End API Integration Tests
# ----------------------------------------------------------------------
def test_api_profiles_connections_flow(client):
    token = make_test_token("user-777")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET connections (returns template)
    res1 = client.get("/api/v1/profiles/connections", headers=headers)
    assert res1.status_code == 200
    assert len(res1.json()["connections"]) >= 5

    # 2. Connect LeetCode
    res2 = client.post(
        "/api/v1/profiles/connections",
        json={"platform_id": "leetcode", "username_or_url": "octocat_coder"},
        headers=headers
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "connected"

    # 3. Disconnect LeetCode
    res3 = client.delete("/api/v1/profiles/connections/leetcode", headers=headers)
    assert res3.status_code == 200

def test_api_evidence_verification_end_to_end(client):
    token = make_test_token("user-verifier-123")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Upload a synthetic resume with a clear project
    resume_text = (
        "Alice Developer\n"
        "alice@example.com\n\n"
        "PROJECTS\n"
        "- CareerLens: Built an AI-powered resume and career readiness analyzer with React, Python, and FastAPI.\n\n"
        "SKILLS\n"
        "Python, React, FastAPI, Docker, SQL"
    )
    pdf_bytes = create_synthetic_pdf(resume_text)
    upload_res = client.post(
        "/api/v1/resume/upload",
        files={"file": ("alice_evidence_resume.pdf", pdf_bytes, "application/pdf")},
        headers=headers
    )
    assert upload_res.status_code == 200
    resume_id = upload_res.json()["resume_id"]

    # 2. Run Evidence Verification with mocked GitHub API
    with patch.object(github_service, "fetch_user_profile_and_repos", return_value=MOCK_GITHUB_PROFILE_DATA):
        verify_payload = {
            "resume_id": resume_id,
            "github_username_or_url": "octocat"
        }
        verify_res = client.post("/api/v1/evidence/verify", json=verify_payload, headers=headers)
        assert verify_res.status_code == 200
        data = verify_res.json()
        assert data["resume_id"] == resume_id
        assert data["total_claims"] >= 1
        assert "claims" in data
        assert data["disclaimer"] != ""
        verif_id = data["verification_id"]

        # 3. Retrieve stored verification report
        get_res = client.get(f"/api/v1/evidence/{verif_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["verification_id"] == verif_id

def test_api_evidence_verification_ownership_enforcement(client):
    token_a = make_test_token("user-a-owner")
    token_b = make_test_token("user-b-intruder")

    resume_text = "Bob\nPROJECTS\n- Microservice: Built Python API."
    pdf_bytes = create_synthetic_pdf(resume_text)
    upload_res = client.post(
        "/api/v1/resume/upload",
        files={"file": ("bob_resume.pdf", pdf_bytes, "application/pdf")},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert upload_res.status_code == 200
    resume_id = upload_res.json()["resume_id"]

    with patch.object(github_service, "fetch_user_profile_and_repos", return_value=MOCK_GITHUB_PROFILE_DATA):
        verify_res = client.post(
            "/api/v1/evidence/verify",
            json={"resume_id": resume_id, "github_username_or_url": "octocat"},
            headers={"Authorization": f"Bearer {token_a}"}
        )
        assert verify_res.status_code == 200
        verif_id = verify_res.json()["verification_id"]

        # User B should be blocked from accessing User A's verification report
        intruder_res = client.get(
            f"/api/v1/evidence/{verif_id}",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert intruder_res.status_code in [403, 404]
