import re
from typing import Dict, List, Any, Optional
from app.services.skill_extractor import skill_extractor, SKILL_TAXONOMY

PREFERRED_PATTERNS = re.compile(
    r"\b(preferred\s+(qualifications|skills|requirements)|nice\s+to\s+have|bonus|pluses|desired\s+qualifications|good\s+to\s+have)\b",
    re.IGNORECASE
)

REQUIRED_PATTERNS = re.compile(
    r"\b(minimum\s+(qualifications|requirements)|basic\s+qualifications|required\s+(skills|qualifications|experience)|what\s+you(?:'ll)?\s+need|must\s+have|requirements)\b",
    re.IGNORECASE
)

RESPONSIBILITIES_PATTERNS = re.compile(
    r"\b(responsibilities|what\s+you(?:'ll)?\s+do|key\s+duties|role\s+responsibilities|day\s+to\s+day)\b",
    re.IGNORECASE
)

EXPERIENCE_YEARS_REGEX = re.compile(
    r"\b(\d+)\+?\s*(?:-|to)?\s*(\d+)?\s*(?:years?|yrs?)\b(?:\s+of)?(?:\s+(?:relevant|hands-on|professional|work)?\s+experience)?",
    re.IGNORECASE
)

EDUCATION_REGEX = re.compile(
    r"\b(bachelor(?:'s)?|master(?:'s)?|phd|doctorate|b\.?s\.?|m\.?s\.?|degree)\b(?:\s+(?:in|of)\s+([a-zA-Z\s]+))?",
    re.IGNORECASE
)

class JobDescriptionParser:
    @classmethod
    def parse_job_description(cls, text: str) -> Dict[str, Any]:
        """
        Extracts required vs preferred skills, experience limits, education, and responsibilities.
        """
        clean_text = text.strip()
        lines = clean_text.splitlines()

        # 1. Segment JD into sections (default, required, preferred, responsibilities)
        current_section = "general"
        sections: Dict[str, List[str]] = {
            "general": [],
            "required": [],
            "preferred": [],
            "responsibilities": []
        }

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Check headings
            if PREFERRED_PATTERNS.search(stripped):
                current_section = "preferred"
                continue
            elif REQUIRED_PATTERNS.search(stripped):
                current_section = "required"
                continue
            elif RESPONSIBILITIES_PATTERNS.search(stripped):
                current_section = "responsibilities"
                continue

            sections[current_section].append(stripped)

        # Recombine section text
        req_text = "\n".join(sections["required"])
        pref_text = "\n".join(sections["preferred"])
        resp_text = "\n".join(sections["responsibilities"])
        general_text = "\n".join(sections["general"])

        # 2. Extract technical skills
        # Look in full text, but classify importance based on where it appears
        all_skills = skill_extractor.extract_skills(clean_text)

        required_skills: List[Dict[str, Any]] = []
        preferred_skills: List[Dict[str, Any]] = []

        pref_lower = pref_text.lower()
        req_lower = req_text.lower()

        for category, skill_list in all_skills.items():
            for s in skill_list:
                s_name = s["name"].lower()
                is_preferred = bool(pref_lower and s_name in pref_lower)
                
                skill_entry = {
                    "name": s["name"],
                    "category": category,
                    "importance": "preferred" if is_preferred else "required",
                    "evidence_snippet": s["evidence_snippet"],
                    "occurrences": s["occurrences"],
                }

                if is_preferred:
                    preferred_skills.append(skill_entry)
                else:
                    required_skills.append(skill_entry)

        # 3. Extract experience requirements
        min_years = 0
        exp_match = EXPERIENCE_YEARS_REGEX.search(clean_text)
        exp_snippet = ""
        if exp_match:
            try:
                min_years = int(exp_match.group(1))
                exp_snippet = exp_match.group(0)
            except (ValueError, TypeError):
                min_years = 0

        # 4. Extract education criteria
        education_criteria = []
        for match in EDUCATION_REGEX.finditer(clean_text):
            education_criteria.append(match.group(0).strip())

        # 5. Extract responsibilities bullets
        responsibilities_bullets = []
        for line in sections["responsibilities"]:
            if len(line) > 15:
                responsibilities_bullets.append(line.lstrip("-*• "))

        return {
            "has_preferred_section": len(sections["preferred"]) > 0,
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "min_experience_years": min_years,
            "experience_snippet": exp_snippet or ("Entry-level / not explicitly specified" if min_years == 0 else f"{min_years}+ years"),
            "education_criteria": list(set(education_criteria)),
            "responsibilities": responsibilities_bullets[:8],
            "raw_text": clean_text,
            "total_words": len(clean_text.split()),
        }

jd_parser = JobDescriptionParser()
