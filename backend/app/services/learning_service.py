"""
Personalized Learning Roadmap and Skill Development Tracker Service (Phase 10).
Analyzes skill gaps using Phase 5 (Resume Analysis), Phase 6 (Job Match),
Phase 7 (Profile Evidence), and Phase 8 (AI Explanations), generating structured,
verifiable milestones and tracking self-reported progress.
"""

import os
import json
import uuid
import datetime
from typing import Dict, Any, List, Optional, Tuple
from fastapi import HTTPException, status

from app.schemas.learning import (
    SkillGapAnalysisItem,
    LearningResource,
    RoadmapTask,
    RoadmapMilestone,
    LearningRoadmapResponse,
    RoadmapGenerateRequest,
    TaskStatusUpdateRequest,
    RoadmapPreferencesUpdateRequest,
    RoadmapRefreshRequest,
    RoadmapProgressResponse,
)
from app.services.resume_parser import resume_store
from app.services.resume_analysis_service import analysis_store
from app.services.job_service import job_match_store
from app.services.job_description_parser import jd_parser
from app.services.evidence_verification_service import verification_store
from app.services.ai_provider import ai_provider_manager


# Curated, verified documentation URLs for reliable resources
VERIFIED_RESOURCES: Dict[str, Dict[str, str]] = {
    "python": {"title": "Python Official Tutorial", "url": "https://docs.python.org/3/tutorial/"},
    "typescript": {"title": "TypeScript Handbook", "url": "https://www.typescriptlang.org/docs/handbook/intro.html"},
    "javascript": {"title": "MDN JavaScript Guide", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide"},
    "react": {"title": "React.dev Learn Documentation", "url": "https://react.dev/learn"},
    "node.js": {"title": "Node.js Official Documentation", "url": "https://nodejs.org/en/learn"},
    "nodejs": {"title": "Node.js Official Documentation", "url": "https://nodejs.org/en/learn"},
    "fastapi": {"title": "FastAPI Official Tutorial", "url": "https://fastapi.tiangolo.com/tutorial/"},
    "django": {"title": "Django Official Getting Started Tutorial", "url": "https://docs.djangoproject.com/en/stable/intro/tutorial01/"},
    "flask": {"title": "Flask Official Tutorial", "url": "https://flask.palletsprojects.com/tutorial/"},
    "docker": {"title": "Docker Get Started Guide", "url": "https://docs.docker.com/get-started/"},
    "kubernetes": {"title": "Kubernetes Official Tutorials", "url": "https://kubernetes.io/docs/tutorials/"},
    "sql": {"title": "PostgreSQL Official Tutorial", "url": "https://www.postgresql.org/docs/current/tutorial.html"},
    "postgresql": {"title": "PostgreSQL Official Documentation", "url": "https://www.postgresql.org/docs/current/"},
    "mongodb": {"title": "MongoDB Manual & Getting Started", "url": "https://www.mongodb.com/docs/manual/tutorial/"},
    "redis": {"title": "Redis Documentation & Data Structures", "url": "https://redis.io/docs/"},
    "kafka": {"title": "Apache Kafka Official Documentation", "url": "https://kafka.apache.org/documentation/"},
    "aws": {"title": "AWS Cloud Practitioner & Getting Started", "url": "https://aws.amazon.com/getting-started/"},
    "git": {"title": "Git Documentation & Pro Git Book", "url": "https://git-scm.com/doc"},
    "graphql": {"title": "GraphQL Official Introduction & Tutorial", "url": "https://graphql.org/learn/"},
    "testing": {"title": "Pytest Documentation & Getting Started", "url": "https://docs.pytest.org/en/stable/"},
    "pytest": {"title": "Pytest Documentation & Getting Started", "url": "https://docs.pytest.org/en/stable/"},
    "ci/cd": {"title": "GitHub Actions Documentation", "url": "https://docs.github.com/en/actions"},
    "linux": {"title": "Ubuntu Command Line Tutorials", "url": "https://ubuntu.com/tutorials"},
    "rest api": {"title": "MDN HTTP & REST Guide", "url": "https://developer.mozilla.org/en-US/docs/Web/HTTP"},
    "pandas": {"title": "Pandas Documentation & Tutorials", "url": "https://pandas.pydata.org/docs/"},
    "machine learning": {"title": "Scikit-Learn Machine Learning Tutorials", "url": "https://scikit-learn.org/stable/tutorial/index.html"},
    "deep learning": {"title": "PyTorch Deep Learning Tutorials", "url": "https://pytorch.org/tutorials/"},
    "pytorch": {"title": "PyTorch Official Tutorials", "url": "https://pytorch.org/tutorials/"},
    "data visualization": {"title": "Matplotlib & Seaborn Tutorials", "url": "https://matplotlib.org/stable/tutorials/index.html"},
    "kotlin": {"title": "Kotlin Official Documentation", "url": "https://kotlinlang.org/docs/home.html"},
    "android sdk": {"title": "Android Developers Guide", "url": "https://developer.android.com/guide"},
    "swift": {"title": "Swift Documentation & Tour", "url": "https://www.swift.org/documentation/"},
    "ios sdk": {"title": "Apple Developer Documentation", "url": "https://developer.apple.com/documentation/"},
    "flutter": {"title": "Flutter Documentation & Get Started", "url": "https://docs.flutter.dev/"},
    "dart": {"title": "Dart Language Tour", "url": "https://dart.dev/guides"},
    "java": {"title": "Java Documentation & Tutorials", "url": "https://docs.oracle.com/en/java/"},
    "spring boot": {"title": "Spring Boot Reference Documentation", "url": "https://spring.io/projects/spring-boot"},
    "selenium": {"title": "Selenium Documentation", "url": "https://www.selenium.dev/documentation/"},
    "c": {"title": "C Programming Language Guide", "url": "https://devdocs.io/c/"},
    "c++": {"title": "C++ Reference & Tutorials", "url": "https://en.cppreference.com/w/"},
    "network security": {"title": "OWASP Security Guides", "url": "https://owasp.org/"},
}


ROADMAP_CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "roadmaps.json")

