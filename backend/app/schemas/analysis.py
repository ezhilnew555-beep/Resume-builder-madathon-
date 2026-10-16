from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any

class ResumeAnalyzeRequestPayload(BaseModel):
    target_role: Optional[str] = Field(None, max_length=150, description="Target career role or specialization")
    job_description: Optional[str] = Field(None, max_length=15000, description="Optional job description text to evaluate alignment")

class SkillItem(BaseModel):
    name: str = Field(..., description="Canonical skill name")
    category: str = Field(..., description="Domain category ('languages', 'frameworks', etc.)")
    evidence_snippet: str = Field(..., description="Text line where skill was identified")
    source_section: str = Field(..., description="Section containing the mention")
    occurrences: int = Field(default=1, description="Number of times found")

class FindingItem(BaseModel):
    id: str = Field(..., description="Unique finding ID")
    type: str = Field(..., description="'error', 'improvement', 'missing', or 'keyword'")
    category: str = Field(..., description="'formatting', 'impact', 'structure', 'style', etc.")
    title: str = Field(..., description="Short finding title")
    location: str = Field(..., description="Source location in resume")
    explanation: str = Field(..., description="Detailed explanation of the issue")
    original_snippet: str = Field(..., description="Exact original excerpt from resume")
    proposed_correction: str = Field(..., description="Actionable rewrite or advice")
    status: str = Field(default="pending", description="'pending', 'accepted', or 'rejected'")

class BulletPointEvaluation(BaseModel):
    original_snippet: str
    section: str
    word_count: int
    score: int
    has_metric: bool
    has_strong_verb: bool
    issues: List[str]
    suggested_rewrite: str

class ResumeAnalysisResponse(BaseModel):
    resume_id: str
    filename: str
    overall_score: int = Field(..., ge=0, le=100, description="Composite CareerLens employability readiness score (0-100)")
    readiness_tier: str = Field(..., description="'Ready for Market', 'Nearly Ready', 'Needs Improvement', 'Critical Gaps'")
    component_scores: Dict[str, int] = Field(..., description="Component breakdowns: structure, content_quality, skill_evidence, ats_readability")
    scoring_weights: Dict[str, float] = Field(..., description="Configurable prototype weights used in computation")
    scoring_rationale: List[str] = Field(default_factory=list, description="Explanations justifying the scoring calculation")
    extracted_skills: Dict[str, List[SkillItem]] = Field(default_factory=dict, description="Identified skills by domain category")
    detected_sections: List[str] = Field(default_factory=list, description="Sections identified in document")
    missing_sections: List[Dict[str, str]] = Field(default_factory=list, description="Recommended sections missing with explanations")
    findings: List[FindingItem] = Field(default_factory=list, description="Prioritized list of actionable recommendations")
    bullet_point_evaluations: List[BulletPointEvaluation] = Field(default_factory=list, description="In-depth analysis of individual bullet statements")
    data_quality_warnings: List[str] = Field(default_factory=list, description="Extraction or readability warnings")
    disclaimer: str = Field(..., description="Clear disclosure that score is a deterministic diagnostic estimate")
    analyzed_at: str = Field(..., description="ISO 8601 UTC timestamp")
