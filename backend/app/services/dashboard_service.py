from typing import Optional
from app.schemas.dashboard import DashboardResponse, ScoreMetric, RecentReportSummary

class DashboardService:
    @staticmethod
    def get_demonstration_dashboard() -> DashboardResponse:
        """
        Returns a clearly labelled demonstration dashboard response
        reflecting the baseline candidate profile for Alex Rivera.
        """
        return DashboardResponse(
            is_demo=True,
            demo_notice="Demonstration mode: baseline telemetry for candidate Alex Rivera. Real data parsing will connect in Phase 3.",
            candidate_name="Alex Rivera",
            target_career="Full Stack / Backend Software Engineer",
            overall_readiness_score=78,
            readiness_tier="Nearly Ready",
            metrics={
                "ats_compatibility": ScoreMetric(
                    value=84,
                    label="ATS Compatibility",
                    status="Optimal Structure",
                    description="Headers, bullet lengths, and font hierarchy follow ATS guidelines."
                ),
                "skill_alignment": ScoreMetric(
                    value=72,
                    label="Skill Alignment",
                    status="2 Gaps Identified",
                    description="Strong Python & React; missing Kubernetes and Kafka."
                ),
                "experience_impact": ScoreMetric(
                    value=76,
                    label="Experience Impact",
                    status="Quantified",
                    description="6 of 7 experience bullets include quantifiable business metrics."
                ),
                "presentation": ScoreMetric(
                    value=88,
                    label="Presentation & Tone",
                    status="Executive",
                    description="Professional vocabulary with high action-verb diversity."
                ),
            },
            active_resume_summary={
                "file_name": "Alex_Rivera_Software_Eng_v2.pdf",
                "word_count": 415,
                "sections_detected": 6,
                "sections_total": 6,
                "total_findings": 5,
                "errors": 1,
                "recommendations": 4,
            },
            skill_coverage=[
                {"skill": "Frontend & React Ecosystem", "percentage": 95, "status": "Verified"},
                {"skill": "Backend & API Engineering (FastAPI)", "percentage": 90, "status": "Verified"},
                {"skill": "Databases & Storage (PostgreSQL, Redis)", "percentage": 85, "status": "Verified"},
                {"skill": "Cloud & Container Orchestration (Docker, K8s)", "percentage": 45, "status": "Partial Gap"},
                {"skill": "Distributed Event Streaming (Kafka)", "percentage": 20, "status": "Critical Gap"},
            ],
            recent_reports=[
                RecentReportSummary(
                    id="rep-101",
                    date="Oct 14, 2026",
                    target_role="Full Stack Software Engineer",
                    overall_score=78
                ),
                RecentReportSummary(
                    id="rep-102",
                    date="Oct 02, 2026",
                    target_role="Junior Backend Developer",
                    overall_score=69
                ),
                RecentReportSummary(
                    id="rep-103",
                    date="Sep 21, 2026",
                    target_role="Frontend React Developer",
                    overall_score=63
                ),
            ]
        )

    @staticmethod
    def get_user_dashboard(user_id: str, user_email: Optional[str] = None) -> DashboardResponse:
        from app.services.report_service import report_store
        
        display_name = user_email.split("@")[0].capitalize() if user_email else "Candidate"
        
        # Check if user has real saved reports
        user_reports, total = report_store.list_reports(user_id=user_id, page=1, page_size=5)
        
        if not user_reports:
            # Clean initial onboarding state
            return DashboardResponse(
                is_demo=False,
                demo_notice="",
                candidate_name=display_name,
                target_career="Not Specified (Upload resume to detect)",
                overall_readiness_score=0,
                readiness_tier="Not Evaluated",
                metrics={
                    "ats_compatibility": ScoreMetric(
                        value=0,
                        label="ATS Compatibility",
                        status="Not Evaluated",
                        description="Upload your resume to calculate machine-readability and layout scores."
                    ),
                    "skill_alignment": ScoreMetric(
                        value=0,
                        label="Skill Alignment",
                        status="Not Evaluated",
                        description="Match against a job description to assess technical skill alignment."
                    ),
                    "experience_impact": ScoreMetric(
                        value=0,
                        label="Experience Impact",
                        status="Not Evaluated",
                        description="Quantify your bullet points with measurable outcomes."
                    ),
                    "presentation": ScoreMetric(
                        value=0,
                        label="Presentation & Tone",
                        status="Not Evaluated",
                        description="Analyze action verbs, active voice, and formatting."
                    ),
                },
                active_resume_summary={
                    "file_name": "No active resume",
                    "word_count": 0,
                    "sections_detected": 0,
                    "sections_total": 0,
                    "total_findings": 0,
                    "errors": 0,
                    "recommendations": 0,
                },
                skill_coverage=[],
                recent_reports=[]
            )
            
        # User has real saved reports in database!
        latest = user_reports[0]
        recent_summaries = [
            RecentReportSummary(
                id=r["id"],
                date=r.get("date", "Recent"),
                target_role=r.get("target_role", "Software Engineer"),
                overall_score=int(r.get("overall_score", 0))
            )
            for r in user_reports
        ]
        
        comp_scores = latest.get("component_scores", {})
        ats_val = int(comp_scores.get("ats_compatibility", latest.get("ats_score", 0)))
        skill_val = int(comp_scores.get("skill_alignment", latest.get("match_score", 0)))
        exp_val = int(comp_scores.get("experience_impact", 0))
        pres_val = int(comp_scores.get("presentation_tone", 0))
        
        return DashboardResponse(
            is_demo=False,
            demo_notice="",
            candidate_name=display_name,
            target_career=latest.get("target_role", "Software Engineer"),
            overall_readiness_score=int(latest.get("overall_score", 0)),
            readiness_tier=latest.get("readiness_tier", "Evaluated"),
            metrics={
                "ats_compatibility": ScoreMetric(
                    value=ats_val,
                    label="ATS Compatibility",
                    status="Evaluated",
                    description="Computed from your latest uploaded resume."
                ),
                "skill_alignment": ScoreMetric(
                    value=skill_val,
                    label="Skill Alignment",
                    status="Evaluated",
                    description="Calculated based on detected skills."
                ),
                "experience_impact": ScoreMetric(
                    value=exp_val,
                    label="Experience Impact",
                    status="Evaluated",
                    description="Analyzed from bullet points and action verbs."
                ),
                "presentation": ScoreMetric(
                    value=pres_val,
                    label="Presentation & Tone",
                    status="Evaluated",
                    description="Evaluated from tone, formatting, and conciseness."
                ),
            },
            active_resume_summary={
                "file_name": latest.get("resume_name", "Uploaded Resume"),
                "word_count": latest.get("word_count", 0),
                "sections_detected": len(latest.get("detected_sections", [])),
                "sections_total": len(latest.get("detected_sections", [])) + len(latest.get("missing_sections", [])),
                "total_findings": len(latest.get("findings", [])),
                "errors": sum(1 for f in latest.get("findings", []) if f.get("type") == "error"),
                "recommendations": sum(1 for f in latest.get("findings", []) if f.get("type") != "error"),
            },
            skill_coverage=latest.get("extracted_skills_list", []),
            recent_reports=recent_summaries
        )

dashboard_service = DashboardService()