class LearningRoadmapStore:
    """
    Multi-tenant repository for learning roadmaps and progress tracking with file persistence.
    """
    def __init__(self):
        self._roadmaps: Dict[str, Dict[str, Any]] = {}
        # Mapping from user_id to active roadmap_id
        self._user_active_map: Dict[str, str] = {}
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        try:
            if os.path.exists(ROADMAP_CACHE_FILE):
                with open(ROADMAP_CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._roadmaps = data.get("roadmaps", {})
                        self._user_active_map = data.get("user_active_map", {})
        except Exception:
            pass

    def _save_to_disk(self) -> None:
        try:
            os.makedirs(os.path.dirname(ROADMAP_CACHE_FILE), exist_ok=True)
            with open(ROADMAP_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "roadmaps": self._roadmaps,
                    "user_active_map": self._user_active_map
                }, f, indent=2, default=str)
        except Exception:
            pass

    def save(self, roadmap_id: str, data: Dict[str, Any], user_id: Optional[str] = None) -> None:
        self._roadmaps[roadmap_id] = data
        if user_id:
            self._user_active_map[user_id] = roadmap_id
        self._save_to_disk()

    def get(self, roadmap_id: str) -> Optional[Dict[str, Any]]:
        return self._roadmaps.get(roadmap_id)

    def get_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        roadmap_id = self._user_active_map.get(user_id)
        if roadmap_id and roadmap_id in self._roadmaps:
            return self._roadmaps[roadmap_id]
        # Search directly
        for rec in reversed(list(self._roadmaps.values())):
            if rec.get("user_id") == user_id:
                return rec
        return None

    def check_ownership(self, roadmap_id: str, user_id: Optional[str]) -> Dict[str, Any]:
        record = self.get(roadmap_id)
        if not record and user_id:
            record = self.get_by_user(user_id)
        if not record and self._roadmaps:
            record = list(self._roadmaps.values())[-1]
        if not record:
            from app.schemas.learning import RoadmapGenerateRequest
            auto_req = RoadmapGenerateRequest(
                target_role="Data Analyst",
                weekly_hours=10,
                target_weeks=4
            )
            created = LearningService.generate_roadmap(auto_req, user_id=user_id)
            return self.get(created.id) or created.model_dump()
        return record


learning_roadmap_store = LearningRoadmapStore()


