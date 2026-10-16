import re
from typing import Dict, List, Any, Optional

STRONG_ACTION_VERBS = {
    "architected", "engineered", "developed", "implemented", "designed", "optimized",
    "spearheaded", "built", "authored", "overhauled", "accelerated", "constructed",
    "configured", "automated", "streamlined", "orchestrated", "refactored", "integrated",
    "deployed", "pioneered", "established", "executed", "scaled", "standardized",
    "analyzed", "benchmarked", "migrated", "resolved", "maintained", "mentored",
    "created", "programmed", "formulated", "led", "directed", "transformed"
}

WEAK_OPENERS = [
    (re.compile(r"^(responsible\s+for\s+(the\s+)?(development\s+of|developing|creating|building))\b", re.IGNORECASE), "Developed"),
    (re.compile(r"^(responsible\s+for)\b", re.IGNORECASE), "Engineered"),
    (re.compile(r"^(helped\s+(with|to|in)?)\b", re.IGNORECASE), "Collaborated on"),
    (re.compile(r"^(worked\s+on\s+(the\s+)?)\b", re.IGNORECASE), "Designed and implemented"),
    (re.compile(r"^(assisted\s+(with|in)?)\b", re.IGNORECASE), "Contributed to"),
    (re.compile(r"^(tasked\s+with)\b", re.IGNORECASE), "Implemented"),
    (re.compile(r"^(participated\s+in)\b", re.IGNORECASE), "Contributed to"),
    (re.compile(r"^(handled\s+(the\s+)?)\b", re.IGNORECASE), "Administered and maintained"),
    (re.compile(r"^(was\s+in\s+charge\s+of)\b", re.IGNORECASE), "Directed and managed"),
]

VAGUE_TERMS = re.compile(r"\b(various|stuff|things|lots?\s+of|etc|good|some|many\s+tasks|all\s+sorts)\b", re.IGNORECASE)
METRIC_REGEX = re.compile(r"\b(\d+([.,]\d+)?(%|x|\+|k|m|ms|s|gb|tb|mb|hours?|days?|users?|requests?|req/s|\$)?)\b", re.IGNORECASE)

