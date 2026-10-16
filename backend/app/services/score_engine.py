from typing import Dict, List, Any, Optional

class DeterministicScoreEngine:
    # Prototype weight distribution (documented & transparent)
    DEFAULT_WEIGHTS = {
        "structure": 0.25,
        "content_quality": 0.30,
        "skill_evidence": 0.25,
        "ats_readability": 0.20,
    }

    @classmethod
    def calculate_scores(
        cls,
        structure_info: Dict[str, Any],
        bullet_evaluations: List[Dict[str, Any]],
        extracted_skills: Dict[str, List[Dict[str, Any]]],
        ats_info: Dict[str, Any],
        style_info: Dict[str, Any],
        has_job_description: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates deterministic component scores and overall readiness estimate.
        """
        # 1. Structure Score
        structure_score = structure_info.get("structure_score", 70)

        # 2. Content Quality Score
        if bullet_evaluations:
            avg_bullet_score = sum(b.get("score", 70) for b in bullet_evaluations) / len(bullet_evaluations)
        else:
            avg_bullet_score = 65  # Baseline if no bullets extracted

        style_score = style_info.get("style_score", 85)
        # Content quality combines bullet impact (70%) and grammar/style (30%)
        content_quality_score = int(round(avg_bullet_score * 0.70 + style_score * 0.30))

        # 3. Skill Evidence Score
        # Count unique skills across core technical categories
        total_skills = sum(len(skills) for skills in extracted_skills.values())
        langs_count = len(extracted_skills.get("languages", []))
        frameworks_count = len(extracted_skills.get("frameworks", []))
        tools_count = len(extracted_skills.get("developer_tools", []))
        dbs_count = len(extracted_skills.get("databases", []))

        skill_score = 40  # Baseline
        if langs_count >= 1:
            skill_score += 15
        if langs_count >= 3:
            skill_score += 10
        if frameworks_count >= 2:
            skill_score += 15
        if tools_count >= 2:
            skill_score += 10
        if dbs_count >= 1:
            skill_score += 10

        skill_evidence_score = min(100, skill_score)

        # 4. ATS Readability Score
        ats_readability_score = ats_info.get("ats_readability_score", 80)

        # 5. Composite Weighted Calculation
        weights = cls.DEFAULT_WEIGHTS
        overall = int(round(
            structure_score * weights["structure"] +
            content_quality_score * weights["content_quality"] +
            skill_evidence_score * weights["skill_evidence"] +
            ats_readability_score * weights["ats_readability"]
        ))
        overall_score = max(0, min(100, overall))

        # Determine Tier
        if overall_score >= 85:
            tier = "Ready for Market"
        elif overall_score >= 70:
            tier = "Nearly Ready"
        elif overall_score >= 50:
            tier = "Needs Improvement"
        else:
            tier = "Critical Gaps"

        # Construct rationale explanations
        rationale: List[str] = []
        if structure_score >= 80:
            rationale.append("Resume contains all critical sections (contact details, education, technical skills).")
        else:
            rationale.append("Some standard sections or contact credentials require completion.")

        if content_quality_score >= 75:
            rationale.append("Action verbs and descriptive statements exhibit strong engineering ownership.")
        else:
            rationale.append("Bullet points could be strengthened by replacing passive verbs with active outcomes.")

        rationale.append(f"Identified {total_skills} verified technical competencies across {len(extracted_skills)} domain categories.")

        if ats_readability_score >= 85:
            rationale.append("Extracted text demonstrates clean typography, standard vocabulary, and parseable formatting.")

        return {
            "overall_score": overall_score,
            "readiness_tier": tier,
            "component_scores": {
                "structure": structure_score,
                "content_quality": content_quality_score,
                "skill_evidence": skill_evidence_score,
                "ats_readability": ats_readability_score,
            },
            "scoring_weights": weights,
            "scoring_rationale": rationale,
        }

score_engine = DeterministicScoreEngine()
