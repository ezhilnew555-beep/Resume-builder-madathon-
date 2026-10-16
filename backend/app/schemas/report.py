from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ReportItem(BaseModel):
    id: str
    date: str
    resume_name: str
    target_role: str
    overall_score: int
    ats_score: int
    match_score: int
    issues_count: int = 0
    status: str = "completed"
    report_title: Optional[str] = None


class ReportsListResponse(BaseModel):
    reports: List[ReportItem] = Field(default_factory=list, description="List of stored candidate evaluation reports")
    total: int = Field(default=0, description="Total number of stored reports")
    page: int = Field(default=1, ge=1, description="Current page number")
    page_size: int = Field(default=10, ge=1, description="Items per page")
    message: str = Field(default="Reports retrieved successfully.", description="Status message")


class ReportSaveRequest(BaseModel):
    resume_id: str
    report_title: Optional[str] = None
    target_role: Optional[str] = None
    job_match_id: Optional[str] = None


class DetailedReportResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    report_title: str
    date: str
    resume_name: str
    resume_id: str
    target_role: str
    overall_score: int
    readiness_tier: str
    ats_score: int
    match_score: int
    status: str = "completed"
    component_scores: Dict[str, int] = Field(default_factory=dict)
    scoring_rationale: Any = Field(default_factory=list)
    extracted_skills: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    detected_sections: List[str] = Field(default_factory=list)
    missing_sections: Any = Field(default_factory=list)
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    bullet_evaluations: List[Dict[str, Any]] = Field(default_factory=list)
    job_match_summary: Optional[Dict[str, Any]] = None
    roadmap_summary: Optional[Dict[str, Any]] = None
    disclaimer: str = (
        "Scores and evaluations represent a CareerLens ATS-style estimate designed for educational and optimization "
        "purposes. CareerLens does not claim to reproduce any specific employer's proprietary applicant tracking system."
    )


class ReportComparisonResponse(BaseModel):
    report_a_id: str
    report_b_id: str
    date_a: str
    date_b: str
    title_a: str
    title_b: str
    score_a: int
    score_b: int
    score_delta: int
    is_compatible: bool = True
    compatibility_notice: Optional[str] = None
    category_deltas: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    issues_resolved: List[Dict[str, Any]] = Field(default_factory=list)
    issues_still_present: List[Dict[str, Any]] = Field(default_factory=list)
    issues_newly_identified: List[Dict[str, Any]] = Field(default_factory=list)
    job_match_delta: Optional[Dict[str, Any]] = None
    recommended_next_actions: List[str] = Field(default_factory=list)
    disclaimer: str = (
        "Report comparisons evaluate deterministic metric changes across document iterations. "
        "A higher score indicates better formatting and keyword alignment, but does not guarantee employment or interview invitations."
    )


class ProgressAnalyticsSummaryResponse(BaseModel):
    total_analyses_completed: int = 0
    latest_score: Optional[int] = None
    previous_score: Optional[int] = None
    score_progression: List[Dict[str, Any]] = Field(default_factory=list)
    issues_resolved_total: int = 0
    current_open_issues: int = 0
    roadmap_tasks_completed: int = 0
    roadmap_tasks_total: int = 0
    roadmap_completion_pct: int = 0
    skills_by_evidence_type: Dict[str, int] = Field(
        default_factory=lambda: {"self_reported": 0, "resume_evidence": 0, "independently_verified": 0}
    )
    target_role: Optional[str] = None
    has_historical_data: bool = False
    disclaimer: str = (
        "Analytics combine self-reported learning progress with document-extracted and third-party verified skills. "
        "Completed roadmap tasks reflect self-reported student progress and do not prove third-party verified competence."
    )
