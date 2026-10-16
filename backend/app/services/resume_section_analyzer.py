import re
from typing import Dict, List, Any

# Expected canonical sections and their necessity levels
SECTION_IMPORTANCE = {
    "contact_info": {
        "level": "critical",
        "description": "Essential contact details (email, phone, location, LinkedIn/GitHub links).",
        "entry_level_required": True,
    },
    "education": {
        "level": "critical",
        "description": "Academic background, university, degree, and graduation year.",
        "entry_level_required": True,
    },
    "skills": {
        "level": "critical",
        "description": "Technical proficiencies, programming languages, and developer tools.",
        "entry_level_required": True,
    },
    "projects": {
        "level": "high",
        "description": "Software or technical projects demonstrating applied engineering skills.",
        "entry_level_required": True,
    },
    "experience": {
        "level": "high",
        "description": "Professional employment, internships, or relevant work history.",
        "entry_level_required": False,  # Optional for entry-level if projects exist!
    },
    "summary": {
        "level": "recommended",
        "description": "A concise 2-3 sentence overview highlighting career objective and core strengths.",
        "entry_level_required": False,
    },
    "certifications": {
        "level": "optional",
        "description": "Industry certifications (AWS, Azure, etc.) or specialized training.",
        "entry_level_required": False,
    },
    "achievements": {
        "level": "optional",
        "description": "Honors, hackathon wins, scholarships, or notable recognitions.",
        "entry_level_required": False,
    },
}

class ResumeSectionAnalyzer:
    @classmethod
    def analyze_sections(cls, raw_text: str, sections: Dict[str, str]) -> Dict[str, Any]:
        """
        Evaluates resume sections, entry-level adaptations, and structural ordering.
        """
        detected_keys = [k for k in sections.keys() if k != "header"]
        
        has_contact = "contact_info" in sections
        has_education = "education" in sections
        has_skills = "skills" in sections
        has_experience = "experience" in sections
        has_projects = "projects" in sections
        has_summary = "summary" in sections

        # Determine if this is an entry-level candidate (has projects/education, but no experience)
        is_entry_level = not has_experience and (has_projects or has_education)

        missing_sections: List[Dict[str, str]] = []
        recommendations: List[str] = []

        # Analyze each standard section
        for sec_key, meta in SECTION_IMPORTANCE.items():
            if sec_key not in sections:
                if is_entry_level and sec_key == "experience":
                    # Explain it's recommended rather than an error
                    missing_sections.append({
                        "section": sec_key,
                        "importance": "recommended",
                        "message": (
                            "No formal work experience section detected. As an entry-level candidate or student, "
                            "in-depth technical projects, open-source contributions, or academic lab work effectively compensate."
                        )
                    })
                elif meta["level"] == "critical":
                    missing_sections.append({
                        "section": sec_key,
                        "importance": "critical",
                        "message": f"Missing critical section: '{sec_key.replace('_', ' ').title()}'. {meta['description']}"
                    })
                    recommendations.append(f"Add a dedicated '{sec_key.replace('_', ' ').title()}' section to pass standard ATS screening.")
                elif meta["level"] == "high":
                    missing_sections.append({
                        "section": sec_key,
                        "importance": "recommended",
                        "message": f"Recommended section missing: '{sec_key.replace('_', ' ').title()}'. {meta['description']}"
                    })
                elif meta["level"] == "recommended":
                    missing_sections.append({
                        "section": sec_key,
                        "importance": "optional",
                        "message": f"Consider adding a '{sec_key.replace('_', ' ').title()}' section to summarize key qualifications."
                    })

        # Contact info completeness check
        contact_issues: List[str] = []
        if has_contact:
            contact_text = sections["contact_info"]
            if not re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", contact_text):
                contact_issues.append("Missing or unparseable email address in contact information.")
            if not re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", contact_text):
                contact_issues.append("No standard phone number detected in contact header.")
        else:
            contact_issues.append("No dedicated contact header detected.")

        # Section Order Evaluation
        section_order_status, order_message = cls._evaluate_section_order(raw_text, detected_keys)

        # Completeness calculation
        total_possible = 100
        score = 100
        if not has_contact:
            score -= 25
        if not has_education:
            score -= 20
        if not has_skills:
            score -= 25
        if not has_experience and not has_projects:
            score -= 25
        elif not has_experience and is_entry_level:
            # Minor deduction if entry level with projects
            score -= 5
        elif not has_projects and has_experience:
            score -= 5

        if contact_issues:
            score -= 5 * len(contact_issues)

        score = max(0, min(100, score))

        return {
            "detected_sections": detected_keys,
            "missing_sections": missing_sections,
            "is_entry_level": is_entry_level,
            "contact_issues": contact_issues,
            "section_order_status": section_order_status,
            "section_order_message": order_message,
            "structure_score": score,
            "recommendations": recommendations,
        }

    @staticmethod
    def _evaluate_section_order(raw_text: str, detected_keys: List[str]) -> (str, str):
        """
        Verifies logical ordering of resume sections.
        Expected standard: Contact/Header -> Summary -> Education/Experience -> Skills/Projects.
        """
        if not detected_keys:
            return "unknown", "Insufficient text to determine section ordering."

        # Find first occurrences in text
        positions = {}
        for key in detected_keys:
            pos = raw_text.lower().find(key.replace("_", " "))
            if pos != -1:
                positions[key] = pos

        sorted_keys = sorted(positions.keys(), key=lambda k: positions[k])

        # If skills or experience appear before contact info
        if "contact_info" in sorted_keys and sorted_keys[0] != "contact_info":
            return "unusual", "Contact information appears after other body sections. ATS parsers expect contact details at the very top."

        return "optimal", "Section sequence follows conventional professional ATS hierarchy."

section_analyzer = ResumeSectionAnalyzer()
