from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class JobMatchRequest(BaseModel):
    company: str = Field(..., min_length=1, max_length=150, description="Target company name")
    role: str = Field(..., min_length=1, max_length=150, description="Target job title")
    job_description: Optional[str] = Field(None, max_length=50000, description="Raw job description text")
    job_url: Optional[str] = Field(None, description="Optional public URL to fetch job description from")
    resume_id: Optional[str] = Field(None, description="ID of parsed resume to match; defaults to latest uploaded")

class JobMatchPendingResponse(BaseModel):
    status: str = Field(default="pending_implementation", description="Lifecycle status")
    message: str = Field(..., description="Notice that matching engine is under development")
    request_validated: bool = Field(default=True, description="Indicates request fields passed validation")
    company: str = Field(..., description="Echo of validated company name")
    role: str = Field(..., description="Echo of validated target role")
    job_description_char_count: int = Field(..., description="Length of received job description")
    scheduled_phase: str = Field(default="Phase 6: Company-Specific Job Matching", description="Target release phase")

class JobMatchRequirementItem(BaseModel):
    name: str
    category: str = "skills"
    importance: str = "required"  # 'required' or 'preferred'
    status: str = "matched"  # 'matched', 'partial', 'missing_evidence', 'needs_verification'
    demonstrated_in_project: bool = False
    evidence_quote: str = ""
    location: str = ""
    confidence: int = 0
    explanation: str = ""
    recommended_action: str = ""
    equivalent_found: Optional[str] = None

class JobMatchResponse(BaseModel):
    match_id: str
    company: str
    role: str
    overall_match_score: int = Field(..., ge=0, le=100)
    hard_skill_match_score: int = Field(..., ge=0, le=100)
    preferred_match_score: int = Field(..., ge=0, le=100)
    experience_match_score: int = Field(..., ge=0, le=100)
    evidence_strength_score: int = Field(..., ge=0, le=100)
    readiness_tier: str
    matched_requirements: List[JobMatchRequirementItem] = Field(default_factory=list)
    partial_matches: List[JobMatchRequirementItem] = Field(default_factory=list)
    missing_evidence: List[JobMatchRequirementItem] = Field(default_factory=list)
    verified_evidence_summary: str
    recommendations: List[str] = Field(default_factory=list)
    disclaimer: str
    analyzed_at: str

class FetchJobUrlRequest(BaseModel):
    url: str = Field(..., description="Target job posting URL (HTTP or HTTPS)")

class FetchJobUrlResponse(BaseModel):
    url: str
    extracted_text: str
    char_count: int
    message: str = "Job description successfully retrieved."

class JobDescriptionCreate(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=150)
    job_title: str = Field(..., min_length=1, max_length=150)
    description: str = Field(..., min_length=10, max_length=50000)

class JobDescriptionResponse(BaseModel):
    id: str
    user_id: str
    company_name: str
    job_title: str
    description: str
    created_at: Optional[datetime] = None

class JobDescriptionListResponse(BaseModel):
    items: List[JobDescriptionResponse] = Field(default_factory=list)
    total: int = 0
    message: str = "Job descriptions retrieved."
