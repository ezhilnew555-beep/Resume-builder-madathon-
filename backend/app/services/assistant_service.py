"""
Contextual AI Career Assistant Service for CareerLens (Phase 8).
Enables interactive, evidence-grounded Q&A for students regarding their
resume diagnostics, job match gaps, and evidence verification findings.
Strictly isolates user reports and enforces authorization boundaries.
"""

import logging
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status

from app.schemas.explanation import (
    AssistantChatRequest,
    AssistantChatResponse,
    AssistantChatMessage
)
from app.services.resume_analysis_service import resume_analysis_service
from app.services.job_service import job_service
from app.services.evidence_verification_service import evidence_verification_service
from app.services.ai_provider import ai_provider_manager
from app.services.prompt_templates import (
    ASSISTANT_SYSTEM_PROMPT,
    sanitize_pii,
    wrap_untrusted_data
)

logger = logging.getLogger(__name__)

class AssistantService:
    def chat(
        self,
        request: AssistantChatRequest,
        user_id: Optional[str] = None
    ) -> AssistantChatResponse:
        """
        Processes a candidate question, grounding the answer strictly in permitted reports.
        Enforces user ownership on resume_id, match_id, and verification_id.
        """
        referenced_reports: List[str] = []
        context_blocks: List[str] = []

        # 1. Inspect and validate resume report
        if request.resume_id:
            try:
                analysis = resume_analysis_service.get_analysis(request.resume_id, user_id=user_id)
                referenced_reports.append(f"Resume Analysis ({request.resume_id[:8]})")
                score = analysis.get("overall_score", 0)
                tier = analysis.get("readiness_tier", "Unknown")
                findings = analysis.get("review_findings", [])
                skills = [s.get("name", "") for s in analysis.get("detected_skills", []) if isinstance(s, dict)]
                
                context_blocks.append(
                    f"[Resume Report Summary]\n"
                    f"Overall Score: {score}/100\n"
                    f"Readiness Tier: {tier}\n"
                    f"Identified Skills: {', '.join(skills[:15])}\n"
                    f"Key Findings ({len(findings)} total):\n" +
                    "\n".join([f"- {f.get('title')}: {f.get('description')}" for f in findings[:4]])
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Could not load resume context {request.resume_id}: {e}")

        # 2. Inspect and validate job match report
        if request.match_id:
            try:
                match = job_service.get_match(request.match_id, user_id=user_id)
                referenced_reports.append(f"Job Match ({match.get('company', 'Target')} - {match.get('role', 'Role')})")
                match_score = match.get("overall_match_score", 0)
                reqs = match.get("evaluated_requirements", [])
                
                context_blocks.append(
                    f"[Job Match Report Summary]\n"
                    f"Target Role: {match.get('role')} at {match.get('company')}\n"
                    f"Match Score: {match_score}%\n"
                    f"Evaluated Requirements:\n" +
                    "\n".join([f"- {r.get('name')}: {r.get('status')} ({r.get('importance')})" for r in reqs[:5]])
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Could not load match context {request.match_id}: {e}")

        # 3. Inspect and validate evidence verification report
        if request.verification_id:
            try:
                veri = evidence_verification_service.get_verification_report(request.verification_id, user_id=user_id)
                referenced_reports.append(f"GitHub Evidence Verification ({request.verification_id[:8]})")
                v_score = veri.get("evidence_score", 0)
                tier = veri.get("confidence_tier", "Unknown")
                claims = veri.get("claim_verifications", [])
                
                context_blocks.append(
                    f"[Evidence Verification Summary]\n"
                    f"Evidence Verification Score: {v_score}/100\n"
                    f"Confidence Tier: {tier}\n"
                    f"Claims Audited ({len(claims)}):\n" +
                    "\n".join([f"- {c.get('claim_text')}: {c.get('verification_status')}" for c in claims[:4]])
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Could not load verification context {request.verification_id}: {e}")

        # Assemble system and user prompts
        context_str = "\n\n".join(context_blocks) if context_blocks else "No specific report IDs attached to this prompt."
        safe_context = wrap_untrusted_data("PERMITTED_USER_REPORTS", context_str)

        # Sanitize user query
        sanitized_query = sanitize_pii(request.message)

        # Build conversation history
        history_lines = []
        for msg in request.history[-5:]:
            history_lines.append(f"{msg.role.upper()}: {sanitize_pii(msg.content)}")
        history_str = "\n".join(history_lines) if history_lines else "No previous conversation."

        full_user_prompt = f"""Conversation History:
{history_str}

Candidate Report Data:
{safe_context}

Candidate Current Question:
{sanitized_query}

Provide a direct, helpful, evidence-grounded response:"""

        # Generate via AI with deterministic fallback
        raw_reply, is_ai, provider_name = ai_provider_manager.generate_with_fallback(
            system_prompt=ASSISTANT_SYSTEM_PROMPT,
            user_prompt=full_user_prompt,
            json_mode=False
        )

        # If deterministic provider was used or reply is empty, tailor rule-based answer
        if not is_ai or not raw_reply:
            raw_reply = self._generate_rule_based_reply(sanitized_query, context_blocks)

        suggested_followups = self._generate_followups(sanitized_query, referenced_reports)

        return AssistantChatResponse(
            reply=raw_reply,
            is_ai_generated=is_ai,
            provider=provider_name,
            referenced_reports=referenced_reports,
            suggested_followups=suggested_followups
        )

    def _generate_rule_based_reply(self, query: str, context_blocks: List[str]) -> str:
        q = query.lower()
        if "score" in q or "improve" in q or "ats" in q:
            return (
                "To improve your CareerLens score, focus on two high-yield changes:\n\n"
                "1. **Quantify Bullet Points:** Replace generic task descriptions with measurable outcomes "
                "(e.g., 'Optimized database queries, reducing API response times by 35%').\n"
                "2. **Standardize Section Headers:** Use universal headings like 'Technical Skills', 'Experience', "
                "and 'Education' so parsing parsers index your credentials without ambiguities."
            )
        elif "github" in q or "verify" in q or "evidence" in q:
            return (
                "For project evidence verification, technical recruiters look for verifiable proof:\n\n"
                "- Ensure every repository cited has a clear **README.md** describing architecture and setup.\n"
                "- Commit actual code rather than empty repositories, and include tests where appropriate.\n"
                "- Pin your top 2-3 production-quality repositories on your public GitHub profile."
            )
        elif "job" in q or "match" in q or "company" in q:
            return (
                "When tailoring for a target job description:\n\n"
                "- Directly mention the required core frameworks and languages if you have hands-on experience.\n"
                "- If a required tool is missing from your background, consider building a targeted demo project "
                "or completing relevant coursework to turn that gap into a talking point."
            )
        else:
            return (
                "I am your CareerLens career assistant. Based on your current diagnostics, "
                "I can help you interpret your ATS resume score, explain specific job compatibility gaps, "
                "or suggest rewrites for your project bullet points. What specific section would you like to review?"
            )

    def _generate_followups(self, query: str, referenced_reports: List[str]) -> List[str]:
        q = query.lower()
        if "score" in q or "resume" in q:
            return [
                "How do I write project bullets in STAR format?",
                "Which skills are missing from my resume?",
                "How can I test my resume against a job description?"
            ]
        elif "job" in q or "match" in q:
            return [
                "What are my highest priority missing qualifications?",
                "Can I match equivalent skills like PostgreSQL for SQL?",
                "How should I address missing required skills?"
            ]
        elif "github" in q or "evidence" in q:
            return [
                "Why did a claim receive 'needs_verification'?",
                "How do I connect my GitHub profile?",
                "What makes a strong README for technical recruiters?"
            ]
        return [
            "How can I increase my resume ATS score?",
            "How do I match my resume against a job posting?",
            "What projects should I highlight on GitHub?"
        ]

assistant_service = AssistantService()
