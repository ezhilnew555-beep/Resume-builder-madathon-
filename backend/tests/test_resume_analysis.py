import io
import pytest
import fitz
import jwt
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.services.skill_extractor import skill_extractor
from app.services.resume_section_analyzer import section_analyzer
from app.services.bullet_point_analyzer import bullet_analyzer
from app.services.score_engine import score_engine

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
# 1. Skill Extraction & Ambiguous Word Disambiguation
# -------------------------------------------------------------
def test_skill_extraction_and_disambiguation():
    sample_text = (
        "SKILLS\n"
        "Python, TypeScript, React, PostgreSQL, Docker, AWS, Git, Redis\n\n"
        "EXPERIENCE\n"
        "Software Engineer. We had to go to the store and react quickly to customer inquiries.\n"
        "Developed backend services using Golang and Python.\n"
        "Proficient in C/C++ embedded programming.\n"
    )
    skills = skill_extractor.extract_skills(sample_text)

    # Core languages
    lang_names = [s["name"] for s in skills["languages"]]
    assert "Python" in lang_names
    assert "TypeScript" in lang_names
    assert "Go" in lang_names
    assert "C++" in lang_names

    # Frameworks
    fw_names = [s["name"] for s in skills["frameworks"]]
    assert "React" in fw_names

    # Databases
    db_names = [s["name"] for s in skills["databases"]]
    assert "PostgreSQL" in db_names
    assert "Redis" in db_names

    # Developer tools
    tool_names = [s["name"] for s in skills["developer_tools"]]
    assert "Docker" in tool_names
    assert "AWS" in tool_names
    assert "Git" in tool_names

def test_ambiguous_words_not_false_positives():
    # Text where "go" and "react" are used purely as common English verbs, not programming languages
    casual_text = (
        "I like to go for runs in the park. "
        "When unexpected things happen, I react with patience and calm."
    )
    skills = skill_extractor.extract_skills(casual_text)
    lang_names = [s["name"] for s in skills["languages"]]
    fw_names = [s["name"] for s in skills["frameworks"]]
    
    assert "Go" not in lang_names
    assert "React" not in fw_names

# -------------------------------------------------------------
# 2. Section Analyzer & Entry-Level Candidate Handling
# -------------------------------------------------------------
def test_entry_level_resume_handles_missing_experience_gracefully():
    sections = {
        "contact_info": "Jane Doe | jane@example.com | 555-0100",
        "education": "BS in Computer Science, Tech University, 2024",
        "skills": "Python, React, SQL, Git",
        "projects": "CareerLens: Automated resume auditing system built with FastAPI.",
    }
    result = section_analyzer.analyze_sections("...", sections)

    assert result["is_entry_level"] is True
    assert result["structure_score"] >= 70
    # Missing experience should be categorized as 'recommended', not 'critical'
    exp_missing = next((m for m in result["missing_sections"] if m["section"] == "experience"), None)
    assert exp_missing is not None
    assert exp_missing["importance"] == "recommended"

# -------------------------------------------------------------
# 3. Bullet Point Analyzer & Honest Metric Guidance (No Hallucinations)
# -------------------------------------------------------------
def test_bullet_point_analyzer_weak_versus_strong():
    weak_bullet = "Responsible for developing the API with Python and FastAPI."
    analysis = bullet_analyzer.analyze_single_bullet(weak_bullet)

    assert analysis is not None
    assert analysis["has_strong_verb"] is False
    assert analysis["has_metric"] is False
    assert analysis["score"] < 70
    assert len(analysis["issues"]) > 0

    # Ensure proposed rewrite does NOT invent fake numbers (e.g. "by 35%")
    suggested = analysis["suggested_rewrite"]
    assert "Developed" in suggested or "Engineered" in suggested
    assert "[Insert real measured outcome" in suggested
    assert "35%" not in suggested  # No made up metrics!

def test_bullet_point_analyzer_strong_bullet():
    strong_bullet = "Engineered asynchronous FastAPI microservices and reduced query latency by 45% across 2M daily requests."
    analysis = bullet_analyzer.analyze_single_bullet(strong_bullet)

    assert analysis is not None
    assert analysis["has_strong_verb"] is True
    assert analysis["has_metric"] is True
    assert analysis["score"] >= 85

