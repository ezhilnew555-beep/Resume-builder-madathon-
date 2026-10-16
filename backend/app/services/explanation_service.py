"""
Grounded AI Explanation Service for CareerLens (Phase 8).
Generates explainable, evidence-grounded interpretations for resume analyses
and job match compatibility reports while strictly preserving deterministic scores.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from app.services.resume_analysis_service import resume_analysis_service
from app.services.resume_parser import resume_store
from app.services.job_service import job_service
from app.services.ai_provider import ai_provider_manager
from app.services.recommendation_service import recommendation_service
from app.services.prompt_templates import (
    RESUME_EXPLANATION_SYSTEM_PROMPT,
    JOB_MATCH_EXPLANATION_SYSTEM_PROMPT,
    build_resume_prompt,
    build_job_match_prompt
)
from app.schemas.explanation import (
    ResumeExplanationResponse,
    ResumeFindingExplanation,
    JobMatchExplanationResponse,
    JobMatchExplanationItem,
    PrioritizedRecommendation
)

logger = logging.getLogger(__name__)

class ExplanationService:
    def explain_resume(self, resume_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates grounded, plain-English explanations for resume findings.
        Guarantees strict score immutability (the Python score cannot be altered by AI).
        """
        # Retrieve deterministic analysis report (handles ownership checks)
        analysis = resume_analysis_service.get_analysis(resume_id=resume_id, user_id=user_id)
        
        # Retrieve resume text sample if accessible
        try:
            resume_record = resume_store.get(resume_id)
            raw_text = resume_record.get("raw_text", "") if resume_record else ""
        except Exception:
            raw_text = ""

        # Extract deterministic immutable values
        immutable_score = int(analysis.get("overall_score", 0))
        immutable_tier = str(analysis.get("readiness_tier", "Needs Revision"))
        findings_data = analysis.get("review_findings", [])
        extracted_skills = analysis.get("detected_skills", [])

        # Build prompt payload
        prompt_data = {
            "overall_score": immutable_score,
            "readiness_tier": immutable_tier,
            "skills": [s.get("name", "") for s in extracted_skills if isinstance(s, dict)],
            "findings": findings_data,
            "resume_text_sample": raw_text[:2000]
        }
        user_prompt = build_resume_prompt(prompt_data)

        # Generate via AI with deterministic fallback
        raw_output, is_ai, provider_name = ai_provider_manager.generate_with_fallback(
            system_prompt=RESUME_EXPLANATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            json_mode=True
        )

        parsed_data = self._safe_parse_json(raw_output)

        # Build finding explanations
        finding_explanations: List[Dict[str, Any]] = []
        raw_items = parsed_data.get("finding_explanations", [])
        if raw_items and isinstance(raw_items, list):
            for item in raw_items:
                if isinstance(item, dict):
                    finding_explanations.append({
                        "finding_id": str(item.get("finding_id", "gen-finding")),
                        "issue_title": str(item.get("issue_title", "Resume Item")),
                        "section": str(item.get("section", "general")),
                        "original_excerpt": str(item.get("original_excerpt", "")),
                        "explanation": str(item.get("explanation", "Finding noted in resume audit.")),
                        "impact_reason": str(item.get("impact_reason", "Impacts presentation quality.")),
                        "concrete_suggestion": str(item.get("concrete_suggestion", "Refine this line.")),
                        "missing_facts_requested": item.get("missing_facts_requested")
                    })

        # If findings were present in analysis but AI didn't format them, backfill from review_findings
        if not finding_explanations and findings_data:
            for f in findings_data[:5]:
                finding_explanations.append({
                    "finding_id": str(f.get("id", "finding-auto")),
                    "issue_title": str(f.get("title", "Review Finding")),
                    "section": str(f.get("section", "general")),
                    "original_excerpt": "",
                    "explanation": str(f.get("description", "")),
                    "impact_reason": "Directly impacts recruiter conversion rates.",
                    "concrete_suggestion": "Revise using STAR action phrasing and quantified outcomes.",
                    "missing_facts_requested": None
                })

        # Process prioritized recommendations
        raw_recs = parsed_data.get("prioritized_recommendations", [])
        structured_recs: List[PrioritizedRecommendation] = []
        if raw_recs and isinstance(raw_recs, list):
            for r in raw_recs:
                if isinstance(r, dict):
                    try:
                        structured_recs.append(PrioritizedRecommendation(
                            id=str(r.get("id", f"rec-{len(structured_recs)+1}")),
                            priority=str(r.get("priority", "medium")).lower(),
                            category=str(r.get("category", "experience")),
                            title=str(r.get("title", "Action Item")),
                            description=str(r.get("description", "")),
                            linked_finding_id=r.get("linked_finding_id"),
                            priority_reason=str(r.get("priority_reason", "Recommended action")),
                            effort_estimate=str(r.get("effort_estimate", "moderate"))
                        ))
                    except Exception:
                        pass

        # If recommendations are still empty, build deterministically
        if not structured_recs:
            structured_recs = recommendation_service.build_resume_recommendations(
                findings=findings_data,
                overall_score=immutable_score,
                skills=prompt_data["skills"]
            )

        summary = parsed_data.get("executive_summary")
        if not summary or not isinstance(summary, str) or len(summary.strip()) < 10:
            summary = (
                f"Your resume scored {immutable_score}/100 ({immutable_tier}). "
                "Overall formatting and technical skill coverage provide a strong baseline; "
                "focusing on action-oriented impact metrics will elevate your hiring competitive standing."
            )

        return {
            "resume_id": resume_id,
            "is_ai_generated": is_ai,
            "provider": provider_name,
            "overall_score": immutable_score,  # IMMUTABLE!
            "readiness_tier": immutable_tier,  # IMMUTABLE!
            "executive_summary": summary,
            "finding_explanations": finding_explanations,
            "prioritized_recommendations": [r.model_dump() for r in structured_recs],
            "disclaimer": "AI recommendations provide advisory guidance. Verification and final editing remain the candidate's prerogative.",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    def explain_job_match(self, match_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates grounded explanations for job compatibility analysis,
        preserving deterministic matching scores.
        """
        match = job_service.get_match(match_id=match_id, user_id=user_id)
        
        immutable_score = int(match.get("overall_match_score", 0))
        company = str(match.get("company", "Target Company"))
        role = str(match.get("role", "Target Role"))
        requirements = match.get("evaluated_requirements", [])

        # Build prompt payload
        prompt_data = {
            "overall_match_score": immutable_score,
            "hard_skill_score": int(match.get("hard_skill_score", 0)),
            "experience_match_score": int(match.get("experience_match_score", 0)),
            "company": company,
            "role": role,
            "requirements": requirements,
            "job_description_sample": match.get("job_description_snippet", "")[:1500],
            "resume_sample": ""
        }
        user_prompt = build_job_match_prompt(prompt_data)

        raw_output, is_ai, provider_name = ai_provider_manager.generate_with_fallback(
            system_prompt=JOB_MATCH_EXPLANATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            json_mode=True
        )

        parsed_data = self._safe_parse_json(raw_output)

        req_explanations: List[Dict[str, Any]] = []
        raw_items = parsed_data.get("requirement_explanations", [])
        if raw_items and isinstance(raw_items, list):
            for item in raw_items:
                if isinstance(item, dict):
                    req_explanations.append({
                        "requirement_name": str(item.get("requirement_name", "Requirement")),
                        "status": str(item.get("status", "partial")),
                        "importance": str(item.get("importance", "required")),
                        "job_requirement_explanation": str(item.get("job_requirement_explanation", "Role requirement.")),
                        "candidate_evidence_summary": str(item.get("candidate_evidence_summary", "No clear evidence.")),
                        "evidence_quote": str(item.get("evidence_quote", "")),
                        "recommended_action": str(item.get("recommended_action", "Address in resume."))
                    })

        # Backfill if empty
        if not req_explanations and requirements:
            for r in requirements:
                req_explanations.append({
                    "requirement_name": str(r.get("name", "Skill")),
                    "status": str(r.get("status", "partial")),
                    "importance": str(r.get("importance", "required")),
                    "job_requirement_explanation": f"Required proficiency for {role} role.",
                    "candidate_evidence_summary": str(r.get("reason", "Evaluated from candidate resume.")),
                    "evidence_quote": str(r.get("matched_keyword", "")),
                    "recommended_action": "Emphasize practical usage in project descriptions."
                })

        raw_recs = parsed_data.get("prioritized_recommendations", [])
        structured_recs: List[PrioritizedRecommendation] = []
        if raw_recs and isinstance(raw_recs, list):
            for r in raw_recs:
                if isinstance(r, dict):
                    try:
                        structured_recs.append(PrioritizedRecommendation(
                            id=str(r.get("id", f"rec-match-{len(structured_recs)+1}")),
                            priority=str(r.get("priority", "high")).lower(),
                            category=str(r.get("category", "skills")),
                            title=str(r.get("title", "Skill Action")),
                            description=str(r.get("description", "")),
                            linked_finding_id=r.get("linked_finding_id"),
                            priority_reason=str(r.get("priority_reason", "Job match priority")),
                            effort_estimate=str(r.get("effort_estimate", "moderate"))
                        ))
                    except Exception:
                        pass

        if not structured_recs:
            structured_recs = recommendation_service.build_job_match_recommendations(
                requirements=requirements,
                overall_match_score=immutable_score
            )

        summary = parsed_data.get("match_summary")
        if not summary or not isinstance(summary, str) or len(summary.strip()) < 10:
            summary = (
                f"Candidate compatibility with {role} at {company} is calculated at {immutable_score}%. "
                "Core qualifications show healthy alignment, with targeted opportunities to demonstrate depth in secondary requirements."
            )

        return {
            "match_id": match_id,
            "is_ai_generated": is_ai,
            "provider": provider_name,
            "overall_match_score": immutable_score,  # IMMUTABLE!
            "company": company,
            "role": role,
            "match_summary": summary,
            "requirement_explanations": req_explanations,
            "prioritized_recommendations": [r.model_dump() for r in structured_recs],
            "disclaimer": "Compatibility analysis is based on algorithmic matching and available resume text.",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    def _safe_parse_json(self, raw_text: str) -> Dict[str, Any]:
        """Safely parses JSON output from AI models, stripping markdown fences if present."""
        if not raw_text:
            return {}
        
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except Exception as e:
            logger.warning(f"Failed to parse AI JSON response: {e}. Payload was: {raw_text[:200]}")
            return {}

explanation_service = ExplanationService()
