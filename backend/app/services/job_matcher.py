import re
from typing import Dict, List, Any, Optional, Tuple

EQUIVALENCE_MAP: Dict[str, List[str]] = {
    "sql": ["postgresql", "mysql", "sqlite", "oracle", "mariadb", "sql server"],
    "relational database": ["postgresql", "mysql", "sqlite", "oracle", "sql"],
    "nosql": ["mongodb", "redis", "cassandra", "dynamodb"],
    "frontend framework": ["react", "vue", "angular", "next.js", "svelte"],
    "modern frontend": ["react", "typescript", "vue", "next.js"],
    "python web framework": ["fastapi", "django", "flask"],
    "backend framework": ["fastapi", "django", "flask", "express", "node.js", "spring boot", "nest.js"],
    "cloud platform": ["aws", "azure", "gcp", "google cloud", "amazon web services"],
    "containerization": ["docker", "kubernetes"],
    "ci/cd": ["github actions", "jenkins", "gitlab ci", "continuous integration"],
    "rest api": ["fastapi", "flask", "express", "django", "restful", "api"],
}

class JobMatchingEngine:
    # Deterministic configurable scoring weights
    WEIGHTS = {
        "required_skills": 0.50,
        "preferred_skills": 0.20,
        "experience_relevance": 0.15,
        "evidence_strength": 0.15,
    }

    @classmethod
    def match_resume_to_job(
        cls,
        resume_record: Dict[str, Any],
        parsed_jd: Dict[str, Any],
        analysis_record: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compares candidate resume against job description requirements.
        Distinguishes required vs preferred criteria, bare mentions vs demonstrated evidence,
        and applies credible terminology equivalents.
        """
        raw_resume = resume_record.get("raw_text", "")
        sections = resume_record.get("sections", {})
        experience_text = sections.get("experience", "")
        projects_text = sections.get("projects", "")
        skills_text = sections.get("skills", "")
        education_text = sections.get("education", "")

        # Extract verified skills if analysis already executed
        candidate_skills_dict = {}
        if analysis_record and "extracted_skills" in analysis_record:
            for cat, items in analysis_record["extracted_skills"].items():
                for itm in items:
                    candidate_skills_dict[itm["name"].lower()] = itm

        # 1. Match Required Skills
        matched_reqs: List[Dict[str, Any]] = []
        partial_matches: List[Dict[str, Any]] = []
        missing_evidence: List[Dict[str, Any]] = []

        all_jd_requirements = parsed_jd["required_skills"] + parsed_jd["preferred_skills"]

        # If no explicit skills detected in JD, evaluate against general tech keywords
        if not all_jd_requirements:
            all_jd_requirements = [
                {"name": "Technical Problem Solving", "category": "general", "importance": "required", "evidence_snippet": "General technical engineering", "occurrences": 1}
            ]

        for req in all_jd_requirements:
            match_item = cls._evaluate_requirement_match(
                req=req,
                raw_resume=raw_resume,
                experience_text=experience_text,
                projects_text=projects_text,
                skills_text=skills_text,
                candidate_skills=candidate_skills_dict
            )

            if match_item["status"] == "matched":
                matched_reqs.append(match_item)
            elif match_item["status"] == "partial":
                partial_matches.append(match_item)
            else:
                missing_evidence.append(match_item)

        # 2. Evaluate Experience Years Alignment
        min_years_required = parsed_jd.get("min_experience_years", 0)
        exp_score, exp_explanation = cls._evaluate_experience_years(
            raw_resume=raw_resume,
            experience_text=experience_text,
            projects_text=projects_text,
            min_years_required=min_years_required
        )

        # 3. Compute Deterministic Scores
        total_required = sum(1 for r in all_jd_requirements if r.get("importance") == "required")
        total_preferred = sum(1 for r in all_jd_requirements if r.get("importance") == "preferred")

        req_matched_count = sum(1 for r in matched_reqs if r.get("importance") == "required")
        req_partial_count = sum(1 for r in partial_matches if r.get("importance") == "required")
        
        pref_matched_count = sum(1 for r in matched_reqs if r.get("importance") == "preferred")
        pref_partial_count = sum(1 for r in partial_matches if r.get("importance") == "preferred")

        # Required skills score (matched = 100%, partial = 50%)
        if total_required > 0:
            required_score = int(round(((req_matched_count * 1.0 + req_partial_count * 0.5) / total_required) * 100))
        else:
            required_score = 80  # Default baseline if JD doesn't specify strict hard requirements

        # Preferred skills score
        if total_preferred > 0:
            preferred_score = int(round(((pref_matched_count * 1.0 + pref_partial_count * 0.5) / total_preferred) * 100))
        else:
            preferred_score = 100  # No preferred requirements missing

        # Evidence Strength Score: ratio of matched requirements demonstrated in experience/projects vs bare mentions
        demonstrated_count = sum(1 for r in matched_reqs if r.get("demonstrated_in_project"))
        evidence_strength_score = int(round((demonstrated_count / len(matched_reqs) * 100))) if matched_reqs else 40

        # Composite Overall Score
        overall_match = int(round(
            required_score * cls.WEIGHTS["required_skills"] +
            preferred_score * cls.WEIGHTS["preferred_skills"] +
            exp_score * cls.WEIGHTS["experience_relevance"] +
            evidence_strength_score * cls.WEIGHTS["evidence_strength"]
        ))
        overall_match_score = max(0, min(100, overall_match))

        # Readiness Tier
        if overall_match_score >= 85:
            tier = "Strong Contender"
        elif overall_match_score >= 70:
            tier = "Competitive Match"
        elif overall_match_score >= 50:
            tier = "Moderate Fit (Skill Gaps)"
        else:
            tier = "Significant Alignment Gaps"

        # Evidence Summary
        evidence_summary = (
            f"Evaluated against {len(all_jd_requirements)} extracted position requirements. "
            f"{len(matched_reqs)} qualifications strongly demonstrated in candidate experience, "
            f"{len(partial_matches)} equivalent or partial proficiencies, and "
            f"{len(missing_evidence)} critical requirement gaps."
        )

        # Strategic Application Recommendations
        recommendations: List[str] = []
        if missing_evidence:
            top_missing = [m["name"] for m in missing_evidence[:3]]
            recommendations.append(
                f"High Priority: Highlight or acquire hands-on project exposure with {', '.join(top_missing)} prior to applying."
            )
        if partial_matches:
            top_partial = partial_matches[0]
            recommendations.append(
                f"Emphasize Demonstrated Equivalent: Make your experience with '{top_partial.get('equivalent_found', top_partial['name'])}' prominent to bridge '{top_partial['name']}'."
            )
        if exp_score < 75:
            recommendations.append(
                "Address Seniority Expectation: Expand bullet points in personal or academic projects to demonstrate deep architectural autonomy."
            )
        else:
            recommendations.append(
                "Tailor Resume Summary: Reference key matching keywords in your professional profile header."
            )

        return {
            "overall_match_score": overall_match_score,
            "hard_skill_match_score": required_score,
            "preferred_match_score": preferred_score,
            "experience_match_score": exp_score,
            "evidence_strength_score": evidence_strength_score,
            "readiness_tier": tier,
            "matched_requirements": matched_reqs,
            "partial_matches": partial_matches,
            "missing_evidence": missing_evidence,
            "verified_evidence_summary": evidence_summary,
            "recommendations": recommendations,
            "experience_evaluation": exp_explanation,
            "disclaimer": (
                "CareerLens Job-Match Estimate is a deterministic evidence benchmark comparing "
                "verifiable text and technical equivalences. It is not an official employer ATS score, "
                "a hiring guarantee, or an internal hiring decision."
            )
        }

    @classmethod
    def _evaluate_requirement_match(
        cls,
        req: Dict[str, Any],
        raw_resume: str,
        experience_text: str,
        projects_text: str,
        skills_text: str,
        candidate_skills: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determines whether a requirement is matched, partial, or missing.
        Distinguishes mere keyword mention from demonstrated project/work evidence.
        """
        name = req["name"]
        name_lower = name.lower()
        importance = req.get("importance", "required")

        # 1. Direct match check
        in_experience = bool(experience_text and re.search(rf"\b{re.escape(name_lower)}\b", experience_text.lower()))
        in_projects = bool(projects_text and re.search(rf"\b{re.escape(name_lower)}\b", projects_text.lower()))
        in_skills = bool(skills_text and re.search(rf"\b{re.escape(name_lower)}\b", skills_text.lower()))
        in_raw = bool(re.search(rf"\b{re.escape(name_lower)}\b", raw_resume.lower()))

        # Check candidate verified skills dictionary
        skill_record = candidate_skills.get(name_lower)

        # Demonstrated evidence: found in experience or projects
        if in_experience or in_projects or (skill_record and skill_record.get("source_section") in ["experience", "projects"]):
            loc = "Experience Section" if in_experience else "Projects Section"
            quote = cls._find_evidence_quote(name_lower, experience_text if in_experience else projects_text)
            return {
                "name": name,
                "category": req.get("category", "skills"),
                "importance": importance,
                "status": "matched",
                "demonstrated_in_project": True,
                "evidence_quote": quote or f"Demonstrated in candidate {loc.lower()}.",
                "location": loc,
                "confidence": 95,
                "explanation": f"Explicitly required by JD and demonstrated with hands-on context in {loc}.",
                "recommended_action": "Keep this accomplishment prominent in your resume.",
            }

        # Bare mention: only in skills list or raw text without project context
        if in_skills or in_raw or skill_record:
            return {
                "name": name,
                "category": req.get("category", "skills"),
                "importance": importance,
                "status": "partial",
                "demonstrated_in_project": False,
                "evidence_quote": f"Listed in Skills list: '{name}'",
                "location": "Skills Section",
                "confidence": 70,
                "explanation": f"'{name}' is listed as a skill, but lacks an evidence bullet demonstrating real-world usage in projects or employment.",
                "recommended_action": f"Add a bullet in Projects or Experience showing how you used '{name}'.",
            }

        # 2. Check Equivalence Mapping (e.g. Postgres -> SQL)
        for general_term, equivalents in EQUIVALENCE_MAP.items():
            if name_lower == general_term or name_lower in equivalents:
                # Check if candidate has ANY of the equivalents
                for eq in equivalents:
                    if re.search(rf"\b{re.escape(eq)}\b", raw_resume.lower()):
                        eq_in_exp = bool(experience_text and re.search(rf"\b{re.escape(eq)}\b", experience_text.lower()))
                        loc = "Experience Section" if eq_in_exp else "Document Text"
                        quote = cls._find_evidence_quote(eq, experience_text if eq_in_exp else raw_resume)
                        return {
                            "name": name,
                            "category": req.get("category", "skills"),
                            "importance": importance,
                            "status": "partial",
                            "demonstrated_in_project": eq_in_exp,
                            "equivalent_found": eq.title(),
                            "evidence_quote": quote or f"Candidate demonstrates credible equivalent: {eq.title()}",
                            "location": loc,
                            "confidence": 80,
                            "explanation": f"JD specifies '{name}', and candidate demonstrates direct equivalent '{eq.title()}'.",
                            "recommended_action": f"Explicitly mention '{name}' alongside '{eq.title()}' to ensure exact keyword matching in ATS.",
                        }

        # 3. Missing Evidence
        return {
            "name": name,
            "category": req.get("category", "skills"),
            "importance": importance,
            "status": "missing_evidence",
            "demonstrated_in_project": False,
            "evidence_quote": "No matching text found in uploaded document.",
            "location": "Not detected",
            "confidence": 0,
            "explanation": f"Required competence '{name}' was not detected anywhere in your resume.",
            "recommended_action": f"Consider acquiring experience or adding verified coursework/projects in '{name}'.",
        }

    @staticmethod
    def _find_evidence_quote(term: str, text: str) -> str:
        for line in text.splitlines():
            if term.lower() in line.lower():
                clean = line.strip().lstrip("-*• ")
                return clean[:120] if len(clean) > 120 else clean
        return ""

    @staticmethod
    def _evaluate_experience_years(
        raw_resume: str,
        experience_text: str,
        projects_text: str,
        min_years_required: int
    ) -> Tuple[int, str]:
        """
        Estimates seniority match based on required years vs candidate history.
        """
        if min_years_required <= 0:
            return 100, "Position is entry-level / no strict years requirement specified."

        # Count date ranges or years mentioned in resume
        years_found = len(re.findall(r"\b(20\d\d)\b", raw_resume))
        # Approximate experience span
        has_projects = len(projects_text.split()) > 40
        has_exp = len(experience_text.split()) > 40

        if min_years_required <= 2:
            if has_exp or has_projects:
                return 90, f"Candidate qualifications align well with {min_years_required}-year entry/junior expectation."
            return 65, f"Requires {min_years_required} years; candidate should expand project details."

        if min_years_required <= 4:
            if has_exp and years_found >= 3:
                return 85, f"Candidate demonstrates relevant tenure meeting the {min_years_required}-year requirement."
            return 60, f"Position requires {min_years_required}+ years of professional experience."

        # Senior (5+ years)
        return 50, f"Role requires {min_years_required}+ years. Seniority qualifications may require additional leadership evidence."

job_matcher = JobMatchingEngine()
