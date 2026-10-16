"""
Recommendation Service for CareerLens (Phase 8).
Ranks and prioritizes resume and job match improvement opportunities into
actionable, structured high/medium/low priority recommendations.
"""

from typing import List, Dict, Any, Optional
from app.schemas.explanation import PrioritizedRecommendation

class RecommendationService:
    @staticmethod
    def build_resume_recommendations(
        findings: List[Dict[str, Any]],
        overall_score: int,
        skills: List[str]
    ) -> List[PrioritizedRecommendation]:
        """
        Deterministically produces prioritized recommendations sorted by impact.
        High: Critical structural blockers, missing quantified metrics, low skill density.
        Medium: Header standardization, formatting polish, skill categorization.
        Low: Minor wording polish, optional additional sections.
        """
        recommendations: List[PrioritizedRecommendation] = []
        rec_counter = 1

        # Check for critical errors or warnings first
        for finding in findings:
            severity = finding.get("severity", "info").lower()
            finding_id = finding.get("id", f"finding-{rec_counter}")
            title = finding.get("title", "")
            section = finding.get("section", "general")

            if severity == "error" or "metric" in title.lower() or "missing" in title.lower():
                recommendations.append(PrioritizedRecommendation(
                    id=f"rec-{rec_counter}",
                    priority="high",
                    category="experience" if "metric" in title.lower() else "structure",
                    title=f"Resolve {title}",
                    description=finding.get("description", "Address this critical resume finding to clear baseline ATS filters."),
                    linked_finding_id=finding_id,
                    priority_reason="High-severity items directly inhibit ATS parsing and recruiter shortlisting.",
                    effort_estimate="quick_fix" if "format" in title.lower() else "moderate"
                ))
                rec_counter += 1
            elif severity == "warning":
                recommendations.append(PrioritizedRecommendation(
                    id=f"rec-{rec_counter}",
                    priority="medium",
                    category="skills" if "skill" in section else "clarity",
                    title=f"Improve {title}",
                    description=finding.get("description", "Refine this area to improve clarity and recruiter impression."),
                    linked_finding_id=finding_id,
                    priority_reason="Medium-priority refinements improve readability and candidate standing in peer comparisons.",
                    effort_estimate="moderate"
                ))
                rec_counter += 1

        # If few technical skills were extracted
        if len(skills) < 5:
            recommendations.append(PrioritizedRecommendation(
                id=f"rec-{rec_counter}",
                priority="high",
                category="skills",
                title="Expand Technical Skills Inventory",
                description="Your resume has fewer than 5 detected technical skills. Explicitly list core programming languages, frameworks, and developer tools you have used.",
                linked_finding_id=None,
                priority_reason="Keyword density in the skills section is essential for automated candidate retrieval.",
                effort_estimate="quick_fix"
            ))
            rec_counter += 1

        # Fallback if no specific recommendations were generated
        if not recommendations:
            recommendations.append(PrioritizedRecommendation(
                id="rec-1",
                priority="low",
                category="clarity",
                title="Maintain Resume Freshness",
                description="Continue tracking recent coursework, projects, and production contributions in your resume.",
                linked_finding_id=None,
                priority_reason="Continuous updates keep your profile aligned with evolving industry expectations.",
                effort_estimate="quick_fix"
            ))

        # Sort recommendations: high first, then medium, then low
        priority_weights = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: priority_weights.get(r.priority.lower(), 3))
        return recommendations

    @staticmethod
    def build_job_match_recommendations(
        requirements: List[Dict[str, Any]],
        overall_match_score: int
    ) -> List[PrioritizedRecommendation]:
        """
        Produces prioritized recommendations for closing job-description gaps.
        """
        recommendations: List[PrioritizedRecommendation] = []
        rec_counter = 1

        for req in requirements:
            status = req.get("status", "").lower()
            importance = req.get("importance", "").lower()
            name = req.get("name", "Requirement")

            if status in ["missing_evidence", "needs_verification"] and importance == "required":
                recommendations.append(PrioritizedRecommendation(
                    id=f"rec-job-{rec_counter}",
                    priority="high",
                    category="skills",
                    title=f"Address Required Skill Gap: {name}",
                    description=f"This role explicitly requires experience with {name}. Add evidence of projects, coursework, or internships using {name}.",
                    linked_finding_id=None,
                    priority_reason=f"{name} is a required core prerequisite for this position.",
                    effort_estimate="moderate"
                ))
                rec_counter += 1
            elif status in ["partial", "missing_evidence"] and importance == "preferred":
                recommendations.append(PrioritizedRecommendation(
                    id=f"rec-job-{rec_counter}",
                    priority="medium",
                    category="skills",
                    title=f"Showcase Preferred Qualification: {name}",
                    description=f"Demonstrating familiarity with {name} provides a competitive advantage over other applicants.",
                    linked_finding_id=None,
                    priority_reason="Preferred qualifications differentiate top-tier candidates in finalist selection.",
                    effort_estimate="moderate"
                ))
                rec_counter += 1

        if not recommendations:
            recommendations.append(PrioritizedRecommendation(
                id="rec-job-1",
                priority="low",
                category="experience",
                title="Tailor Project Emphases",
                description="Align the phrasing of your project achievements to closely mirror the company's tech stack terminology.",
                linked_finding_id=None,
                priority_reason="Fine-tuning vocabulary improves recruiter rapport and interview alignment.",
                effort_estimate="quick_fix"
            ))

        priority_weights = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: priority_weights.get(r.priority.lower(), 3))
        return recommendations

recommendation_service = RecommendationService()
