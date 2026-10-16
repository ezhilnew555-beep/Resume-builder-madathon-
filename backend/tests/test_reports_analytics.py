"""
Tests for Phase 11: Reports History, Detailed Assessment, Before-and-After Comparison,
Progress Analytics, and Native PDF Export.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.resume_parser import resume_store
from app.services.resume_analysis_service import analysis_store
from app.services.report_service import report_store

client = TestClient(app)


def test_list_reports_empty():
    report_store._reports.clear()
    response = client.get("/api/v1/reports")
    assert response.status_code == 200
    data = response.json()
    assert data["reports"] == []
    assert data["total"] == 0
    assert "No stored reports found" in data["message"]


def test_save_report_and_get_details():
    # Setup resume and analysis in stores
    resume_id = "res-rep-001"
    resume_store.save(resume_id, {
        "resume_id": resume_id,
        "filename": "john_doe_resume.pdf",
        "text": "Experienced Python and React developer with 3 years building cloud APIs.",
        "detected_sections": ["Experience", "Skills", "Education"],
    })

    analysis_store.save(resume_id, {
        "resume_id": resume_id,
        "filename": "john_doe_resume.pdf",
        "overall_score": 76.5,
        "readiness_tier": "Competitive",
        "component_scores": {"formatting": 85, "structure": 80, "skills": 75, "bullet_impact": 66},
        "scoring_rationale": {"summary": "Strong skill alignment."},
        "extracted_skills": {"languages": [{"name": "Python"}, {"name": "React"}]},
        "detected_sections": ["Experience", "Skills", "Education"],
        "missing_sections": ["Projects"],
        "findings": [
            {"id": "f-1", "title": "Missing Projects Section", "severity": "warning", "description": "Add projects section."}
        ],
        "bullet_point_evaluations": [],
    })

    # Save report
    payload = {
        "resume_id": resume_id,
        "target_role": "Full Stack Engineer",
        "report_title": "Q4 Career Audit"
    }
    res_save = client.post("/api/v1/reports/save", json=payload)
    assert res_save.status_code == 201
    save_data = res_save.json()

    assert save_data["report_title"] == "Q4 Career Audit"
    assert save_data["overall_score"] in (76, 77)
    assert save_data["target_role"] == "Full Stack Engineer"
    assert "CareerLens ATS-style estimate" in save_data["disclaimer"]
    report_id = save_data["id"]

    # Retrieve detailed report
    res_get = client.get(f"/api/v1/reports/{report_id}")
    assert res_get.status_code == 200
    get_data = res_get.json()
    assert get_data["id"] == report_id
    assert len(get_data["findings"]) == 1
    assert "formatting" in get_data["component_scores"]


def test_list_reports_with_pagination():
    report_store._reports.clear()
    for i in range(3):
        r_id = f"test-rep-{i}"
        report_store.save(r_id, {
            "id": r_id,
            "report_title": f"Report #{i}",
            "date": f"Oct 0{i+1}, 2026",
            "resume_name": "resume.pdf",
            "target_role": "Software Engineer",
            "overall_score": 70 + i * 5,
            "ats_score": 70 + i * 5,
            "match_score": 60,
            "issues_count": 2,
            "status": "completed",
        })

    # Page 1, size 2
    res_p1 = client.get("/api/v1/reports?page=1&page_size=2")
    assert res_p1.status_code == 200
    d1 = res_p1.json()
    assert d1["total"] == 3
    assert len(d1["reports"]) == 2
    assert d1["page"] == 1

    # Page 2, size 2
    res_p2 = client.get("/api/v1/reports?page=2&page_size=2")
    assert res_p2.status_code == 200
    d2 = res_p2.json()
    assert len(d2["reports"]) == 1


def test_compare_two_reports():
    rep_a_id = "rep-compare-a"
    rep_b_id = "rep-compare-b"

    report_store.save(rep_a_id, {
        "id": rep_a_id,
        "date": "2026-10-01",
        "report_title": "Initial Draft",
        "target_role": "Backend Engineer",
        "overall_score": 65,
        "component_scores": {"formatting": 60, "skills": 70},
        "match_score": 50,
        "findings": [
            {"title": "Weak Action Verbs", "description": "Bullets lack metrics."},
            {"title": "Missing Contact Info", "description": "Phone is missing."}
        ]
    })

    report_store.save(rep_b_id, {
        "id": rep_b_id,
        "date": "2026-10-15",
        "report_title": "Revised Draft",
        "target_role": "Backend Engineer",
        "overall_score": 82,
        "component_scores": {"formatting": 85, "skills": 80},
        "match_score": 75,
        "findings": [
            # "Missing Contact Info" was fixed!
            {"title": "Weak Action Verbs", "description": "Some bullets still weak."},
            {"title": "New Finding: Add Docker", "description": "Tool recommended."}
        ]
    })

    res_comp = client.get(f"/api/v1/reports/{rep_a_id}/compare/{rep_b_id}")
    assert res_comp.status_code == 200
    comp_data = res_comp.json()

    assert comp_data["score_delta"] == 17
    assert comp_data["is_compatible"] is True

    # Check resolved issues
    resolved_titles = [f["title"] for f in comp_data["issues_resolved"]]
    assert "Missing Contact Info" in resolved_titles

    # Check category deltas
    assert comp_data["category_deltas"]["formatting"]["delta"] == 25

    # Check newly identified issues
    new_titles = [f["title"] for f in comp_data["issues_newly_identified"]]
    assert "New Finding: Add Docker" in new_titles


def test_compare_reports_incompatible_notice():
    rep_1 = "rep-incompat-1"
    rep_2 = "rep-incompat-2"

    report_store.save(rep_1, {
        "id": rep_1,
        "date": "2026-10-01",
        "target_role": "Frontend Engineer",
        "overall_score": 70,
        "findings": []
    })
    report_store.save(rep_2, {
        "id": rep_2,
        "date": "2026-10-02",
        "target_role": "Data Scientist",
        "overall_score": 60,
        "findings": []
    })

    res_comp = client.get(f"/api/v1/reports/{rep_1}/compare/{rep_2}")
    assert res_comp.status_code == 200
    comp_data = res_comp.json()
    assert comp_data["is_compatible"] is False
    assert "Caution" in comp_data["compatibility_notice"]


def test_delete_report():
    rep_del = "rep-to-delete"
    report_store.save(rep_del, {
        "id": rep_del,
        "target_role": "QA Engineer",
        "overall_score": 70,
    })

    res_del = client.delete(f"/api/v1/reports/{rep_del}")
    assert res_del.status_code == 200
    assert res_del.json()["success"] is True

    # Getting deleted report returns 404
    res_get = client.get(f"/api/v1/reports/{rep_del}")
    assert res_get.status_code == 404


def test_progress_analytics_summary():
    report_store._reports.clear()
    for i in range(2):
        r_id = f"analytics-rep-{i}"
        report_store.save(r_id, {
            "id": r_id,
            "date": f"2026-10-0{i+1}",
            "created_at": f"2026-10-0{i+1}T10:00:00Z",
            "target_role": "Systems Engineer",
            "overall_score": 68 + i * 10,
            "ats_score": 68 + i * 10,
            "match_score": 60 + i * 5,
            "findings": [{"title": f"Issue {i}"}],
            "extracted_skills": {"languages": [{"name": "C++"}, {"name": "Python"}]}
        })

    res_analytics = client.get("/api/v1/reports/analytics/summary")
    assert res_analytics.status_code == 200
    data = res_analytics.json()

    assert data["total_analyses_completed"] == 2
    assert data["latest_score"] == 78
    assert data["previous_score"] == 68
    assert data["has_historical_data"] is True
    assert len(data["score_progression"]) == 2
    assert "skills_by_evidence_type" in data
    assert "disclaimer" in data


def test_export_report_pdf():
    rep_pdf = "rep-pdf-test"
    report_store.save(rep_pdf, {
        "id": rep_pdf,
        "resume_name": "candidate_cv.pdf",
        "date": "Oct 16, 2026",
        "target_role": "Cloud Architect",
        "overall_score": 88,
        "readiness_tier": "Interview Ready",
        "component_scores": {"formatting": 90, "structure": 85, "skills": 89},
        "findings": [
            {"title": "Missing Certifications", "description": "Add AWS certification.", "severity": "info"}
        ],
    })

    res_pdf = client.get(f"/api/v1/reports/{rep_pdf}/export/pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert res_pdf.content.startswith(b"%PDF-")
    assert len(res_pdf.content) > 500


def test_multi_tenant_isolation():
    rep_secret = "rep-user-secret"
    report_store.save(rep_secret, {
        "id": rep_secret,
        "user_id": "user-owner-1",
        "overall_score": 90
    }, user_id="user-owner-1")

    # Unauthorized access by user-owner-2
    with pytest.raises(Exception) as excinfo:
        report_store.check_ownership(rep_secret, user_id="user-owner-2")
    assert "403" in str(excinfo.value)
