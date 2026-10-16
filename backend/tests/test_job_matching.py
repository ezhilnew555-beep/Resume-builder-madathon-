import pytest
import jwt
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.services.job_description_parser import jd_parser
from app.services.job_matcher import job_matcher
from app.services.url_retriever import url_retriever
import fitz

@pytest.fixture
def client():
    return TestClient(app)

def make_test_token(user_id: str, email: str = "test@example.com") -> str:
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

# -------------------------------------------------------------
# 1. Job Description Parser Unit Tests
# -------------------------------------------------------------
def test_job_description_parser_sections():
    jd_text = """
    Target Role: Backend Engineer
    Company: FinTech Velocity

    About the Role:
    We are seeking a Backend Engineer with 3+ years of experience building distributed systems.

    Required Qualifications:
    - 3+ years of production experience in Python and PostgreSQL.
    - Strong understanding of Docker and REST APIs.
    - Bachelor's degree in Computer Science or equivalent.

    Preferred Qualifications:
    - Experience with Kubernetes, AWS, and Redis caching.
    - Familiarity with CI/CD and automated testing.

    Responsibilities:
    - Design and maintain scalable microservices.
    - Collaborate with cross-functional teams to deliver payment solutions.
    """

    parsed = jd_parser.parse_job_description(jd_text)
    assert parsed["min_experience_years"] == 3
    assert any("degree" in ed.lower() for ed in parsed["education_criteria"])

    # Required skills
    req_skills = [s["name"] for s in parsed["required_skills"]]
    assert "Python" in req_skills
    assert "PostgreSQL" in req_skills
    assert "Docker" in req_skills

    # Preferred skills
    pref_skills = [s["name"] for s in parsed["preferred_skills"]]
    assert "Kubernetes" in pref_skills or "AWS" in pref_skills or "Redis" in pref_skills

    # Responsibilities
    assert len(parsed["responsibilities"]) >= 1


# -------------------------------------------------------------
# 2. Matching Engine: Strong Match vs Low Match
# -------------------------------------------------------------
def test_job_matching_strong_match():
    candidate_resume = {
        "raw_text": """
        Jane Doe
        jane.doe@example.com
        
        SKILLS
        Python, FastAPI, PostgreSQL, Docker, Git, Redis
        
        EXPERIENCE
        Backend Software Engineer | Acme Corp (2022 - Present)
        - Engineered scalable backend microservices using Python and FastAPI, handling 15,000 req/sec.
        - Designed and optimized relational schemas in PostgreSQL, reducing query latency by 45%.
        - Containerized 12 core services using Docker and deployed on AWS.
        
        EDUCATION
        B.S. in Computer Science, University of Technology
        """,
        "sections": {
            "experience": "Engineered scalable backend microservices using Python and FastAPI, handling 15,000 req/sec. Designed and optimized relational schemas in PostgreSQL. Containerized services using Docker.",
            "skills": "Python, FastAPI, PostgreSQL, Docker, Git, Redis",
            "education": "B.S. in Computer Science, University of Technology"
        }
    }

    jd_text = """
    Required Qualifications:
    - Proficient in Python and PostgreSQL.
    - Practical experience with Docker.
    
    Preferred Qualifications:
    - Experience with Redis and FastAPI.
    """

    parsed_jd = jd_parser.parse_job_description(jd_text)
    res = job_matcher.match_resume_to_job(
        resume_record=candidate_resume,
        parsed_jd=parsed_jd
    )

    assert res["overall_match_score"] >= 70
    assert res["hard_skill_match_score"] >= 80
    assert res["readiness_tier"] in ["Strong Contender", "Competitive Match"]
    assert len(res["matched_requirements"]) >= 2
    # Verify quotes exist in matched requirements
    assert any(m["evidence_quote"] != "" for m in res["matched_requirements"])


def test_job_matching_low_match():
    graphic_designer_resume = {
        "raw_text": """
        John Artist
        Skills: Photoshop, Figma, Illustrator, UI Design, Wireframing
        Experience: Graphic Designer creating branding identities and marketing banners.
        Education: B.A. in Fine Arts
        """,
        "sections": {
            "skills": "Photoshop, Figma, Illustrator, UI Design",
            "experience": "Graphic Designer creating branding identities and marketing banners."
        }
    }

    software_jd = """
    Required Qualifications:
    - Must have 5+ years with C++, Rust, and Linux kernel programming.
    - Deep knowledge of Kubernetes clustering and network protocols.
    """

    parsed_jd = jd_parser.parse_job_description(software_jd)
    res = job_matcher.match_resume_to_job(
        resume_record=graphic_designer_resume,
        parsed_jd=parsed_jd
    )

    assert res["overall_match_score"] < 40
    assert len(res["missing_evidence"]) >= 1
    assert res["readiness_tier"] in ["Significant Alignment Gaps", "Moderate Fit (Skill Gaps)"]


