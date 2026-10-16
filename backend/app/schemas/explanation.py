from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ResumeFindingExplanation(BaseModel):
    finding_id: str
    issue_title: str
    section: str
    original_excerpt: str
    explanation: str
    impact_reason: str
    concrete_suggestion: str
    missing_facts_requested: Optional[str] = None

class JobMatchExplanationItem(BaseModel):
    requirement_name: str
    status: str  # 'matched', 'partial', 'missing_evidence', 'needs_verification'
    importance: str  # 'required', 'preferred'
    job_requirement_explanation: str
    candidate_evidence_summary: str
    evidence_quote: str = ""
    recommended_action: str

class PrioritizedRecommendation(BaseModel):
    id: str
    priority: str  # 'high', 'medium', 'low'
    category: str  # 'skills', 'experience', 'structure', 'clarity', 'verification'
    title: str
    description: str
    linked_finding_id: Optional[str] = None
    priority_reason: str
    effort_estimate: str = "moderate"  # 'quick_fix', 'moderate', 'substantial'

class ResumeExplanationResponse(BaseModel):
    resume_id: str
    is_ai_generated: bool
    provider: str
    overall_score: int
    readiness_tier: str
    executive_summary: str
    finding_explanations: List[ResumeFindingExplanation] = Field(default_factory=list)
    prioritized_recommendations: List[PrioritizedRecommendation] = Field(default_factory=list)
    disclaimer: str
    generated_at: str

class JobMatchExplanationResponse(BaseModel):
    match_id: str
    is_ai_generated: bool
    provider: str
    overall_match_score: int
    company: str
    role: str
    match_summary: str
    requirement_explanations: List[JobMatchExplanationItem] = Field(default_factory=list)
    prioritized_recommendations: List[PrioritizedRecommendation] = Field(default_factory=list)
    disclaimer: str
    generated_at: str

class AssistantChatMessage(BaseModel):
    role: str  # 'user', 'assistant', 'system'
    content: str = Field(..., max_length=2000)

class AssistantChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    history: List[AssistantChatMessage] = Field(default_factory=list, max_length=10)
    resume_id: Optional[str] = None
    match_id: Optional[str] = None
    verification_id: Optional[str] = None

class AssistantChatResponse(BaseModel):
    reply: str
    is_ai_generated: bool
    provider: str
    referenced_reports: List[str] = Field(default_factory=list)
    suggested_followups: List[str] = Field(default_factory=list)
