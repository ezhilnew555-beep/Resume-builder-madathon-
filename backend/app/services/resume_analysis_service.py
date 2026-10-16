import datetime
import time
from typing import Dict, Any, Optional
from fastapi import HTTPException, status

from app.services.resume_parser import resume_store
from app.services.skill_extractor import skill_extractor
from app.services.resume_section_detector import section_detector
from app.services.resume_section_analyzer import section_analyzer
from app.services.bullet_point_analyzer import bullet_analyzer
from app.services.grammar_checker import grammar_checker
from app.services.ats_checker import ats_checker
from app.services.score_engine import score_engine
from app.services.suggestion_engine import suggestion_engine
from app.schemas.analysis import ResumeAnalysisResponse, ResumeAnalyzeRequestPayload

class ResumeAnalysisStore:
    """
    In-memory storage for analysis results with user ownership enforcement.
    """
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def save(self, resume_id: str, data: Dict[str, Any]) -> None:
        self._cache[resume_id] = data

    def get(self, resume_id: str) -> Optional[Dict[str, Any]]:
        return self._cache.get(resume_id)

    def check_ownership(self, resume_id: str, user_id: Optional[str]) -> Dict[str, Any]:
        record = self.get(resume_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis for resume ID '{resume_id}' not found. Please trigger analysis first."
            )
        owner = record.get("user_id")
        if owner and (not user_id or user_id != owner):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: you do not have permission to view this analysis."
            )
        return record

analysis_store = ResumeAnalysisStore()

class ResumeAnalysisService:
    @classmethod
    def analyze_resume(
        cls,
        resume_id: str,
        payload: Optional[ResumeAnalyzeRequestPayload] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyzes real extracted resume text from Phase 4, computes scores, and generates findings.
        """
        # 1. Fetch parsed resume record and enforce ownership
        resume_record = resume_store.check_ownership(resume_id, user_id)

        raw_text = resume_record.get("raw_text", "")
        sections = resume_record.get("sections", {})
        filename = resume_record.get("filename", "resume")
        extraction_status = resume_record.get("extraction_status", "unknown")

        # 2. Check for empty or failed extraction
        if extraction_status in ["failed", "ocr_unavailable"] or not raw_text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Cannot analyze document: extraction status is '{extraction_status}'. "
                    "No readable text is available for ATS analysis. "
                    "Please ensure the document contains selectable text or install Tesseract OCR for scanned PDFs."
                )
            )

        job_description = payload.job_description if payload else None
        target_role = payload.target_role if payload else None

        # 3. Execute Analysis Engines
        extracted_skills = skill_extractor.extract_skills(raw_text, sections)
        section_info = section_analyzer.analyze_sections(raw_text, sections)
        bullet_evaluations = bullet_analyzer.analyze_bullets_in_sections(sections)
        grammar_info = grammar_checker.check_grammar_and_style(raw_text, sections)
        ats_info = ats_checker.evaluate_ats_readability(raw_text, sections, job_description)

        # 4. Compute Transparent Deterministic Scores
        scoring_result = score_engine.calculate_scores(
            structure_info=section_info,
            bullet_evaluations=bullet_evaluations,
            extracted_skills=extracted_skills,
            ats_info=ats_info,
            style_info=grammar_info,
            has_job_description=bool(job_description)
        )

        # 5. Aggregate Actionable Improvement Findings
        findings = suggestion_engine.aggregate_findings(
            section_info=section_info,
            bullet_evaluations=bullet_evaluations,
            grammar_info=grammar_info,
            ats_info=ats_info
        )

        # 6. Build Comprehensive Analysis Response
        data_quality_warnings = ats_info.get("warnings", [])
        if section_info.get("contact_issues"):
            data_quality_warnings.extend(section_info["contact_issues"])

        analysis_payload = {
            "resume_id": resume_id,
            "filename": filename,
            "overall_score": scoring_result["overall_score"],
            "readiness_tier": scoring_result["readiness_tier"],
            "component_scores": scoring_result["component_scores"],
            "scoring_weights": scoring_result["scoring_weights"],
            "scoring_rationale": scoring_result["scoring_rationale"],
            "extracted_skills": extracted_skills,
            "detected_sections": section_info["detected_sections"],
            "missing_sections": section_info["missing_sections"],
            "findings": findings,
            "bullet_point_evaluations": bullet_evaluations,
            "data_quality_warnings": data_quality_warnings,
            "disclaimer": ats_info["disclaimer"],
            "analyzed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "user_id": user_id,
        }

        # Cache in memory store
        analysis_store.save(resume_id, analysis_payload)

        return analysis_payload

    @classmethod
    def get_analysis(cls, resume_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves previously computed analysis, enforcing ownership.
        """
        # First verify the resume itself exists and ownership matches
        resume_store.check_ownership(resume_id, user_id)
        # Check if analysis exists
        record = analysis_store.get(resume_id)
        if not record:
            # Auto-run analysis on the fly if resume exists!
            return cls.analyze_resume(resume_id, user_id=user_id)
        return record

resume_analysis_service = ResumeAnalysisService()