# -------------------------------------------------------------
# 3. Equivalence Mapping (e.g. Postgres satisfies SQL)
# -------------------------------------------------------------
def test_job_matching_equivalence():
    resume_with_postgres = {
        "raw_text": """
        Jane Developer
        SKILLS: PostgreSQL, FastAPI
        EXPERIENCE:
        - Managed PostgreSQL transactional databases with active replication.
        """,
        "sections": {
            "skills": "PostgreSQL, FastAPI",
            "experience": "Managed PostgreSQL transactional databases with active replication."
        }
    }

    # Job demands SQL
    jd_text = """
    Required Qualifications:
    - Strong knowledge of SQL and relational database concepts.
    """

    parsed_jd = jd_parser.parse_job_description(jd_text)
    res = job_matcher.match_resume_to_job(
        resume_record=resume_with_postgres,
        parsed_jd=parsed_jd
    )

    # Should match SQL via PostgreSQL equivalent
    has_sql_match = any("sql" in m["name"].lower() for m in res["matched_requirements"])
    has_sql_partial = any("sql" in m["name"].lower() for m in res["partial_matches"])
    assert has_sql_match or has_sql_partial


# -------------------------------------------------------------
# 4. Mention Only vs Project Demonstration
# -------------------------------------------------------------
def test_job_matching_mention_without_project_evidence():
    resume_mention_only = {
        "raw_text": """
        Alice Candidate
        SKILLS: Python, Kubernetes
        EXPERIENCE:
        - Developed web applications using Python and Django.
        """,
        "sections": {
            "skills": "Python, Kubernetes",
            "experience": "Developed web applications using Python and Django."
        }
    }

    jd_text = """
    Required Qualifications:
    - 2+ years of hands-on Kubernetes experience in production.
    """

    parsed_jd = jd_parser.parse_job_description(jd_text)
    res = job_matcher.match_resume_to_job(
        resume_record=resume_mention_only,
        parsed_jd=parsed_jd
    )

    # Kubernetes should be in partial_matches because it was only mentioned in skills
    k8s_partials = [m for m in res["partial_matches"] if "kubernetes" in m["name"].lower()]
    assert len(k8s_partials) == 1
    assert "lacks an evidence bullet" in k8s_partials[0]["explanation"]


# -------------------------------------------------------------
# 5. Deterministic Repeatability
# -------------------------------------------------------------
def test_job_matching_deterministic_repeatability():
    resume = {
        "raw_text": "SKILLS: Python, React, Docker\nEXPERIENCE: Built web apps with Python and React.",
        "sections": {
            "skills": "Python, React, Docker",
            "experience": "Built web apps with Python and React."
        }
    }
    jd = "Required: Python, React, Docker. Preferred: AWS."
    parsed_jd = jd_parser.parse_job_description(jd)

    res1 = job_matcher.match_resume_to_job(resume, parsed_jd)
    res2 = job_matcher.match_resume_to_job(resume, parsed_jd)

    assert res1["overall_match_score"] == res2["overall_match_score"]
    assert res1["hard_skill_match_score"] == res2["hard_skill_match_score"]
    assert res1["preferred_match_score"] == res2["preferred_match_score"]
    assert len(res1["matched_requirements"]) == len(res2["matched_requirements"])


# -------------------------------------------------------------
# 6. SSRF & URL Retrieval Security
# -------------------------------------------------------------
def test_url_retriever_ssrf_blocking():
    # Loopback IP
    with pytest.raises(HTTPException) as exc1:
        url_retriever.fetch_job_text_from_url("http://127.0.0.1:8000/internal")
    assert exc1.value.status_code == 400
    assert "blocked" in exc1.value.detail.lower()

    # Localhost
    with pytest.raises(HTTPException) as exc2:
        url_retriever.fetch_job_text_from_url("http://localhost:3000")
    assert exc2.value.status_code == 400
    assert "blocked" in exc2.value.detail.lower()

    # Invalid scheme
    with pytest.raises(HTTPException) as exc3:
        url_retriever.fetch_job_text_from_url("ftp://example.com/job.txt")
    assert exc3.value.status_code == 400
    assert "only standard http and https" in exc3.value.detail.lower()


