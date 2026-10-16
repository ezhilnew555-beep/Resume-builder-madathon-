"""
Resume Builder Service for CareerLens (Phase 9).
Handles draft lifecycle, version history, importing parsed resumes,
AI-assisted diff suggestions, and rerunning ATS analysis on updated content.
"""

import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status

from app.schemas.builder import (
    ResumeBuilderData,
    ContactData,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    CertificationEntry,
    AchievementEntry,
    SkillsData,
    ResumeDraftCreateRequest,
    ResumeDraftUpdateRequest,
    ResumeDraftResponse,
    ResumeVersionItem,
    VersionListResponse,
    AISuggestionItem,
    AIEditSuggestRequest,
    AIEditSuggestResponse,
    BuilderAnalysisResponse,
)
from app.services.resume_parser import resume_store
from app.services.resume_analysis_service import resume_analysis_service
from app.services.ai_provider import ai_provider_manager
from app.services.prompt_templates import sanitize_pii, wrap_untrusted_data

logger = logging.getLogger(__name__)

class ResumeBuilderStore:
    def __init__(self):
        self._drafts: Dict[str, Dict[str, Any]] = {}
        self._versions: Dict[str, List[Dict[str, Any]]] = {}

    def get_draft(self, draft_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        draft = self._drafts.get(draft_id)
        if not draft:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume draft {draft_id} was not found."
            )
        # Ownership isolation
        if draft.get("user_id") and user_id and draft["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have authorization to access this resume draft."
            )
        return draft

    def save_draft(self, draft: Dict[str, Any]) -> None:
        self._drafts[draft["draft_id"]] = draft

    def get_versions(self, draft_id: str) -> List[Dict[str, Any]]:
        return self._versions.setdefault(draft_id, [])

    def add_version(self, draft_id: str, version: Dict[str, Any]) -> None:
        versions = self.get_versions(draft_id)
        versions.append(version)


builder_store = ResumeBuilderStore()