# -------------------------------------------------------------
# 4. Deterministic Scoring Consistency
# -------------------------------------------------------------
def test_deterministic_scoring_consistency():
    structure_info = {"structure_score": 85, "detected_sections": ["contact_info", "skills", "education"]}
    bullets = [
        {"score": 80, "has_metric": True},
        {"score": 90, "has_metric": True},
    ]
    extracted_skills = {
        "languages": [{"name": "Python"}, {"name": "TypeScript"}],
        "frameworks": [{"name": "React"}],
        "developer_tools": [{"name": "Docker"}],
        "databases": [{"name": "PostgreSQL"}],
    }
    ats_info = {"ats_readability_score": 90}
    style_info = {"style_score": 95}

    score_1 = score_engine.calculate_scores(structure_info, bullets, extracted_skills, ats_info, style_info)
    score_2 = score_engine.calculate_scores(structure_info, bullets, extracted_skills, ats_info, style_info)

    assert score_1["overall_score"] == score_2["overall_score"]
    assert score_1["component_scores"] == score_2["component_scores"]
    assert score_1["readiness_tier"] == score_2["readiness_tier"]

# -------------------------------------------------------------
# 5. Full End-to-End API Integration Tests
# -------------------------------------------------------------
def test_full_resume_analysis_pipeline(client: TestClient):
    synthetic_resume = (
        "Alex Rivera\n"
        "alex.rivera@example.com | +1 555-0199 | Austin, TX\n\n"
        "PROFESSIONAL SUMMARY\n"
        "Full stack software engineer with experience building web applications.\n\n"
        "EDUCATION\n"
        "Bachelor of Science in Computer Science, State University, 2024\n\n"
        "TECHNICAL SKILLS\n"
        "Python, FastAPI, TypeScript, React, PostgreSQL, Docker, Git, AWS\n\n"
        "WORK EXPERIENCE\n"
        "- Responsible for developing backend endpoints and handling bugs.\n"
        "- Engineered real-time data streaming pipeline and reduced latency by 30%.\n\n"
        "PROJECTS\n"
        "- CareerLens: Built an AI-powered resume and career readiness analyzer with React and FastAPI.\n"
    )
    pdf_bytes = create_synthetic_pdf(synthetic_resume)

    # 1. Upload resume
    upload_res = client.post(
        "/api/v1/resume/upload",
        files={"file": ("alex_rivera.pdf", pdf_bytes, "application/pdf")}
    )
    assert upload_res.status_code == 200
    resume_id = upload_res.json()["resume_id"]

    # 2. Trigger Analysis
    analyze_res = client.post(
        f"/api/v1/resume/{resume_id}/analyze",
        json={"target_role": "Full Stack Engineer"}
    )
    assert analyze_res.status_code == 200
    analysis = analyze_res.json()

    assert analysis["resume_id"] == resume_id
    assert 0 <= analysis["overall_score"] <= 100
    assert analysis["readiness_tier"] in ["Ready for Market", "Nearly Ready", "Needs Improvement", "Critical Gaps"]
    assert "structure" in analysis["component_scores"]
    assert "content_quality" in analysis["component_scores"]
    assert "skill_evidence" in analysis["component_scores"]
    assert "ats_readability" in analysis["component_scores"]
    assert len(analysis["extracted_skills"]["languages"]) > 0
    assert len(analysis["findings"]) > 0
    assert "disclaimer" in analysis

    # 3. Retrieve Analysis via GET
    get_res = client.get(f"/api/v1/resume/{resume_id}/analysis")
    assert get_res.status_code == 200
    assert get_res.json()["overall_score"] == analysis["overall_score"]

def test_analysis_ownership_isolation(client: TestClient):
    user_a = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    user_b = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    token_a = make_test_token(user_a)
    token_b = make_test_token(user_b)

    # User A uploads
    pdf_bytes = create_synthetic_pdf("User A Resume\n\nEDUCATION\nBS CS\n\nSKILLS\nPython")
    upload_res = client.post(
        "/api/v1/resume/upload",
        files={"file": ("user_a.pdf", pdf_bytes, "application/pdf")},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert upload_res.status_code == 200
    resume_id = upload_res.json()["resume_id"]

    # User B cannot analyze User A's resume
    b_analyze = client.post(
        f"/api/v1/resume/{resume_id}/analyze",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert b_analyze.status_code == 403

    # User B cannot view User A's analysis
    b_get = client.get(
        f"/api/v1/resume/{resume_id}/analysis",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert b_get.status_code == 403