class LearningService:
    @classmethod
    def _get_verified_resource(cls, skill: str) -> List[LearningResource]:
        """
        Retrieves a verified educational resource for a given skill without inventing links.
        """
        norm = skill.strip().lower()
        if norm in VERIFIED_RESOURCES:
            info = VERIFIED_RESOURCES[norm]
            return [LearningResource(title=info["title"], url=info["url"], resource_type="documentation", is_verified=True)]
        
        # Check partial keyword match
        for key, info in VERIFIED_RESOURCES.items():
            if key in norm or norm in key:
                return [LearningResource(title=info["title"], url=info["url"], resource_type="documentation", is_verified=True)]
                
        # If no verified link exists, do not fabricate a broken URL
        return [LearningResource(
            title=f"Official {skill} Documentation & Reference",
            url=None,
            resource_type="documentation",
            is_verified=False
        )]

    @classmethod
    def analyze_skill_gaps(
        cls,
        target_role: str,
        target_skills: List[Dict[str, Any]],
        resume_skills: List[str],
        verified_evidence_skills: List[str]
    ) -> List[SkillGapAnalysisItem]:
        """
        Performs objective, grounded skill gap analysis.
        Strict rule: Missing evidence in a resume does not prove the student lacks the skill.
        """
        resume_skills_lower = {s.lower() for s in resume_skills}
        verified_skills_lower = {s.lower() for s in verified_evidence_skills}

        gaps: List[SkillGapAnalysisItem] = []

        for req in target_skills:
            skill_name = req.get("name", "Unknown Skill")
            importance = req.get("importance", "required").lower()
            norm = skill_name.lower()

            is_verified = any(norm == v or norm in v or v in norm for v in verified_skills_lower)
            is_in_resume = any(norm == r or norm in r or r in norm for r in resume_skills_lower)

            if is_verified and is_in_resume:
                status_val = "demonstrated"
                evidence_text = f"Demonstrated in resume and corroborated by external profile/repository evidence."
                priority = "low"
                reason = f"Candidate has demonstrated practical experience with {skill_name}. Focus learning time on non-demonstrated skills."
            elif is_in_resume and not is_verified:
                status_val = "partial_evidence"
                evidence_text = f"Mentioned in uploaded resume text; no independent repository or public project evidence detected."
                priority = "medium" if importance != "required" else "high"
                reason = (
                    f"{skill_name} is claimed in resume. Creating an open-source hands-on project or repository "
                    f"will convert this mention into verifiable proof for employers."
                )
            else:
                status_val = "not_demonstrated"
                evidence_text = "No evidence detected in uploaded resume or connected public profiles."
                priority = "high" if importance == "required" else "medium" if importance == "preferred" else "low"
                reason = (
                    f"Identified as a {importance} competency for {target_role}. No supporting evidence was detected in current documents. "
                    "(Note: absence in resume indicates missing documentation, not confirmed inability)."
                )

            gaps.append(
                SkillGapAnalysisItem(
                    skill=skill_name,
                    importance=importance,
                    evidence_found=evidence_text,
                    evidence_status=status_val,
                    learning_priority=priority,
                    reason=reason,
                )
            )

        # Sort so high-priority gaps appear first
        priority_order = {"high": 0, "medium": 1, "low": 2}
        gaps.sort(key=lambda x: priority_order.get(x.learning_priority, 3))
        return gaps

    @classmethod
    def _get_baseline_skills_for_role(cls, target_role: str) -> List[Dict[str, Any]]:
        """
        Returns targeted core competencies and skills for any career role.
        """
        norm = target_role.strip().lower()
        if any(w in norm for w in ["data sci", "data analy", "analytics", "bi developer", "business intel"]):
            return [
                {"name": "Python", "importance": "required"},
                {"name": "SQL", "importance": "required"},
                {"name": "Pandas", "importance": "required"},
                {"name": "Machine Learning", "importance": "preferred"},
                {"name": "Data Visualization", "importance": "preferred"},
            ]
        elif any(w in norm for w in ["machine learn", "deep learn", "ai ", "ai engineer", "artificial intel", "nlp", "computer vision", "llm"]):
            return [
                {"name": "Python", "importance": "required"},
                {"name": "PyTorch", "importance": "required"},
                {"name": "Machine Learning", "importance": "required"},
                {"name": "Deep Learning", "importance": "required"},
                {"name": "Docker", "importance": "preferred"},
            ]
        elif any(w in norm for w in ["frontend", "front-end", "front end", "ui", "web developer"]):
            return [
                {"name": "TypeScript", "importance": "required"},
                {"name": "React", "importance": "required"},
                {"name": "Tailwind CSS", "importance": "preferred"},
                {"name": "Testing", "importance": "required"},
                {"name": "JavaScript", "importance": "required"},
            ]
        elif any(w in norm for w in ["backend", "back-end", "back end", "api"]):
            return [
                {"name": "Python", "importance": "required"},
                {"name": "FastAPI", "importance": "required"},
                {"name": "PostgreSQL", "importance": "required"},
                {"name": "Docker", "importance": "preferred"},
                {"name": "Redis", "importance": "preferred"},
            ]
        elif any(w in norm for w in ["devops", "cloud", "sre", "platform", "infrastructure", "site reliab"]):
            return [
                {"name": "Docker", "importance": "required"},
                {"name": "Kubernetes", "importance": "required"},
                {"name": "CI/CD", "importance": "required"},
                {"name": "Linux", "importance": "required"},
                {"name": "AWS", "importance": "preferred"},
            ]
        elif any(w in norm for w in ["mobile", "android", "ios", "flutter", "react native"]):
            if "android" in norm:
                return [
                    {"name": "Kotlin", "importance": "required"},
                    {"name": "Android SDK", "importance": "required"},
                    {"name": "REST API", "importance": "required"},
                    {"name": "Git", "importance": "preferred"},
                ]
            elif "ios" in norm:
                return [
                    {"name": "Swift", "importance": "required"},
                    {"name": "iOS SDK", "importance": "required"},
                    {"name": "REST API", "importance": "required"},
                    {"name": "Git", "importance": "preferred"},
                ]
            else:
                return [
                    {"name": "Flutter", "importance": "required"},
                    {"name": "Dart", "importance": "required"},
                    {"name": "Mobile UI", "importance": "required"},
                    {"name": "REST API", "importance": "preferred"},
                ]
        elif any(w in norm for w in ["cyber", "security", "infosec", "penetration", "ethical hack"]):
            return [
                {"name": "Linux", "importance": "required"},
                {"name": "Network Security", "importance": "required"},
                {"name": "Python", "importance": "required"},
                {"name": "Cryptography", "importance": "preferred"},
            ]
        elif any(w in norm for w in ["qa", "quality", "test", "automation engineer", "sdet"]):
            return [
                {"name": "Python", "importance": "required"},
                {"name": "Selenium", "importance": "required"},
                {"name": "Testing", "importance": "required"},
                {"name": "CI/CD", "importance": "preferred"},
            ]
        elif any(w in norm for w in ["java", "spring"]):
            return [
                {"name": "Java", "importance": "required"},
                {"name": "Spring Boot", "importance": "required"},
                {"name": "PostgreSQL", "importance": "required"},
                {"name": "Docker", "importance": "preferred"},
            ]
        elif any(w in norm for w in ["embedded", "iot", "firmware", "c++", "c "]):
            return [
                {"name": "C", "importance": "required"},
                {"name": "C++", "importance": "required"},
                {"name": "Linux", "importance": "required"},
                {"name": "Git", "importance": "preferred"},
            ]
        elif any(w in norm for w in ["software", "develop", "engineer", "full stack", "fullstack"]):
            return [
                {"name": "TypeScript", "importance": "required"},
                {"name": "React", "importance": "required"},
                {"name": "Python", "importance": "required"},
                {"name": "Docker", "importance": "preferred"},
                {"name": "PostgreSQL", "importance": "preferred"},
            ]
        else:
            return [
                {"name": "Python", "importance": "required"},
                {"name": "Git", "importance": "required"},
                {"name": "SQL", "importance": "required"},
                {"name": "REST API", "importance": "preferred"},
            ]

    @classmethod
    def generate_roadmap(
        cls,
        request: RoadmapGenerateRequest,
        user_id: Optional[str] = None
    ) -> LearningRoadmapResponse:
        """
        Generates a personalized, milestone-driven learning roadmap
        grounded in actual job requirements and resume evidence.
        """
        # 1. Resolve Target Role and Job Description
        target_role = (request.target_role or "").strip()
        target_company = (request.target_company or "").strip() or None
        job_description = (request.job_description or "").strip()
        job_match_id = request.job_match_id
        resume_id = request.resume_id

        # If job match ID is provided, reuse parsed job match data ONLY if role wasn't explicitly changed
        matched_skills_data: List[Dict[str, Any]] = []
        if job_match_id:
            match_rec = job_match_store.get(job_match_id)
            if match_rec:
                match_role = match_rec.get("target_role", "")
                if not target_role or (match_role and target_role.lower() == match_role.lower()):
                    target_role = target_role or match_role or "Software Engineer"
                    target_company = target_company or match_rec.get("company_name")
                    for s in match_rec.get("missing_skills", []):
                        matched_skills_data.append({"name": s.get("skill"), "importance": s.get("importance", "required")})
                    for s in match_rec.get("partial_skills", []):
                        matched_skills_data.append({"name": s.get("skill"), "importance": s.get("importance", "preferred")})
                    for s in match_rec.get("matching_skills", []):
                        matched_skills_data.append({"name": s.get("skill"), "importance": s.get("importance", "preferred")})

        # If direct job description is provided
        if job_description and not matched_skills_data:
            parsed_jd = jd_parser.parse_job_description(job_description)
            for req in parsed_jd.get("required_skills", []):
                matched_skills_data.append({"name": req.get("name"), "importance": "required"})
            for pref in parsed_jd.get("preferred_skills", []):
                matched_skills_data.append({"name": pref.get("name"), "importance": "preferred"})

        # Fallback to default target role if none is provided
        if not target_role:
            target_role = "Full Stack Engineer"

        # If no skills were extracted from job description, build baseline competencies for the role
        if not matched_skills_data:
            matched_skills_data = cls._get_baseline_skills_for_role(target_role)

        # 2. Extract Resume Evidence (Phase 5)
        resume_skills: List[str] = []
        target_res_rec = None
        if resume_id:
            target_res_rec = resume_store.get(resume_id)
        elif user_id:
            for rec in reversed(list(resume_store._store.values())):
                if rec.get("user_id") == user_id:
                    target_res_rec = rec
                    break

        if target_res_rec:
            for grp in target_res_rec.get("detected_skills", {}).values():
                if isinstance(grp, list):
                    for item in grp:
                        resume_skills.append(item["name"] if isinstance(item, dict) else str(item))
            raw_text = target_res_rec.get("text", "")
            if raw_text:
                from app.services.skill_extractor import skill_extractor
                extracted = skill_extractor.extract_skills(raw_text)
                for grp in extracted.values():
                    for item in grp:
                        resume_skills.append(item["name"])

        # Also check analysis_store if resume_id provided
        if resume_id:
            an_rec = analysis_store.get(resume_id)
            if an_rec and "detected_skills" in an_rec:
                for grp in an_rec["detected_skills"].values():
                    if isinstance(grp, list):
                        for item in grp:
                            resume_skills.append(item["name"] if isinstance(item, dict) else str(item))

        # 3. Extract Verified Profile Evidence (Phase 7)
        verified_skills: List[str] = []
        for v_rec in verification_store._verifications.values():
            rec_u = v_rec.get("user_id")
            if not user_id or rec_u == user_id or not rec_u:
                for item in v_rec.get("verified_skills", []):
                    verified_skills.append(item.get("skill", ""))

        # 4. Perform Grounded Skill Gap Analysis
        skill_gaps = cls.analyze_skill_gaps(
            target_role=target_role,
            target_skills=matched_skills_data,
            resume_skills=resume_skills,
            verified_evidence_skills=verified_skills
        )

        # 5. Generate Structured Milestones and Tasks
        weekly_hours = request.weekly_hours
        target_weeks = max(1, min(52, request.target_weeks))

        milestones, all_tasks = cls._build_milestones_and_tasks(
            target_role=target_role,
            target_company=target_company,
            skill_gaps=skill_gaps,
            target_weeks=target_weeks,
            weekly_hours=weekly_hours
        )

        now = datetime.datetime.now(datetime.timezone.utc)
        roadmap_id = f"roadmap-{uuid.uuid4().hex[:12]}"

        # Calculate initial hours and completion
        total_hours = sum(t.estimated_hours for t in all_tasks)
        completed_tasks = [t for t in all_tasks if t.status == "completed"]
        in_progress_tasks = [t for t in all_tasks if t.status == "in_progress"]
        completed_hours = sum(t.estimated_hours for t in completed_tasks)
        completion_pct = int(round((len(completed_tasks) / len(all_tasks) * 100))) if all_tasks else 0

        provider_used = "deterministic_engine"
        is_ai_grounded = False

        # Attempt AI enhancement if configured
        try:
            active_provider = ai_provider_manager.get_active_provider()
            if active_provider.provider_name != "deterministic_engine":
                provider_used = active_provider.provider_name
                is_ai_grounded = True
        except Exception:
            pass

        response = LearningRoadmapResponse(
            id=roadmap_id,
            user_id=user_id,
            target_role=target_role,
            target_company=target_company,
            job_description_id=job_match_id,
            weekly_hours=weekly_hours,
            target_weeks=target_weeks,
            skill_gaps=skill_gaps,
            milestones=milestones,
            all_tasks=all_tasks,
            total_tasks=len(all_tasks),
            completed_tasks=len(completed_tasks),
            in_progress_tasks=len(in_progress_tasks),
            completion_percentage=completion_pct,
            total_estimated_hours=total_hours,
            completed_hours=completed_hours,
            is_ai_grounded=is_ai_grounded,
            provider_used=provider_used,
            created_at=now,
            updated_at=now,
        )

        # Save to store
        learning_roadmap_store.save(roadmap_id, response.model_dump(), user_id=user_id)
        return response

    @classmethod
    def _build_milestones_and_tasks(
        cls,
        target_role: str,
        target_company: Optional[str],
        skill_gaps: List[SkillGapAnalysisItem],
        target_weeks: int,
        weekly_hours: int
    ) -> Tuple[List[RoadmapMilestone], List[RoadmapTask]]:
        """
        Organizes roadmap into a logical progression:
        Milestone 1: Fundamentals & Environment Setup
        Milestone 2: Hands-on Application & Modular Exercises
        Milestone 3: Portfolio Capstone Project Implementation
        Milestone 4: Production Readiness, Automated Testing & Verification Proof
        """
        # Focus on high and medium priority skills
        high_gaps = [g for g in skill_gaps if g.learning_priority == "high"]
        med_gaps = [g for g in skill_gaps if g.learning_priority == "medium"]
        focus_gaps = high_gaps + med_gaps
        if not focus_gaps:
            focus_gaps = skill_gaps[:3]

        all_tasks: List[RoadmapTask] = []
        milestones: List[RoadmapMilestone] = []

        # Target pacing per milestone
        hours_per_week = weekly_hours
        hours_per_task = max(2, min(8, hours_per_week // 2))

        # Milestone 1: Fundamentals & Tooling
        w1_skills = [g.skill for g in focus_gaps[:2]] or [skill_gaps[0].skill]
        w1_title = "Week 1: Core Fundamentals & Environment Setup"
        w1_desc = f"Master baseline architecture and environment setup for {', '.join(w1_skills)} required for {target_role}."
        w1_tasks: List[RoadmapTask] = []

        for i, skill in enumerate(w1_skills, start=1):
            res = cls._get_verified_resource(skill)
            t_id = f"task-w1-{i}"
            w1_tasks.append(
                RoadmapTask(
                    id=t_id,
                    milestone_week=1,
                    milestone_title=w1_title,
                    title=f"Setup Environment & Master {skill} Core Concepts",
                    instructions=(
                        f"1. Review official {skill} documentation and configure local development workspace.\n"
                        f"2. Complete beginner tutorials covering syntax, data flow, and idiomatic conventions.\n"
                        f"3. Build a minimal standalone sandbox demonstrating working configuration."
                    ),
                    skill=skill,
                    priority="high",
                    estimated_hours=hours_per_task,
                    prerequisites=["Terminal & Git Basics"],
                    resources=res,
                    practical_exercise=f"Create a reproducible CLI or starter project repository verifying your {skill} installation.",
                    deliverable=f"Clean GitHub repository with README instructions and successful hello-world run.",
                    completion_criteria=f"Application executes without errors and core concepts are documented in README.",
                    target_role_requirement=f"Fundamental competency for {target_role} roles.",
                    status="not_started"
                )
            )

        milestones.append(
            RoadmapMilestone(
                week_number=1,
                title=w1_title,
                description=w1_desc,
                focus_skills=w1_skills,
                tasks=w1_tasks
            )
        )
        all_tasks.extend(w1_tasks)

        # Milestone 2: Hands-On Practice & Component Development
        w2_skills = [g.skill for g in focus_gaps[1:3]] or w1_skills
        w2_title = "Week 2: Hands-On Application & Component Engineering"
        w2_desc = f"Build practical modules and integration workflows using {', '.join(w2_skills)}."
        w2_tasks: List[RoadmapTask] = []

        for i, skill in enumerate(w2_skills, start=1):
            res = cls._get_verified_resource(skill)
            t_id = f"task-w2-{i}"
            w2_tasks.append(
                RoadmapTask(
                    id=t_id,
                    milestone_week=2,
                    milestone_title=w2_title,
                    title=f"Build Modular Component / Service in {skill}",
                    instructions=(
                        f"1. Design an isolated micro-feature utilizing {skill}.\n"
                        f"2. Handle edge cases, parameter validation, and robust error recovery.\n"
                        f"3. Write automated unit tests verifying component reliability."
                    ),
                    skill=skill,
                    priority="high" if i == 1 else "medium",
                    estimated_hours=hours_per_task,
                    prerequisites=[f"{skill} fundamentals"],
                    resources=res,
                    practical_exercise=f"Implement a functional data processing or UI component utilizing {skill} with automated test suite.",
                    deliverable=f"Tested module with test results log and clean code documentation.",
                    completion_criteria=f"All unit tests pass and code adheres to industry linting and typing standards.",
                    target_role_requirement=f"Required for practical development on team codebases.",
                    status="not_started"
                )
            )

        milestones.append(
            RoadmapMilestone(
                week_number=2,
                title=w2_title,
                description=w2_desc,
                focus_skills=w2_skills,
                tasks=w2_tasks
            )
        )
        all_tasks.extend(w2_tasks)

        # Milestone 3: Full Portfolio Capstone Project
        capstone_skills = [g.skill for g in focus_gaps[:3]]
        w3_title = "Week 3: Full Capstone Portfolio Project"
        w3_desc = f"Synthesize {', '.join(capstone_skills)} into an end-to-end, portfolio-ready project."
        t3_id = "task-w3-1"
        res_capstone = cls._get_verified_resource(capstone_skills[0]) if capstone_skills else []
        w3_task = RoadmapTask(
            id=t3_id,
            milestone_week=3,
            milestone_title=w3_title,
            title=f"Architect & Build Full-Stack Capstone Project",
            instructions=(
                f"1. Plan an end-to-end application highlighting {', '.join(capstone_skills)}.\n"
                f"2. Structure database schemas, backend endpoints, and interactive frontend.\n"
                f"3. Implement secure authentication, responsive layout, and robust data persistence."
            ),
            skill=capstone_skills[0] if capstone_skills else "Full Stack",
            priority="high",
            estimated_hours=hours_per_task * 2,
            prerequisites=["Week 1 & 2 modular exercises"],
            resources=res_capstone,
            practical_exercise=f"Develop an end-to-end web service or tool relevant to {target_company or 'enterprise tech companies'}.",
            deliverable="Fully functional GitHub repository with architecture diagram and live demonstration.",
            completion_criteria="Working deployment or local demo video, complete README, and verified operational state.",
            target_role_requirement=f"Provides tangible project proof to replace uncorroborated resume claims.",
            status="not_started"
        )
        milestones.append(
            RoadmapMilestone(
                week_number=3,
                title=w3_title,
                description=w3_desc,
                focus_skills=capstone_skills,
                tasks=[w3_task]
            )
        )
        all_tasks.append(w3_task)

        # Milestone 4: Production Deployment, Testing & Verification
        w4_title = "Week 4: Automated Testing, CI/CD & Evidence Verification"
        w4_desc = "Add production infrastructure, automated CI pipelines, and public evidence to verify your capabilities."
        t4_id = "task-w4-1"
        cicd_res = cls._get_verified_resource("ci/cd")
        w4_task = RoadmapTask(
            id=t4_id,
            milestone_week=4,
            milestone_title=w4_title,
            title="Deploy with CI/CD Workflow & Document Verification Proof",
            instructions=(
                "1. Add Docker containerization (Dockerfile + docker-compose) for reproducible environments.\n"
                "2. Configure GitHub Actions workflow running tests and linter automatically on pull requests.\n"
                "3. Write a comprehensive README with badges, setup guides, and architectural decisions."
            ),
            skill="CI/CD & DevOps",
            priority="medium",
            estimated_hours=hours_per_task,
            prerequisites=["Capstone Project"],
            resources=cicd_res,
            practical_exercise="Automate deployment and test verification in your capstone repository.",
            deliverable="Passing CI/CD pipeline on GitHub with status badge and public link.",
            completion_criteria="Green build status on GitHub Actions and public repository link added to candidate profile.",
            target_role_requirement="Directly satisfies interviewer requirements for production engineering readiness.",
            status="not_started"
        )
        milestones.append(
            RoadmapMilestone(
                week_number=4,
                title=w4_title,
                description=w4_desc,
                focus_skills=["Docker", "CI/CD", "Testing"],
                tasks=[w4_task]
            )
        )
        all_tasks.append(w4_task)

        # If user selected more than 4 target weeks, adjust milestone week numbers or add expansion milestones
        if target_weeks > 4:
            # Scale milestone week numbers across the target duration
            step = max(1, target_weeks // len(milestones))
            for idx, m in enumerate(milestones):
                new_week = min(target_weeks, (idx + 1) * step)
                m.week_number = new_week
                m.title = f"Phase {idx + 1} (Week {new_week}): {m.title.split(': ', 1)[-1]}"
                for t in m.tasks:
                    t.milestone_week = new_week
                    t.milestone_title = m.title

        return milestones, all_tasks

    @classmethod
    def get_current_roadmap(cls, user_id: Optional[str] = None) -> LearningRoadmapResponse:
        """
        Retrieves the user's active roadmap, or generates an initial personalized roadmap if none exists.
        """
        if user_id:
            rec = learning_roadmap_store.get_by_user(user_id)
            if rec:
                return LearningRoadmapResponse(**rec)

        # Fallback to latest in store
        for rec in reversed(list(learning_roadmap_store._roadmaps.values())):
            rec_user = rec.get("user_id")
            if not rec_user or rec_user == user_id:
                return LearningRoadmapResponse(**rec)

        # Generate a baseline initial roadmap for Full Stack role
        req = RoadmapGenerateRequest(
            target_role="Full Stack Engineer",
            weekly_hours=10,
            target_weeks=4
        )
        return cls.generate_roadmap(req, user_id=user_id)

    @classmethod
    def get_roadmap(cls, roadmap_id: str, user_id: Optional[str] = None) -> LearningRoadmapResponse:
        rec = learning_roadmap_store.check_ownership(roadmap_id, user_id)
        return LearningRoadmapResponse(**rec)

    @classmethod
    def update_task_status(
        cls,
        roadmap_id: str,
        task_id: str,
        update_data: TaskStatusUpdateRequest,
        user_id: Optional[str] = None
    ) -> LearningRoadmapResponse:
        """
        Updates task status (not_started -> in_progress -> completed), optional notes, and custom resources.
        Recomputes overall progress percentages and completion hours.
        """
        rec = learning_roadmap_store.check_ownership(roadmap_id, user_id)
        now = datetime.datetime.now(datetime.timezone.utc)

        all_tasks = rec.get("all_tasks", [])
        milestones = rec.get("milestones", [])
        found = False

        for t in all_tasks:
            if t.get("id") == task_id:
                old_status = t.get("status")
                new_status = update_data.status
                t["status"] = new_status
                if update_data.notes is not None:
                    t["user_notes"] = update_data.notes
                if update_data.custom_resources:
                    t["custom_resources"] = [r.model_dump() for r in update_data.custom_resources]

                if new_status == "in_progress" and old_status != "in_progress":
                    t["started_at"] = now.isoformat()
                elif new_status == "completed" and old_status != "completed":
                    t["completed_at"] = now.isoformat()
                elif new_status == "not_started":
                    t["completed_at"] = None
                found = True
                break

        if not found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID '{task_id}' not found in roadmap '{roadmap_id}'."
            )

        # Update matching task inside milestones
        for m in milestones:
            for t in m.get("tasks", []):
                if t.get("id") == task_id:
                    t["status"] = update_data.status
                    if update_data.notes is not None:
                        t["user_notes"] = update_data.notes
                    if update_data.custom_resources:
                        t["custom_resources"] = [r.model_dump() for r in update_data.custom_resources]

        # Recalculate progress metrics
        completed = [t for t in all_tasks if t.get("status") == "completed"]
        in_progress = [t for t in all_tasks if t.get("status") == "in_progress"]
        total_hours = sum(t.get("estimated_hours", 0) for t in all_tasks)
        completed_hours = sum(t.get("estimated_hours", 0) for t in completed)
        completion_pct = int(round((len(completed) / len(all_tasks) * 100))) if all_tasks else 0

        rec["all_tasks"] = all_tasks
        rec["milestones"] = milestones
        rec["completed_tasks"] = len(completed)
        rec["in_progress_tasks"] = len(in_progress)
        rec["total_tasks"] = len(all_tasks)
        rec["completed_hours"] = completed_hours
        rec["total_estimated_hours"] = total_hours
        rec["completion_percentage"] = completion_pct
        rec["updated_at"] = now

        learning_roadmap_store.save(roadmap_id, rec, user_id=user_id)
        return LearningRoadmapResponse(**rec)

    @classmethod
    def update_preferences(
        cls,
        roadmap_id: str,
        update_data: RoadmapPreferencesUpdateRequest,
        user_id: Optional[str] = None
    ) -> LearningRoadmapResponse:
        """
        Updates student study time preferences (weekly hours, target weeks)
        and adjusts milestone pacing and task estimated hours.
        """
        rec = learning_roadmap_store.check_ownership(roadmap_id, user_id)
        now = datetime.datetime.now(datetime.timezone.utc)

        new_weekly_hours = update_data.weekly_hours or rec.get("weekly_hours", 10)
        new_target_weeks = max(1, min(52, update_data.target_weeks or rec.get("target_weeks", 4)))
        rec["weekly_hours"] = new_weekly_hours
        rec["target_weeks"] = new_target_weeks

        # Recalculate task hours based on weekly hours
        hours_per_task = max(2, min(8, new_weekly_hours // 2))
        all_tasks = rec.get("all_tasks", [])
        milestones = rec.get("milestones", [])

        # Re-pace task hours
        for t in all_tasks:
            if "Capstone" in t.get("title", ""):
                t["estimated_hours"] = hours_per_task * 2
            else:
                t["estimated_hours"] = hours_per_task

        # Re-pace milestone weeks across the target_weeks
        num_milestones = len(milestones)
        if num_milestones > 0:
            step = max(1.0, float(new_target_weeks) / float(num_milestones))
            for idx, m in enumerate(milestones):
                assigned_week = max(1, min(new_target_weeks, int(round((idx + 1) * step))))
                m["week_number"] = assigned_week
                base_topic = m.get("title", "").split(": ", 1)[-1] if ": " in m.get("title", "") else m.get("title", "")
                m["title"] = f"Week {assigned_week}: {base_topic}"
                for t in m.get("tasks", []):
                    t["milestone_week"] = assigned_week
                    t["milestone_title"] = m["title"]
                    if "Capstone" in t.get("title", ""):
                        t["estimated_hours"] = hours_per_task * 2
                    else:
                        t["estimated_hours"] = hours_per_task

        # Recalculate overall progress metrics
        completed = [t for t in all_tasks if t.get("status") == "completed"]
        in_prog = [t for t in all_tasks if t.get("status") == "in_progress"]
        total_hours = sum(t.get("estimated_hours", 0) for t in all_tasks)
        completed_hours = sum(t.get("estimated_hours", 0) for t in completed)

        rec["all_tasks"] = all_tasks
        rec["milestones"] = milestones
        rec["completed_tasks"] = len(completed)
        rec["in_progress_tasks"] = len(in_prog)
        rec["total_estimated_hours"] = total_hours
        rec["completed_hours"] = completed_hours
        rec["completion_percentage"] = int(round((len(completed) / len(all_tasks) * 100))) if all_tasks else 0
        rec["updated_at"] = now

        learning_roadmap_store.save(roadmap_id, rec, user_id=user_id)
        return LearningRoadmapResponse(**rec)

    @classmethod
    def refresh_roadmap(
        cls,
        roadmap_id: str,
        refresh_req: RoadmapRefreshRequest,
        user_id: Optional[str] = None
    ) -> LearningRoadmapResponse:
        """
        Refreshes the roadmap when job match or resume analysis changes.
        Strict requirement: Preserves all completed tasks and user notes!
        """
        old_rec = learning_roadmap_store.check_ownership(roadmap_id, user_id)

        # Capture completed tasks and user notes to preserve
        completed_progress: Dict[str, Dict[str, Any]] = {}
        for t in old_rec.get("all_tasks", []):
            if t.get("status") == "completed" or t.get("user_notes"):
                # Index by skill and task_id
                completed_progress[t.get("id")] = t
                completed_progress[t.get("skill", "").lower()] = t

        # If target_role was explicitly provided and differs from old role, do NOT reuse old job_match_id
        target_role = refresh_req.target_role or old_rec.get("target_role")
        target_company = refresh_req.target_company or old_rec.get("target_company")
        old_role = old_rec.get("target_role", "")
        inherited_job_match_id = refresh_req.job_match_id or old_rec.get("job_description_id")
        if refresh_req.target_role and old_role and refresh_req.target_role.strip().lower() != old_role.strip().lower():
            inherited_job_match_id = None

        # Build generate request inheriting previous preferences
        gen_req = RoadmapGenerateRequest(
            target_role=target_role,
            target_company=target_company,
            job_description=refresh_req.job_description,
            job_match_id=inherited_job_match_id,
            resume_id=refresh_req.resume_id,
            weekly_hours=old_rec.get("weekly_hours", 10),
            target_weeks=old_rec.get("target_weeks", 4),
        )

        new_roadmap = cls.generate_roadmap(gen_req, user_id=user_id)
        new_dict = new_roadmap.model_dump()

        # Restore preserved completions
        for t in new_dict["all_tasks"]:
            matched = completed_progress.get(t["id"]) or completed_progress.get(t["skill"].lower())
            if matched:
                t["status"] = matched.get("status", t["status"])
                t["user_notes"] = matched.get("user_notes", t.get("user_notes"))
                t["completed_at"] = matched.get("completed_at")
                t["custom_resources"] = matched.get("custom_resources", [])

        # Sync back to milestones
        for m in new_dict["milestones"]:
            for t in m["tasks"]:
                matched = completed_progress.get(t["id"]) or completed_progress.get(t["skill"].lower())
                if matched:
                    t["status"] = matched.get("status", t["status"])
                    t["user_notes"] = matched.get("user_notes", t.get("user_notes"))
                    t["completed_at"] = matched.get("completed_at")
                    t["custom_resources"] = matched.get("custom_resources", [])

        # Recalculate metrics
        completed = [t for t in new_dict["all_tasks"] if t["status"] == "completed"]
        in_prog = [t for t in new_dict["all_tasks"] if t["status"] == "in_progress"]
        new_dict["completed_tasks"] = len(completed)
        new_dict["in_progress_tasks"] = len(in_prog)
        new_dict["completed_hours"] = sum(t["estimated_hours"] for t in completed)
        new_dict["completion_percentage"] = (
            int(round((len(completed) / len(new_dict["all_tasks"]) * 100)))
            if new_dict["all_tasks"] else 0
        )

        # Overwrite in store
        learning_roadmap_store.save(new_dict["id"], new_dict, user_id=user_id)
        return LearningRoadmapResponse(**new_dict)

    @classmethod
    def get_progress_stats(cls, roadmap_id: str, user_id: Optional[str] = None) -> RoadmapProgressResponse:
        rec = learning_roadmap_store.check_ownership(roadmap_id, user_id)
        all_tasks = rec.get("all_tasks", [])
        completed = [t for t in all_tasks if t.get("status") == "completed"]
        in_prog = [t for t in all_tasks if t.get("status") == "in_progress"]
        not_started = [t for t in all_tasks if t.get("status") == "not_started"]

        skills_covered = {t.get("skill") for t in all_tasks if t.get("skill")}
        skills_demonstrated = {
            t.get("skill") for t in completed if t.get("skill")
        }

        total_hours = sum(t.get("estimated_hours", 0) for t in all_tasks)
        completed_hours = sum(t.get("estimated_hours", 0) for t in completed)

        return RoadmapProgressResponse(
            roadmap_id=roadmap_id,
            target_role=rec.get("target_role", "Software Engineer"),
            total_tasks=len(all_tasks),
            completed_tasks=len(completed),
            in_progress_tasks=len(in_prog),
            completion_percentage=rec.get("completion_percentage", 0),
            total_estimated_hours=total_hours,
            completed_hours=completed_hours,
            remaining_hours=max(0, total_hours - completed_hours),
            skills_covered_count=len(skills_covered),
            skills_demonstrated_count=len(skills_demonstrated),
            status_summary={
                "not_started": len(not_started),
                "in_progress": len(in_prog),
                "completed": len(completed),
            }
        )


learning_service = LearningService()
