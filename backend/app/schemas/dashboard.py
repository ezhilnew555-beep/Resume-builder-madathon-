from pydantic import BaseModel, Field
from typing import List, Dict, Any

class ScoreMetric(BaseModel):
    value: int = Field(..., ge=0, le=100, description="Score between 0 and 100")
    label: str
    status: str
    description: str

class SkillGapItem(BaseModel):
    name: str
    coverage_percentage: int = Field(..., ge=0, le=100)
    status: str

class RecentReportSummary(BaseModel):
    id: str
    date: str
    target_role: str
    overall_score: int

class DashboardResponse(BaseModel):
    is_demo: bool = Field(default=True, description="Explicit indicator that this is demonstration data")
    demo_notice: str = Field(..., description="Notice explaining demonstration status")
    candidate_name: str
    target_career: str
    overall_readiness_score: int = Field(..., ge=0, le=100)
    readiness_tier: str
    metrics: Dict[str, ScoreMetric]
    active_resume_summary: Dict[str, Any]
    skill_coverage: List[Dict[str, Any]]
    recent_reports: List[RecentReportSummary]