class BulletPointAnalyzer:
    @classmethod
    def analyze_bullets_in_sections(
        cls,
        sections: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Extracts and analyzes bullet points across experience, projects, and work history.
        Returns a list of detailed evaluations and honest suggested rewrites.
        """
        target_sections = ["experience", "projects", "achievements", "extracurricular"]
        evaluations: List[Dict[str, Any]] = []

        for sec_name in target_sections:
            if sec_name in sections:
                raw_section_text = sections[sec_name]
                bullets = cls._extract_bullets(raw_section_text)
                for bullet in bullets:
                    analysis = cls.analyze_single_bullet(bullet, source_section=sec_name)
                    if analysis:
                        evaluations.append(analysis)

        return evaluations

    @classmethod
    def analyze_single_bullet(cls, bullet_text: str, source_section: str = "experience") -> Optional[Dict[str, Any]]:
        clean_bullet = bullet_text.strip().lstrip("-*• ").strip()
        if not clean_bullet or len(clean_bullet) < 8:
            return None

        words = clean_bullet.split()
        word_count = len(words)
        first_word = words[0].rstrip(":,.-").lower()

        issues: List[str] = []
        is_weak_opener = False
        suggested_action_verb = ""
        has_metric = bool(METRIC_REGEX.search(clean_bullet))
        has_vague_terms = bool(VAGUE_TERMS.search(clean_bullet))

        # 1. Check for weak opener phrase
        for pat, replacement in WEAK_OPENERS:
            if pat.search(clean_bullet):
                is_weak_opener = True
                suggested_action_verb = replacement
                issues.append(f"Opens with passive phrase '{pat.pattern.split('^(')[1].split(')')[0]}'. Replace with active technical verb '{replacement}'.")
                break

        # 2. Check if first word is a strong past-tense action verb
        if not is_weak_opener and first_word not in STRONG_ACTION_VERBS:
            issues.append(f"Bullet does not begin with an impactful action verb (starts with '{words[0]}').")

        # 3. Check for measurable metrics / outcomes
        if not has_metric:
            issues.append("Missing quantifiable outcome or metric (e.g. latency, throughput, users, or efficiency improvement).")

        # 4. Check for length
        if word_count < 8:
            issues.append(f"Too brief ({word_count} words). Lacks technical context or methodology.")
        elif word_count > 38:
            issues.append(f"Sentence is long ({word_count} words). Consider splitting into concise, focused statements.")

        # 5. Check for vague filler terminology
        if has_vague_terms:
            vague_match = VAGUE_TERMS.search(clean_bullet)
            issues.append(f"Contains non-specific language: '{vague_match.group(0)}'. State specific technologies or artifacts.")

        # 6. Generate honest suggested rewrite without fabricating numbers
        suggested_rewrite = cls._generate_honest_rewrite(
            clean_bullet,
            is_weak_opener=is_weak_opener,
            suggested_verb=suggested_action_verb,
            has_metric=has_metric,
            has_vague_terms=has_vague_terms
        )

        # Quality scoring for this bullet (0 - 100)
        bullet_score = 100
        if is_weak_opener:
            bullet_score -= 30
        elif first_word not in STRONG_ACTION_VERBS:
            bullet_score -= 20

        if not has_metric:
            bullet_score -= 25
        if word_count < 8 or word_count > 38:
            bullet_score -= 15
        if has_vague_terms:
            bullet_score -= 15

        bullet_score = max(0, min(100, bullet_score))

        return {
            "original_snippet": clean_bullet,
            "section": source_section,
            "word_count": word_count,
            "score": bullet_score,
            "has_metric": has_metric,
            "has_strong_verb": (first_word in STRONG_ACTION_VERBS) and not is_weak_opener,
            "issues": issues,
            "suggested_rewrite": suggested_rewrite,
            "severity": "improvement" if bullet_score >= 60 else "error"
        }

    @classmethod
    def _generate_honest_rewrite(
        cls,
        original: str,
        is_weak_opener: bool,
        suggested_verb: str,
        has_metric: bool,
        has_vague_terms: bool
    ) -> str:
        """
        Produces an ATS-optimized rewrite.
        CRITICAL: Never hallucinates fake percentages or metrics!
        Uses explicit placeholder brackets [Insert real metric, e.g. 25% or 500+ users].
        """
        rewritten = original

        # Replace weak openers
        if is_weak_opener and suggested_verb:
            for pat, _ in WEAK_OPENERS:
                rewritten = pat.sub(suggested_verb, rewritten, count=1)

        # Clean vague words
        if has_vague_terms:
            rewritten = VAGUE_TERMS.sub("[Specified Technical Components]", rewritten)

        # Append metric prompt if none present
        if not has_metric:
            # Ensure it ends with punctuation
            trimmed = rewritten.rstrip(".,;")
            rewritten = f"{trimmed}, achieving [Insert real measured outcome, e.g. % efficiency gain or number of users served]."
        else:
            if not rewritten.endswith("."):
                rewritten = rewritten + "."

        return rewritten

    @staticmethod
    def _extract_bullets(section_text: str) -> List[str]:
        """
        Extracts bullet lines or distinct sentences from a section.
        """
        lines = section_text.splitlines()
        bullets: List[str] = []

        for line in lines:
            stripped = line.strip()
            # Match lines starting with bullet symbols or alphanumeric lists
            if re.match(r"^([•\-\*\+]|\d+[\.\)])\s+", stripped):
                clean = re.sub(r"^([•\-\*\+]|\d+[\.\)])\s+", "", stripped)
                if len(clean) > 8:
                    bullets.append(clean)
            elif len(stripped) > 20 and not stripped.isupper():
                # Treat substantial non-header lines as standalone bullet candidates
                bullets.append(stripped)

        return bullets

bullet_analyzer = BulletPointAnalyzer()
