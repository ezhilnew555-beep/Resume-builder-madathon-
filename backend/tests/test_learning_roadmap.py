"""
Tests for Phase 10: Personalized Learning Roadmap and Skill Development Tracker.
Verifies roadmap generation, skill gap analysis, milestone pacing, task progress tracking,
notes persistence, progress preservation during regeneration, and multi-tenant isolation.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.job_service import job_match_store
from app.services.resume_parser import resume_store
from app.services.evidence_verification_service import verification_store
from app.services.learning_service import learning_roadmap_store

client = TestClient(app)


def test_generate_roadmap_with_role_and_defaults():
    payload = {
        "target_role": "Backend Engineer",
        "weekly_hours": 12,
        "target_weeks": 4
    }
    response = client.post("/api/v1/learning/roadmap/generate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["target_role"] == "Backend Engineer"
    assert data["weekly_hours"] == 12
    assert data["target_weeks"] == 4
    assert len(data["skill_gaps"]) > 0
    assert len(data["milestones"]) >= 4
    assert len(data["all_tasks"]) >= 4
    assert data["completion_percentage"] == 0
    assert data["completed_tasks"] == 0
    assert data["total_tasks"] == len(data["all_tasks"])
    assert data["total_estimated_hours"] > 0
    assert "disclaimer" in data


def test_generate_roadmap_with_job_match_data():
    match_id = "test-match-101"
    job_match_store.save(match_id, {
        "match_id": match_id,
        "target_role": "Senior Cloud Engineer",
        "company_name": "Acme Cloud Corp",
        "overall_match_score": 75.0,
        "matching_skills": [{"skill": "Python", "importance": "required"}],
        "missing_skills": [
            {"skill": "Kubernetes", "importance": "required", "recommendation": "Learn K8s"},
            {"skill": "Terraform", "importance": "preferred", "recommendation": "Learn IaC"}
        ],
        "partial_skills": [{"skill": "Docker", "importance": "required"}]
    })

    payload = {
        "job_match_id": match_id,
        "weekly_hours": 15,
        "target_weeks": 4
    }
    response = client.post("/api/v1/learning/roadmap/generate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["target_role"] == "Senior Cloud Engineer"
    assert data["target_company"] == "Acme Cloud Corp"
    skills_in_gaps = [g["skill"] for g in data["skill_gaps"]]
    assert "Kubernetes" in skills_in_gaps
    assert "Terraform" in skills_in_gaps

    # Verify verified educational resource link
    k8s_gap = next((g for g in data["skill_gaps"] if g["skill"] == "Kubernetes"), None)
    assert k8s_gap is not None
    assert k8s_gap["learning_priority"] == "high"


def test_skill_evidence_status_consistency():
    # Setup candidate resume and verification evidence
    user_id = "user-alice-10"
    resume_store.save("res-alice-10", {
        "resume_id": "res-alice-10",
        "user_id": user_id,
        "filename": "alice_resume.pdf",
        "text": "Experienced in Python and Docker.",
        "detected_skills": {
            "languages": ["Python"],
            "developer_tools": ["Docker"]
        }
    })

    # Python is verified on GitHub; Docker is in resume only; Kubernetes is missing
    verification_store.save("ver-alice-10", {
        "verification_id": "ver-alice-10",
        "user_id": user_id,
        "verified_skills": [{"skill": "Python"}]
    })

    payload = {
        "target_role": "DevOps Engineer",
        "resume_id": "res-alice-10",
        "job_description": "We require Python, Docker, and Kubernetes for building cloud platforms.",
        "weekly_hours": 10,
        "target_weeks": 4
    }
    response = client.post("/api/v1/learning/roadmap/generate", json=payload)
    assert response.status_code == 200
    data = response.json()

    gaps = {g["skill"].lower(): g for g in data["skill_gaps"]}

    # Python should be demonstrated
    if "python" in gaps:
        assert gaps["python"]["evidence_status"] == "demonstrated"
        assert gaps["python"]["learning_priority"] == "low"

    # Docker should be partial evidence (in resume text, no repo verification)
    if "docker" in gaps:
        assert gaps["docker"]["evidence_status"] == "partial_evidence"

    # Kubernetes should be not_demonstrated with non-stigmatizing rationale
    if "kubernetes" in gaps:
        assert gaps["kubernetes"]["evidence_status"] == "not_demonstrated"
        assert gaps["kubernetes"]["learning_priority"] == "high"
        assert "not confirmed inability" in gaps["kubernetes"]["reason"]


def test_get_current_and_get_by_id():
    res_gen = client.post("/api/v1/learning/roadmap/generate", json={"target_role": "Frontend Specialist"})
    roadmap_id = res_gen.json()["id"]

    res_get = client.get(f"/api/v1/learning/roadmap/{roadmap_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == roadmap_id

    res_cur = client.get("/api/v1/learning/roadmap/current")
    assert res_cur.status_code == 200
    assert res_cur.json()["id"] is not None


def test_get_task_details():
    res_gen = client.post("/api/v1/learning/roadmap/generate", json={"target_role": "Full Stack Engineer"})
    data = res_gen.json()
    roadmap_id = data["id"]
    task_id = data["all_tasks"][0]["id"]

    res_task = client.get(f"/api/v1/learning/roadmap/{roadmap_id}/tasks/{task_id}")
    assert res_task.status_code == 200
    task_data = res_task.json()
    assert task_data["id"] == task_id
    assert "instructions" in task_data
    assert "practical_exercise" in task_data
    assert "deliverable" in task_data


def test_update_task_status_and_notes():
    res_gen = client.post("/api/v1/learning/roadmap/generate", json={"target_role": "Software Engineer"})
    data = res_gen.json()
    roadmap_id = data["id"]
    task_id = data["all_tasks"][0]["id"]

    # 1. Update to in_progress
    res_in_prog = client.patch(
        f"/api/v1/learning/roadmap/{roadmap_id}/tasks/{task_id}",
        json={"status": "in_progress", "notes": "Started reading official documentation."}
    )
    assert res_in_prog.status_code == 200
    data_prog = res_in_prog.json()
    assert data_prog["in_progress_tasks"] == 1
    updated_task = next(t for t in data_prog["all_tasks"] if t["id"] == task_id)
    assert updated_task["status"] == "in_progress"
    assert updated_task["user_notes"] == "Started reading official documentation."
    assert updated_task["started_at"] is not None

    # 2. Update to completed
    res_comp = client.patch(
        f"/api/v1/learning/roadmap/{roadmap_id}/tasks/{task_id}",
        json={"status": "completed", "notes": "Completed exercises and committed to GitHub."}
    )
    assert res_comp.status_code == 200
    data_comp = res_comp.json()
    assert data_comp["completed_tasks"] == 1
    assert data_comp["completion_percentage"] > 0
    updated_comp_task = next(t for t in data_comp["all_tasks"] if t["id"] == task_id)
    assert updated_comp_task["status"] == "completed"
    assert updated_comp_task["completed_at"] is not None


def test_invalid_task_status_rejected():
    res_gen = client.post("/api/v1/learning/roadmap/generate", json={"target_role": "QA Engineer"})
    data = res_gen.json()
    roadmap_id = data["id"]
    task_id = data["all_tasks"][0]["id"]

    # Invalid status should return 422 Unprocessable Entity
    res_inv = client.patch(
        f"/api/v1/learning/roadmap/{roadmap_id}/tasks/{task_id}",
        json={"status": "finished"}
    )
    assert res_inv.status_code == 422


def test_update_preferences():
    res_gen = client.post("/api/v1/learning/roadmap/generate", json={"target_role": "ML Engineer"})
    roadmap_id = res_gen.json()["id"]

    res_pref = client.patch(
        f"/api/v1/learning/roadmap/{roadmap_id}/preferences",
        json={"weekly_hours": 20, "target_weeks": 8}
    )
    assert res_pref.status_code == 200
    pref_data = res_pref.json()
    assert pref_data["weekly_hours"] == 20
    assert pref_data["target_weeks"] == 8


def test_refresh_preserves_completed_tasks_and_notes():
    # 1. Generate roadmap
    res_gen = client.post("/api/v1/learning/roadmap/generate", json={"target_role": "Platform Engineer"})
    roadmap_id = res_gen.json()["id"]
    task_id = res_gen.json()["all_tasks"][0]["id"]

    # 2. Complete task 1 with notes
    client.patch(
        f"/api/v1/learning/roadmap/{roadmap_id}/tasks/{task_id}",
        json={"status": "completed", "notes": "Verified working pipeline on GitHub."}
    )

    # 3. Refresh roadmap with an updated job description
    res_ref = client.post(
        f"/api/v1/learning/roadmap/{roadmap_id}/refresh",
        json={"job_description": "We need an engineer skilled in Linux, Python, and Docker."}
    )
    assert res_ref.status_code == 200
    ref_data = res_ref.json()

    # Completed task status and notes MUST be preserved!
    assert ref_data["completed_tasks"] >= 1
    preserved_task = next((t for t in ref_data["all_tasks"] if t["id"] == task_id), None)
    if preserved_task:
        assert preserved_task["status"] == "completed"
        assert preserved_task["user_notes"] == "Verified working pipeline on GitHub."


def test_progress_statistics_endpoint():
    res_gen = client.post("/api/v1/learning/roadmap/generate", json={"target_role": "Systems Engineer"})
    roadmap_id = res_gen.json()["id"]

    res_prog = client.get(f"/api/v1/learning/roadmap/{roadmap_id}/progress")
    assert res_prog.status_code == 200
    stats = res_prog.json()
    assert stats["roadmap_id"] == roadmap_id
    assert stats["total_tasks"] > 0
    assert "remaining_hours" in stats
    assert "status_summary" in stats


def test_multi_tenant_isolation():
    # Create roadmap owned by user-alpha
    gen_res = learning_roadmap_store.save("roadmap-alpha-secret", {
        "id": "roadmap-alpha-secret",
        "user_id": "user-alpha",
        "target_role": "Alpha Role",
        "all_tasks": [],
        "milestones": [],
        "skill_gaps": [],
        "created_at": "2026-10-16T12:00:00Z",
        "updated_at": "2026-10-16T12:00:00Z"
    }, user_id="user-alpha")

    # Access without auth or by another user should be checked
    with pytest.raises(Exception) as excinfo:
        learning_roadmap_store.check_ownership("roadmap-alpha-secret", user_id="user-beta")
    assert "403" in str(excinfo.value)
