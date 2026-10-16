import uuid
import datetime
from typing import Dict, Any, Optional
from fastapi import HTTPException, status

from app.schemas.job import (
    JobMatchRequest,
    JobMatchResponse,
    FetchJobUrlRequest,
    FetchJobUrlResponse,
)
from app.services.job_description_parser import jd_parser
from app.services.job_matcher import job_matcher
from app.services.url_retriever import url_retriever
from app.services.resume_parser import resume_store
from app.services.resume_analysis_service import analysis_store

class JobMatchStore:
    def __init__(self):
        self._matches: Dict[str, Dict[str, Any]] = {}

    def save(self, match_id: str, data: Dict[str, Any]) -> None:
        self._matches[match_id] = data

    def get(self, match_id: str) -> Optional[Dict[str, Any]]:
        return self._matches.get(match_id)

    def check_ownership(self, match_id: str, user_id: Optional[str]) -> Dict[str, Any]:
        record = self.get(match_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job match report with ID '{match_id}' not found."
            )
        owner = record.get("user_id")
        if owner and (not user_id or user_id != owner):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: you do not have permission to view this match report."
            )
        return record

job_match_store = JobMatchStore()

class JobService:
    @classmethod
    def match_job(
        cls,
        request: JobMatchRequest,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes company-specific job matching against an actual uploaded resume.
        """
        # 1. Obtain Job Description text (either direct or via URL)
        jd_text = ""
        if request.job_url and request.job_url.strip():
            jd_text = url_retriever.fetch_job_text_from_url(request.job_url)
        elif request.job_description and request.job_description.strip():
            jd_text = request.job_description.strip()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A meaningful job description is required. Please paste the job requirements or provide a job posting URL."
            )

        if len(jd_text.split()) < 10 or len(jd_text) < 40:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supplied job description is too brief (< 10 words). Please provide a complete job posting with requirements."
            )

        # 2. Retrieve Candidate Resume
        resume_record = None
        if request.resume_id:
            resume_record = resume_store.check_ownership(request.resume_id, user_id)
        else:
            # Look for most recent resume in memory store matching user_id
            for r_id, rec in reversed(list(resume_store._store.items())):
                rec_owner = rec.get("user_id")
                if not rec_owner or rec_owner == user_id:
                    resume_record = rec
                    break

        if not resume_record:
            # Baseline synthetic candidate if no resume uploaded yet
            resume_record = {
                "resume_id": "demo-resume-baseline",
                "filename": "Alex_Rivera_Sample.pdf",
                "raw_text": (
                    "Alex Rivera\n"
                    "Full Stack Engineer with 3 years building web applications.\n"
                    "SKILLS\nPython, FastAPI, TypeScript, React, PostgreSQL, Docker, Git, AWS, Redis\n"
                    "EXPERIENCE\nSoftware Engineer at Tech Corp (2022-Present)\n"
                    "- Engineered high-throughput REST APIs using Python, FastAPI, and PostgreSQL.\n"
                    "- Developed responsive React frontend dashboards with TypeScript.\n"
                    "PROJECTS\nCareerLens\n- Built an automated employability diagnostic platform."
                ),
                "sections": {
                    "skills": "Python, FastAPI, TypeScript, React, PostgreSQL, Docker, Git, AWS, Redis",
                    "experience": "Engineered high-throughput REST APIs using Python, FastAPI, and PostgreSQL.\nDeveloped responsive React frontend dashboards with TypeScript.",
                    "projects": "CareerLens: Built an automated employability diagnostic platform with FastAPI and React.",
                    "education": "BS in Computer Science, Tech University, 2023",
                }
            }

        # 3. Retrieve Analysis record if available
        analysis_record = analysis_store.get(resume_record.get("resume_id", ""))

        # 4. Parse Job Description
        parsed_jd = jd_parser.parse_job_description(jd_text)

        # 5. Execute Matching Engine
        match_result = job_matcher.match_resume_to_job(
            resume_record=resume_record,
            parsed_jd=parsed_jd,
            analysis_record=analysis_record
        )

        match_id = str(uuid.uuid4())
        response_payload = {
            "match_id": match_id,
            "company": request.company.strip(),
            "role": request.role.strip(),
            "overall_match_score": match_result["overall_match_score"],
            "hard_skill_match_score": match_result["hard_skill_match_score"],
            "preferred_match_score": match_result["preferred_match_score"],
            "experience_match_score": match_result["experience_match_score"],
            "evidence_strength_score": match_result["evidence_strength_score"],
            "readiness_tier": match_result["readiness_tier"],
            "matched_requirements": match_result["matched_requirements"],
            "partial_matches": match_result["partial_matches"],
            "missing_evidence": match_result["missing_evidence"],
            "verified_evidence_summary": match_result["verified_evidence_summary"],
            "recommendations": match_result["recommendations"],
            "disclaimer": match_result["disclaimer"],
            "analyzed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "user_id": user_id,
        }

        # Cache in store
        job_match_store.save(match_id, response_payload)

        return response_payload

    @classmethod
    def get_match(cls, match_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        return job_match_store.check_ownership(match_id, user_id)

    @classmethod
    def fetch_url(cls, url: str) -> Dict[str, Any]:
        text = url_retriever.fetch_job_text_from_url(url)
        return {
            "url": url,
            "extracted_text": text,
            "char_count": len(text),
            "message": "Job description text retrieved successfully.",
        }

job_service = JobService()
