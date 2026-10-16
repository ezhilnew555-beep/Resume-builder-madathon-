import re
from typing import Dict, List, Any, Optional
from app.services.skill_extractor import skill_extractor, SKILL_TAXONOMY

PROJECT_HEADER_REGEX = re.compile(
    r"^(?:[-*•]\s*)?([A-Za-z0-9\s\-_]+)(?:\s*[:|–—]\s*|\s*\|\s*|\s*\(([^)]+)\))(.*)$"
)

GITHUB_URL_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+)",
    re.IGNORECASE
)

class EvidenceExtractor:
    @classmethod
    def extract_resume_claims(
        cls,
        resume_record: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extracts verifiable claims (project initiatives, claimed technologies, coding profiles)
        from candidate resume sections and text.
        """
        raw_text = resume_record.get("raw_text", "")
        sections = resume_record.get("sections", {})
        projects_text = sections.get("projects", "")
        experience_text = sections.get("experience", "")

        claims: List[Dict[str, Any]] = []
        seen_project_names = set()

        # 1. Extract Project Claims
        project_source_text = projects_text or experience_text
        if project_source_text:
            lines = [l.strip() for l in project_source_text.splitlines() if l.strip()]
            current_project: Optional[Dict[str, Any]] = None

            for line in lines:
                # Check for project header lines
                # Examples:
                # "- CareerLens: Built an AI-powered resume analyzer with React and FastAPI."
                # "Distributed Cache | Go, Redis, Docker"
                # "E-Commerce Microservices (Python / Django)"
                cleaned_line = line.lstrip("-*• ").strip()
                if len(cleaned_line) < 5:
                    continue

                # Check if line contains a project name
                header_match = PROJECT_HEADER_REGEX.match(line)
                is_bullet = line.startswith(("-", "*", "•"))

                # Try to extract potential project name
                proj_name = ""
                proj_desc = cleaned_line

                if header_match:
                    candidate_name = header_match.group(1).strip()
                    # Filter out generic words like "Experience", "Summary", "Technologies"
                    if candidate_name.lower() not in ["skills", "experience", "education", "summary", "responsibilities"]:
                        proj_name = candidate_name
                        proj_desc = header_match.group(3).strip() or cleaned_line
                elif ":" in cleaned_line and len(cleaned_line.split(":")[0].split()) <= 4:
                    parts = cleaned_line.split(":", 1)
                    proj_name = parts[0].strip()
                    proj_desc = parts[1].strip()

                if proj_name and len(proj_name) >= 3 and len(proj_name) <= 50 and proj_name.lower() not in seen_project_names:
                    seen_project_names.add(proj_name.lower())
                    
                    # Extract technologies in this project
                    techs = cls._extract_technologies_in_text(line + " " + proj_desc)
                    # Check for embedded github link
                    repo_match = GITHUB_URL_REGEX.search(line)
                    embedded_repo = repo_match.group(0) if repo_match else None

                    claims.append({
                        "claim_id": f"proj-{len(claims) + 1}",
                        "claim_type": "project",
                        "project_name": proj_name,
                        "original_claim": f"Project '{proj_name}': {proj_desc[:200]}",
                        "claimed_technologies": techs,
                        "embedded_repo_url": embedded_repo,
                        "source_section": "Projects" if projects_text else "Experience",
                        "raw_snippet": line[:300],
                    })

        # 2. Extract Key Technical Skill Claims
        # Extract skills specifically validated from skill_extractor
        extracted_skills = skill_extractor.extract_skills(raw_text, sections)
        for cat in ["languages", "frameworks", "databases", "developer_tools"]:
            for skill in extracted_skills.get(cat, []):
                # Only make claims for skills with context
                if skill["source_section"] in ["experience", "projects"] or skill["occurrences"] >= 2:
                    claims.append({
                        "claim_id": f"skill-{len(claims) + 1}",
                        "claim_type": "technical_skill",
                        "project_name": None,
                        "original_claim": f"Technical Competency in {skill['name']} ({skill['category']})",
                        "claimed_technologies": [skill["name"]],
                        "embedded_repo_url": None,
                        "source_section": skill["source_section"],
                        "raw_snippet": skill["evidence_snippet"][:300],
                    })

        return claims

    @staticmethod
    def _extract_technologies_in_text(text: str) -> List[str]:
        found: List[str] = []
        text_lower = text.lower()
        for cat, skills in SKILL_TAXONOMY.items():
            for canonical, aliases in skills.items():
                for alias in aliases:
                    if re.search(rf"\b{re.escape(alias.lower())}\b", text_lower):
                        if canonical not in found:
                            found.append(canonical)
                        break
        return found

evidence_extractor = EvidenceExtractor()