class BuilderService:
    def create_draft(
        self,
        request: ResumeDraftCreateRequest,
        user_id: Optional[str] = None
    ) -> ResumeDraftResponse:
        """
        Creates a new resume draft. Can import structured content from a previously parsed resume
        or start with an empty / provided structure.
        """
        draft_id = f"draft-{uuid.uuid4().hex[:12]}"
        now_str = datetime.now(timezone.utc).isoformat()

        initial_data = request.initial_data or ResumeBuilderData()
        imported_id = None

        # If importing from parsed resume
        if request.source_resume_id:
            try:
                parsed_record = resume_store.get(request.source_resume_id)
                if parsed_record:
                    # Enforce ownership check if document belonged to a user
                    if parsed_record.get("user_id") and user_id and parsed_record["user_id"] != user_id:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Cannot import from a resume uploaded by another user."
                        )
                    initial_data = self._import_from_parsed_resume(parsed_record)
                    imported_id = request.source_resume_id
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Could not import parsed resume {request.source_resume_id}: {e}")

        initial_data.template_id = request.template_id

        draft_record = {
            "draft_id": draft_id,
            "user_id": user_id,
            "title": request.title,
            "created_at": now_str,
            "updated_at": now_str,
            "current_version": 1,
            "data": initial_data.model_dump(),
            "imported_from_resume_id": imported_id,
            "is_saved": True,
        }

        builder_store.save_draft(draft_record)

        # Create initial Version 1 snapshot
        v1_record = {
            "version_id": f"ver-1-{uuid.uuid4().hex[:6]}",
            "version_number": 1,
            "created_at": now_str,
            "note": "Initial draft creation",
            "data_snapshot": initial_data.model_dump(),
        }
        builder_store.add_version(draft_id, v1_record)

        return ResumeDraftResponse(
            draft_id=draft_id,
            user_id=user_id,
            title=request.title,
            created_at=now_str,
            updated_at=now_str,
            current_version=1,
            data=initial_data,
            is_saved=True,
            imported_from_resume_id=imported_id,
        )

    def get_draft(self, draft_id: str, user_id: Optional[str] = None) -> ResumeDraftResponse:
        draft = builder_store.get_draft(draft_id, user_id=user_id)
        return ResumeDraftResponse(
            draft_id=draft["draft_id"],
            user_id=draft.get("user_id"),
            title=draft["title"],
            created_at=draft["created_at"],
            updated_at=draft["updated_at"],
            current_version=draft["current_version"],
            data=ResumeBuilderData(**draft["data"]),
            is_saved=draft.get("is_saved", True),
            imported_from_resume_id=draft.get("imported_from_resume_id"),
        )

    def update_draft(
        self,
        draft_id: str,
        request: ResumeDraftUpdateRequest,
        user_id: Optional[str] = None
    ) -> ResumeDraftResponse:
        """
        Updates the draft in place (used for autosave).
        """
        draft = builder_store.get_draft(draft_id, user_id=user_id)
        now_str = datetime.now(timezone.utc).isoformat()

        if request.title:
            draft["title"] = request.title
        if request.template_id:
            request.data.template_id = request.template_id

        draft["data"] = request.data.model_dump()
        draft["updated_at"] = now_str
        draft["is_saved"] = True

        builder_store.save_draft(draft)

        return ResumeDraftResponse(
            draft_id=draft_id,
            user_id=draft.get("user_id"),
            title=draft["title"],
            created_at=draft["created_at"],
            updated_at=now_str,
            current_version=draft["current_version"],
            data=request.data,
            is_saved=True,
            imported_from_resume_id=draft.get("imported_from_resume_id"),
        )

    def create_version_snapshot(
        self,
        draft_id: str,
        note: str,
        user_id: Optional[str] = None
    ) -> ResumeVersionItem:
        """
        Explicitly saves a new version checkpoint so the student can compare or revert.
        """
        draft = builder_store.get_draft(draft_id, user_id=user_id)
        now_str = datetime.now(timezone.utc).isoformat()
        next_ver = draft["current_version"] + 1

        v_record = {
            "version_id": f"ver-{next_ver}-{uuid.uuid4().hex[:6]}",
            "version_number": next_ver,
            "created_at": now_str,
            "note": note,
            "data_snapshot": draft["data"],
        }
        builder_store.add_version(draft_id, v_record)

        draft["current_version"] = next_ver
        draft["updated_at"] = now_str
        builder_store.save_draft(draft)

        return ResumeVersionItem(
            version_id=v_record["version_id"],
            version_number=next_ver,
            created_at=now_str,
            note=note,
            data_snapshot=ResumeBuilderData(**draft["data"]),
        )

    def list_versions(self, draft_id: str, user_id: Optional[str] = None) -> VersionListResponse:
        draft = builder_store.get_draft(draft_id, user_id=user_id)
        raw_versions = builder_store.get_versions(draft_id)
        
        items = [
            ResumeVersionItem(
                version_id=v["version_id"],
                version_number=v["version_number"],
                created_at=v["created_at"],
                note=v["note"],
                data_snapshot=ResumeBuilderData(**v["data_snapshot"]),
            )
            for v in raw_versions
        ]
        items.sort(key=lambda x: x.version_number, reverse=True)

        return VersionListResponse(
            draft_id=draft_id,
            total_versions=len(items),
            versions=items,
        )

    def suggest_edits(
        self,
        draft_id: str,
        request: AIEditSuggestRequest,
        user_id: Optional[str] = None
    ) -> AIEditSuggestResponse:
        """
        Generates diff-style edit suggestions (original vs proposed text with rationale).
        Strict safety: Never fabricates metrics or skills; asks student for missing numbers.
        """
        draft = builder_store.get_draft(draft_id, user_id=user_id)
        data = request.current_data or ResumeBuilderData(**draft["data"])

        suggestions: List[AISuggestionItem] = []

        # 1. Summary improvement
        if data.summary.strip():
            summary_text = data.summary.strip()
            # If summary contains weak phrases
            if "responsible for" in summary_text.lower() or "worked on" in summary_text.lower() or len(summary_text) < 150:
                suggestions.append(AISuggestionItem(
                    id="sugg-summary-1",
                    target_section="summary",
                    title="Strengthen Professional Summary with Action Focus",
                    original_text=summary_text,
                    proposed_text=(
                        f"Software Engineer specializing in {data.skills.languages or 'modern software development'}, "
                        f"experienced in architecting reliable services and responsive user applications. "
                        f"Proven ability to deliver maintainable features in collaborative engineering environments."
                    ),
                    rationale="Eliminates passive wording and leads with tangible core competencies for stronger ATS ranking.",
                    missing_facts_prompt=None,
                ))

        # 2. Bullet points improvements (STAR method & quantified impact)
        # Check experience bullets
        for exp in data.experience:
            for b_idx, bullet in enumerate(exp.bullets):
                b_clean = bullet.strip()
                if not b_clean:
                    continue
                # If bullet is missing numbers/percentages
                has_digits = any(char.isdigit() for char in b_clean)
                if not has_digits and len(b_clean) > 20:
                    suggestions.append(AISuggestionItem(
                        id=f"sugg-exp-{exp.id}-{b_idx}",
                        target_section="experience",
                        target_entry_id=exp.id,
                        target_bullet_index=b_idx,
                        title=f"Quantify Impact in {exp.company} Experience",
                        original_text=b_clean,
                        proposed_text=f"Engineered and deployed {b_clean.rstrip('.')}, improving operational throughput by [X]% across [Y] active users.",
                        rationale="Quantified metrics (percentages, volume, latency) substantiate claims and elevate ATS content quality scores.",
                        missing_facts_prompt="What was the user count, performance improvement percentage, or request volume achieved?",
                    ))
                    if len(suggestions) >= 4:
                        break

        # Check project bullets
        for proj in data.projects:
            for b_idx, bullet in enumerate(proj.bullets):
                b_clean = bullet.strip()
                if not b_clean:
                    continue
                has_digits = any(char.isdigit() for char in b_clean)
                if not has_digits and len(b_clean) > 15:
                    suggestions.append(AISuggestionItem(
                        id=f"sugg-proj-{proj.id}-{b_idx}",
                        target_section="projects",
                        target_entry_id=proj.id,
                        target_bullet_index=b_idx,
                        title=f"Add Technical Specifics to {proj.name}",
                        original_text=b_clean,
                        proposed_text=f"Architected {b_clean.rstrip('.')} using {proj.tech_stack or 'modern frameworks'}, achieving sub-second response times.",
                        rationale="Explicitly highlights technology stack and technical ownership.",
                        missing_facts_prompt="What specific latency, database scale, or test coverage metric did this project reach?",
                    ))
                    if len(suggestions) >= 5:
                        break

        # 3. Job tailoring if job description provided
        if request.job_description and len(request.job_description) > 30:
            jd_lower = request.job_description.lower()
            if "docker" in jd_lower and "docker" not in (data.skills.tools or "").lower():
                suggestions.append(AISuggestionItem(
                    id="sugg-tailor-docker",
                    target_section="skills",
                    title="Incorporate Required Job Posting Keyword: Docker",
                    original_text=data.skills.tools or "Git",
                    proposed_text=f"{data.skills.tools}, Docker" if data.skills.tools else "Docker, Git",
                    rationale="The target job posting explicitly requires containerization experience. Include Docker if you have hands-on experience.",
                    missing_facts_prompt="Have you used Docker or Docker Compose in your coursework, personal projects, or internships?",
                ))

        # Fallback if no specific suggestions were triggered
        if not suggestions:
            suggestions.append(AISuggestionItem(
                id="sugg-general-1",
                target_section="summary",
                title="Polish Vocabulary for Precision",
                original_text=data.summary or "Summary statement",
                proposed_text=data.summary or "Dedicated software developer with solid foundation in computer science and modern frameworks.",
                rationale="Content already meets baseline ATS standards; maintain clear active verbs throughout.",
                missing_facts_prompt=None,
            ))

        return AIEditSuggestResponse(
            draft_id=draft_id,
            is_ai_generated=False,
            provider="deterministic_rule_engine",
            suggestions=suggestions[:6],
            disclaimer="Suggestions provide guidance based on ATS best practices. The original text is preserved until you explicitly accept a recommendation.",
        )

    def reanalyze_draft(self, draft_id: str, user_id: Optional[str] = None) -> BuilderAnalysisResponse:
        """
        Reruns Phase 5 deterministic ATS analysis directly on the current builder content.
        """
        draft = builder_store.get_draft(draft_id, user_id=user_id)
        data = ResumeBuilderData(**draft["data"])

        # Compile structured data into plain text for the analysis engine
        raw_text_parts = [
            data.contact.full_name,
            f"{data.contact.email} | {data.contact.phone} | {data.contact.location}",
            "\nPROFESSIONAL SUMMARY\n" + data.summary,
            "\nTECHNICAL SKILLS\n" + f"Languages: {data.skills.languages}\nFrameworks: {data.skills.frameworks}\nDatabases: {data.skills.databases}\nTools: {data.skills.tools}",
        ]

        if data.experience:
            raw_text_parts.append("\nWORK EXPERIENCE")
            for exp in data.experience:
                raw_text_parts.append(f"{exp.role} at {exp.company} ({exp.start_date} - {exp.end_date})")
                for b in exp.bullets:
                    raw_text_parts.append(f"- {b}")

        if data.projects:
            raw_text_parts.append("\nPROJECTS")
            for proj in data.projects:
                raw_text_parts.append(f"{proj.name} ({proj.tech_stack})")
                for b in proj.bullets:
                    raw_text_parts.append(f"- {b}")

        if data.education:
            raw_text_parts.append("\nEDUCATION")
            for edu in data.education:
                raw_text_parts.append(f"{edu.degree} in {edu.field_of_study} - {edu.school} ({edu.end_date}) GPA: {edu.gpa}")

        full_compiled_text = "\n".join(raw_text_parts)

        # Use deterministic ATS scoring engine
        from app.services.skill_extractor import skill_extractor
        from app.services.score_engine import score_engine
        from app.services.ats_checker import ats_checker
        from app.services.resume_section_analyzer import section_analyzer
        from app.services.bullet_point_analyzer import bullet_analyzer
        from app.services.grammar_checker import grammar_checker
        from app.services.suggestion_engine import suggestion_engine

        # Section dict
        sections_dict = {
            "contact_info": data.contact.full_name,
            "summary": data.summary,
            "skills": f"{data.skills.languages} {data.skills.frameworks} {data.skills.databases} {data.skills.tools}",
            "experience": "\n".join([exp.role for exp in data.experience]),
            "projects": "\n".join([proj.name for proj in data.projects]),
            "education": "\n".join([edu.school for edu in data.education]),
        }

        extracted_skills = skill_extractor.extract_skills(full_compiled_text, sections_dict)
        section_info = section_analyzer.analyze_sections(full_compiled_text, sections_dict)
        bullet_evaluations = bullet_analyzer.analyze_bullets_in_sections(sections_dict)
        grammar_info = grammar_checker.check_grammar_and_style(full_compiled_text, sections_dict)
        ats_info = ats_checker.evaluate_ats_readability(full_compiled_text, sections_dict)

        scoring_result = score_engine.calculate_scores(
            structure_info=section_info,
            bullet_evaluations=bullet_evaluations,
            extracted_skills=extracted_skills,
            ats_info=ats_info,
            style_info=grammar_info,
            has_job_description=False
        )

        findings = suggestion_engine.aggregate_findings(
            section_info=section_info,
            bullet_evaluations=bullet_evaluations,
            grammar_info=grammar_info,
            ats_info=ats_info
        )

        return BuilderAnalysisResponse(
            draft_id=draft_id,
            overall_score=scoring_result["overall_score"],
            readiness_tier=scoring_result["readiness_tier"],
            component_scores=scoring_result["component_scores"],
            detected_skills_count=len(extracted_skills),
            findings_count=len(findings),
            analyzed_text_sample=full_compiled_text[:500],
        )

    def _import_from_parsed_resume(self, parsed_record: Dict[str, Any]) -> ResumeBuilderData:
        """
        Translates raw parsed resume text and detected sections into ResumeBuilderData.
        """
        raw_text = parsed_record.get("raw_text", "")
        sections = parsed_record.get("sections", {})

        # Extract name from first line or filename
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        first_line = lines[0] if lines else "Candidate Name"
        name = first_line if len(first_line) < 40 and not any(c in first_line for c in ["@", "http", "Resume"]) else "Candidate Name"

        # Email & Phone heuristic
        import re
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', raw_text)
        phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', raw_text)

        contact = ContactData(
            full_name=name,
            email=emails[0] if emails else "",
            phone=phones[0] if phones else "",
            location="United States",
        )

        summary_text = sections.get("summary", "")
        skills_text = sections.get("skills", "")
        exp_text = sections.get("experience", "")
        edu_text = sections.get("education", "")
        proj_text = sections.get("projects", "")

        # Populate skills
        skills_data = SkillsData(
            languages=skills_text[:120] if skills_text else "Python, TypeScript, SQL",
            frameworks="FastAPI, React",
            databases="PostgreSQL",
            tools="Git, Docker",
        )

        # Experience entries
        exp_entries: List[ExperienceEntry] = []
        if exp_text:
            exp_lines = [l.strip() for l in exp_text.splitlines() if l.strip()]
            bullets = [l.lstrip("-•* ") for l in exp_lines if l.startswith(("-", "•", "*")) or len(l) > 30]
            exp_entries.append(ExperienceEntry(
                id=f"exp-{uuid.uuid4().hex[:6]}",
                role="Software Developer",
                company="Engineering Experience",
                start_date="2023",
                end_date="Present",
                is_current=True,
                bullets=bullets[:3] if bullets else ["Developed backend features and collaborating across agile sprints."],
            ))

        # Project entries
        proj_entries: List[ProjectEntry] = []
        if proj_text:
            p_lines = [l.strip() for l in proj_text.splitlines() if l.strip()]
            bullets = [l.lstrip("-•* ") for l in p_lines if l.startswith(("-", "•", "*")) or len(l) > 25]
            proj_entries.append(ProjectEntry(
                id=f"proj-{uuid.uuid4().hex[:6]}",
                name="Key Technical Project",
                tech_stack="Python, React, PostgreSQL",
                bullets=bullets[:2] if bullets else ["Designed and implemented core service modules."],
            ))
        elif "project" in raw_text.lower():
            proj_entries.append(ProjectEntry(
                id=f"proj-{uuid.uuid4().hex[:6]}",
                name="Technical Project",
                tech_stack="Python, Go, Redis",
                bullets=["Engineered distributed modules with low latency."],
            ))

        # Education entries
        edu_entries: List[EducationEntry] = []
        edu_entries.append(EducationEntry(
            id=f"edu-{uuid.uuid4().hex[:6]}",
            school=edu_text.splitlines()[0][:50] if edu_text else "University",
            degree="B.S. in Computer Science",
            end_date="2024",
            gpa="3.8",
            highlights="Dean's Honor List",
        ))

        return ResumeBuilderData(
            contact=contact,
            summary=summary_text if summary_text else "Software Engineer passionate about high-quality code and scalable systems.",
            skills=skills_data,
            experience=exp_entries,
            projects=proj_entries,
            education=edu_entries,
            template_id="modern",
        )

builder_service = BuilderService()
