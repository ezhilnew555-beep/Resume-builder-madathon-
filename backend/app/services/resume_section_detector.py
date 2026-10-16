import re
from typing import Dict, List, Any, Tuple

# Mapping of canonical section keys to regex patterns for headings
SECTION_PATTERNS: Dict[str, List[re.Pattern]] = {
    "contact_info": [
        re.compile(r"^(contact(\s+information)?|personal\s+(details|info))\b", re.IGNORECASE),
    ],
    "summary": [
        re.compile(r"^(professional\s+summary|summary|profile|about\s+me|career\s+objective|objective|executive\s+summary)\b", re.IGNORECASE),
    ],
    "education": [
        re.compile(r"^(education|academic\s+background|educational\s+qualifications|academics|degrees)\b", re.IGNORECASE),
    ],
    "skills": [
        re.compile(r"^(technical\s+skills|core\s+competencies|skills(\s*(&|and)\s*abilities)?|technologies|technical\s+proficiency|areas\s+of\s+expertise|programming\s+languages)\b", re.IGNORECASE),
    ],
    "experience": [
        re.compile(r"^(work\s+experience|professional\s+experience|experience|employment\s+history|work\s+history|internships?)\b", re.IGNORECASE),
    ],
    "projects": [
        re.compile(r"^(projects|academic\s+projects|key\s+projects|technical\s+projects|personal\s+projects|notable\s+projects)\b", re.IGNORECASE),
    ],
    "certifications": [
        re.compile(r"^(certifications?|licenses?(\s*(&|and)\s*certifications?)?|certificates|credentials)\b", re.IGNORECASE),
    ],
    "achievements": [
        re.compile(r"^(achievements|awards(\s*(&|and)\s*honors)?|honors|accomplishments|publications)\b", re.IGNORECASE),
    ],
    "extracurricular": [
        re.compile(r"^(extracurricular(\s+activities)?|leadership(\s+experience)?|volunteer(\s+experience)?|activities)\b", re.IGNORECASE),
    ],
}

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_REGEX = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")

class ResumeSectionDetector:
    @staticmethod
    def identify_heading(line: str) -> Tuple[bool, str]:
        """
        Tests if a stripped line is likely a resume section header.
        Returns (is_header, canonical_section_key).
        """
        clean = line.strip().rstrip(":-_#")
        if not clean or len(clean) < 3 or len(clean) > 45:
            return False, ""

        # Check against defined section patterns
        for section_key, patterns in SECTION_PATTERNS.items():
            for pat in patterns:
                if pat.search(clean):
                    return True, section_key

        return False, ""

    @classmethod
    def segment_sections(cls, raw_text: str) -> Dict[str, str]:
        """
        Segments raw resume text into detected sections while preserving paragraph structure.
        Only returns sections that were genuinely detected.
        """
        if not raw_text or not raw_text.strip():
            return {}

        lines = raw_text.splitlines()
        detected_sections: Dict[str, List[str]] = {}
        current_section = "header"
        buffer: List[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if buffer and buffer[-1] != "":
                    buffer.append("")
                continue

            is_header, section_key = cls.identify_heading(stripped)
            if is_header:
                # Flush previous section
                if buffer:
                    content = "\n".join(buffer).strip()
                    if content:
                        detected_sections.setdefault(current_section, []).append(content)
                current_section = section_key
                buffer = []
            else:
                buffer.append(line)

        # Flush final section
        if buffer:
            content = "\n".join(buffer).strip()
            if content:
                detected_sections.setdefault(current_section, []).append(content)

        # Process sections dictionary
        result: Dict[str, str] = {}
        for key, text_chunks in detected_sections.items():
            combined = "\n\n".join(text_chunks).strip()
            if key == "header":
                # If header section contains contact indicators (email or phone), canonicalize as contact_info
                if EMAIL_REGEX.search(combined) or PHONE_REGEX.search(combined):
                    result["contact_info"] = combined
                else:
                    # Keep as preamble/header if substantial
                    result["header"] = combined
            else:
                result[key] = combined

        return result

    @classmethod
    def evaluate_extraction_quality(cls, raw_text: str, sections: Dict[str, str]) -> Dict[str, Any]:
        """
        Evaluates extraction quality, calculates words/chars, and flags potential dropouts.
        """
        words = re.findall(r"\b\w+\b", raw_text)
        total_words = len(words)
        total_chars = len(raw_text)

        detected_keys = [k for k in sections.keys() if k != "header"]
        
        # Standard expected core sections
        core_sections = ["education", "skills", "experience"]
        missing_core = [sec for sec in core_sections if sec not in detected_keys]

        # Calculate score (0-100)
        score = 0
        if total_words >= 50:
            score += 25
        if total_words >= 150:
            score += 25
        
        # Section coverage (up to 30 pts)
        core_found = len(core_sections) - len(missing_core)
        score += core_found * 10

        # Structure clarity (up to 20 pts)
        if len(detected_keys) >= 4:
            score += 20
        elif len(detected_keys) >= 2:
            score += 10

        quality_level = "high" if score >= 75 else ("moderate" if score >= 45 else "low")

        return {
            "total_words": total_words,
            "total_characters": total_chars,
            "detected_sections_count": len(detected_keys),
            "detected_sections": detected_keys,
            "missing_core_sections": missing_core,
            "quality_score": min(score, 100),
            "quality_level": quality_level,
            "has_contact_info": "contact_info" in sections or EMAIL_REGEX.search(raw_text) is not None,
        }

section_detector = ResumeSectionDetector()