# -------------------------------------------------------------
# 7. API Endpoints: Match, Retrieval & Validation
# -------------------------------------------------------------
def test_api_jobs_match_short_jd_rejected(client):
    # Short JD (< 40 characters)
    payload = {
        "company": "Google",
        "role": "Software Engineer",
        "job_description": "We need engineer."
    }
    response = client.post("/api/v1/jobs/match", json=payload)
    assert response.status_code == 400
    assert "too brief" in response.json()["detail"].lower()


def test_api_jobs_match_end_to_end(client):
    # 1. Upload a valid test resume first
    resume_text = (
        "Alex Tech\n"
        "alex@example.com\n\n"
        "SKILLS\n"
        "Python, React, TypeScript, Docker, PostgreSQL\n\n"
        "EXPERIENCE\n"
        "Full Stack Developer | TechLabs (2022 - Present)\n"
        "- Developed full-stack SaaS features using Python, FastAPI, and React with TypeScript.\n"
        "- Optimized PostgreSQL queries and automated deployments with Docker containers.\n\n"
        "EDUCATION\n"
        "B.S. in Computer Science"
    )
    pdf_bytes = create_synthetic_pdf(resume_text)
    upload_res = client.post(
        "/api/v1/resume/upload",
        files={"file": ("alex_resume.pdf", pdf_bytes, "application/pdf")}
    )
    assert upload_res.status_code == 200
    resume_id = upload_res.json()["resume_id"]

    # 2. Run Match
    match_payload = {
        "company": "Stripe",
        "role": "Full Stack Engineer",
        "job_description": (
            "We are looking for a Full Stack Engineer to join our Payments team.\n"
            "Requirements:\n"
            "- Strong proficiency in Python and React.\n"
            "- Experience working with PostgreSQL databases and Docker containerization.\n"
            "Preferred:\n"
            "- Familiarity with TypeScript and CI/CD pipelines."
        ),
        "resume_id": resume_id
    }
    match_res = client.post("/api/v1/jobs/match", json=match_payload)
    assert match_res.status_code == 200
    data = match_res.json()
    assert data["company"] == "Stripe"
    assert data["role"] == "Full Stack Engineer"
    assert data["overall_match_score"] >= 70
    assert len(data["matched_requirements"]) >= 3
    assert data["disclaimer"] != ""
    match_id = data["match_id"]

    # 3. Retrieve stored match
    get_res = client.get(f"/api/v1/jobs/matches/{match_id}")
    assert get_res.status_code == 200
    assert get_res.json()["match_id"] == match_id


def test_api_jobs_fetch_url_ssrf_blocked(client):
    payload = {"url": "http://127.0.0.1:8080/admin"}
    response = client.post("/api/v1/jobs/fetch-url", json=payload)
    assert response.status_code == 400
    assert "blocked" in response.json()["detail"].lower()


def test_api_jobs_user_ownership_enforcement(client):
    # Upload resume as User A
    token_a = make_test_token("user-a-111")
    token_b = make_test_token("user-b-222")

    resume_text = "Alice A\nSKILLS: Python, SQL\nEXPERIENCE: Worked with Python and SQL."
    pdf_bytes = create_synthetic_pdf(resume_text)
    upload_res = client.post(
        "/api/v1/resume/upload",
        files={"file": ("alice_resume.pdf", pdf_bytes, "application/pdf")},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert upload_res.status_code == 200
    resume_id = upload_res.json()["resume_id"]

    # User A matches job
    match_payload = {
        "company": "OpenAI",
        "role": "Research Engineer",
        "job_description": "We are looking for an engineer with strong Python and SQL background.",
        "resume_id": resume_id
    }
    match_res = client.post(
        "/api/v1/jobs/match",
        json=match_payload,
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert match_res.status_code == 200
    match_id = match_res.json()["match_id"]

    # User B attempts to access User A's match report -> 404/403
    forbidden_res = client.get(
        f"/api/v1/jobs/matches/{match_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert forbidden_res.status_code in [403, 404]
