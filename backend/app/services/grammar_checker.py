import re
from typing import Dict, List, Any

# First person pronouns (in professional resumes, bullets should avoid first person)
FIRST_PERSON_PATTERNS = [
    (re.compile(r"\b(I|me|my|mine)\b", re.IGNORECASE), "first-person singular pronoun ('I', 'my')"),
    (re.compile(r"\b(we|us|our|ours)\b", re.IGNORECASE), "first-person plural pronoun ('we', 'our')"),
]

PASSIVE_VOICE_PATTERN = re.compile(
    r"\b(was|were|been|being)\s+(developed|created|implemented|assigned|handled|tasked|asked|managed|chosen)\b",
    re.IGNORECASE
)

FILLER_PHRASES = [
    (re.compile(r"\bin\s+order\s+to\b", re.IGNORECASE), "in order to", "to"),
    (re.compile(r"\bduties\s+included\b", re.IGNORECASE), "duties included", "Spearheaded / Managed"),
    (re.compile(r"\bas\s+well\s+as\b", re.IGNORECASE), "as well as", "and"),
    (re.compile(r"\bfor\s+the\s+purpose\s+of\b", re.IGNORECASE), "for the purpose of", "to"),
]

class GrammarAndStyleChecker:
    @classmethod
    def check_grammar_and_style(cls, raw_text: str, sections: Dict[str, str]) -> Dict[str, Any]:
        """
        Runs deterministic rule-based grammar, style, and tone checks.
        """
        issues: List[Dict[str, Any]] = []
        lines = raw_text.splitlines()

        # 1. First Person Pronouns in Experience or Projects
        target_sections = ["experience", "projects", "summary"]
        for sec_name in target_sections:
            if sec_name in sections:
                sec_text = sections[sec_name]
                for pat, label in FIRST_PERSON_PATTERNS:
                    matches = list(pat.finditer(sec_text))
                    if matches:
                        sample_match = matches[0].group(0)
                        issues.append({
                            "type": "error",
                            "category": "style_grammar",
                            "title": f"First-Person Pronoun in {sec_name.title()}",
                            "location": f"Section: {sec_name.title()}",
                            "explanation": f"Detected {label} ('{sample_match}'). Modern ATS best practices require action-first telegraphic phrasing without pronouns.",
                            "original_snippet": cls._find_snippet_around(matches[0].start(), sec_text),
                            "proposed_correction": f"Remove '{sample_match}' and start the statement directly with a strong active verb.",
                        })

        # 2. Passive Voice Detection
        for sec_name in ["experience", "projects"]:
            if sec_name in sections:
                sec_text = sections[sec_name]
                passive_matches = list(PASSIVE_VOICE_PATTERN.finditer(sec_text))
                for m in passive_matches[:2]:  # Limit to avoid clutter
                    phrase = m.group(0)
                    issues.append({
                        "type": "improvement",
                        "category": "style_grammar",
                        "title": f"Passive Voice in {sec_name.title()}",
                        "location": f"Section: {sec_name.title()}",
                        "explanation": f"Passive construction '{phrase}' diminishes perceived ownership and impact.",
                        "original_snippet": cls._find_snippet_around(m.start(), sec_text),
                        "proposed_correction": f"Rephrase with active ownership: e.g. replace '{phrase}' with an active verb like 'Engineered' or 'Executed'.",
                    })

        # 3. Filler Phrases
        for pat, original_phrase, suggested in FILLER_PHRASES:
            matches = list(pat.finditer(raw_text))
            if matches:
                issues.append({
                    "type": "improvement",
                    "category": "style_grammar",
                    "title": f"Wordy Filler Phrase ('{original_phrase}')",
                    "location": "Body text",
                    "explanation": f"'{original_phrase}' adds unnecessary length without technical value.",
                    "original_snippet": cls._find_snippet_around(matches[0].start(), raw_text),
                    "proposed_correction": f"Replace with concise equivalent '{suggested}'.",
                })

        # 4. Bullet Punctuation Consistency
        punctuation_status, punct_msg = cls._check_bullet_punctuation(sections)
        if punctuation_status == "inconsistent":
            issues.append({
                "type": "improvement",
                "category": "formatting",
                "title": "Inconsistent Bullet Punctuation",
                "location": "Bullet points",
                "explanation": punct_msg,
                "original_snippet": "Mixed terminal punctuation (. vs none)",
                "proposed_correction": "Standardize all bullet points to either consistently end with a period or consistently omit terminal periods.",
            })

        style_score = max(0, 100 - len(issues) * 12)

        return {
            "style_score": style_score,
            "issues": issues,
            "punctuation_status": punctuation_status,
        }

    @staticmethod
    def _find_snippet_around(pos: int, text: str, radius: int = 50) -> str:
        start = max(0, pos - radius)
        end = min(len(text), pos + radius)
        snippet = text[start:end].replace("\n", " ").strip()
        return f"...{snippet}..."

    @staticmethod
    def _check_bullet_punctuation(sections: Dict[str, str]) -> (str, str):
        bullet_endings: List[bool] = []
        for sec in ["experience", "projects"]:
            if sec in sections:
                for line in sections[sec].splitlines():
                    clean = line.strip()
                    if clean.startswith(("-", "*", "•")) or (len(clean) > 20 and not clean.isupper()):
                        bullet_endings.append(clean.endswith("."))

        if not bullet_endings or len(bullet_endings) < 3:
            return "consistent", "Sufficient bullets not available for consistency analysis."

        period_count = sum(1 for e in bullet_endings if e)
        non_period_count = len(bullet_endings) - period_count

        if period_count > 0 and non_period_count > 0:
            if min(period_count, non_period_count) >= 2:
                return "inconsistent", f"Found {period_count} bullets ending with a period and {non_period_count} bullets without a period."

        return "consistent", "Bullet terminal punctuation is uniform."

grammar_checker = GrammarAndStyleChecker()
