import re
from typing import Dict, List, Any, Optional, Set
from collections import Counter

STOP_WORDS = {
    "and", "the", "with", "for", "that", "this", "from", "have", "been", "will",
    "your", "into", "over", "after", "about", "other", "their", "which", "there",
    "work", "using", "used", "team", "year", "years", "across"
}

class ATSCheckerService:
    @classmethod
    def evaluate_ats_readability(
        cls,
        raw_text: str,
        sections: Dict[str, str],
        job_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluates machine readability, formatting flags, keyword density, and optional JD alignment.
        """
        issues: List[Dict[str, Any]] = []
        warnings: List[str] = []

        total_chars = len(raw_text)
        words = re.findall(r"\b[a-zA-Z]{3,}\b", raw_text.lower())
        total_words = len(words)

        # 1. Extraction text density check
        if total_words < 80:
            warnings.append("Document text is unusually sparse (< 80 words). Risk of extraction dropout or scanned image.")
            issues.append({
                "type": "error",
                "category": "ats_readability",
                "title": "Low Extracted Text Volume",
                "location": "Full Document",
                "explanation": "ATS parsers require dense textual content to index skills and qualifications.",
                "original_snippet": f"Extracted only {total_words} words.",
                "proposed_correction": "Ensure resume is exported directly from Word or Google Docs without flattened image graphics.",
            })

        # 2. Check for abnormal control characters or encoding corruption
        non_ascii_symbols = re.findall(r"[^\x00-\x7F\u2022\u2013\u2014\u2019\u201C\u201D]", raw_text)
        if len(non_ascii_symbols) > 15:
            warnings.append("Detected non-standard unicode characters or font encoding artifacts.")
            issues.append({
                "type": "improvement",
                "category": "ats_readability",
                "title": "Special Font Encoding Artifacts",
                "location": "Document text",
                "explanation": "Special graphic bullets, ligatures, or uncommon fonts may produce unreadable symbols in legacy ATS parsers.",
                "original_snippet": f"{len(non_ascii_symbols)} non-standard glyphs detected",
                "proposed_correction": "Use standard vector web fonts (Arial, Calibri, Helvetica, Times New Roman) and standard bullet points.",
            })

        # 3. Excessive repeated keyword / keyword stuffing check
        word_counts = Counter(words)
        stuffed_words: List[Tuple[str, int, float]] = []
        for word, count in word_counts.most_common(10):
            if word not in STOP_WORDS and count >= 5:
                freq = count / total_words if total_words > 0 else 0
                if freq > 0.045:  # Over 4.5% frequency of entire document
                    stuffed_words.append((word, count, freq))

        if stuffed_words:
            for w, cnt, fr in stuffed_words:
                issues.append({
                    "type": "improvement",
                    "category": "ats_readability",
                    "title": f"Excessive Keyword Repetition ('{w}')",
                    "location": "Full Document",
                    "explanation": f"The term '{w}' appears {cnt} times ({fr*100:.1f}% of total words). ATS spam filters may flag repeated keyword stuffing.",
                    "original_snippet": f"'{w}' repeated {cnt} times",
                    "proposed_correction": f"Vary vocabulary using technical synonyms and diverse action verbs rather than repeating '{w}'.",
                })

        # 4. Multi-column or complex layout detection
        # Check for heavy pipe '|' usage or tab character density
        pipe_count = raw_text.count("|")
        if pipe_count > 12:
            warnings.append("High volume of table / pipe separators detected. Ensure multi-column layout does not scramble reading order.")

        # 5. Optional Job Description Keyword Alignment
        jd_match_info = None
        if job_description and job_description.strip():
            jd_match_info = cls._compare_with_job_description(raw_text, job_description)
            if jd_match_info["missing_keywords"]:
                for kw in jd_match_info["missing_keywords"][:5]:
                    issues.append({
                        "type": "keyword",
                        "category": "job_alignment",
                        "title": f"Missing Job Keyword: '{kw}'",
                        "location": "Target JD Alignment",
                        "explanation": f"The supplied job description emphasizes '{kw}', but it was not detected in your resume text.",
                        "original_snippet": f"JD requirement: {kw}",
                        "proposed_correction": f"If you possess experience with '{kw}', incorporate it explicitly in your Skills or Experience section.",
                    })
        else:
            # JD skipped gracefully
            pass

        # Calculate ATS readability score (0 - 100)
        ats_score = 100
        if total_words < 80:
            ats_score -= 40
        elif total_words < 150:
            ats_score -= 15

        if len(non_ascii_symbols) > 15:
            ats_score -= 15

        if stuffed_words:
            ats_score -= 10 * len(stuffed_words)

        ats_score = max(0, min(100, ats_score))

        return {
            "ats_readability_score": ats_score,
            "issues": issues,
            "warnings": warnings,
            "total_words": total_words,
            "has_jd_comparison": bool(job_description),
            "jd_match_info": jd_match_info,
            "disclaimer": (
                "CareerLens analyzes extracted vector text structure and machine readability. "
                "Because raw text cannot reveal visual layout quirks (e.g. two-column PDF text scrambling), "
                "this deterministic score serves as an employability readiness diagnostic, "
                "not an official proprietary employer ATS decision."
            )
        }

    @staticmethod
    def _compare_with_job_description(resume_text: str, jd_text: str) -> Dict[str, Any]:
        """
        Extracts technical keywords from JD and checks presence in resume.
        """
        # Look for capitalized technical words or common programming buzzwords in JD
        jd_words = re.findall(r"\b[A-Z][a-zA-Z0-9\+\#\.\-]{2,}\b|\b(python|react|docker|sql|aws|ci/cd|kubernetes|typescript|api)\b", jd_text, re.IGNORECASE)
        common_candidates = [w.lower() for w in jd_words if len(w) > 2 and w.lower() not in STOP_WORDS]
        counts = Counter(common_candidates)

        top_jd_keywords = [w for w, _ in counts.most_common(15)]
        resume_lower = resume_text.lower()

        matched = [w for w in top_jd_keywords if w in resume_lower]
        missing = [w for w in top_jd_keywords if w not in resume_lower]

        match_rate = int((len(matched) / len(top_jd_keywords) * 100)) if top_jd_keywords else 100

        return {
            "top_jd_keywords": top_jd_keywords,
            "matched_keywords": matched,
            "missing_keywords": missing,
            "match_rate": match_rate,
        }

ats_checker = ATSCheckerService()
