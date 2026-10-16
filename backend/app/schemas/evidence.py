from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ClaimVerificationItem(BaseModel):
    claim_id: str
    claim_type: str = "project"  # 'project', 'technical_skill', 'achievement'
    original_claim: str
    project_name: Optional[str] = None
    claimed_technologies: List[str] = Field(default_factory=list)
    evidence_source: str
    supporting_excerpt: str = ""
    status: str = "unverified"  # 'supported', 'partially_supported', 'unverified', 'inaccessible'
    confidence: int = 0
    reason: str
    evidence_limitations: str
    recommended_action: str
    repository_url: Optional[str] = None
    has_test_suite: bool = False
    has_documentation: bool = False
    language_breakdown: Dict[str, Any] = Field(default_factory=dict)

class EvidenceVerifyRequest(BaseModel):
    resume_id: Optional[str] = Field(None, description="Optional specific resume ID; defaults to latest uploaded")
    github_username_or_url: Optional[str] = Field(None, description="Optional GitHub override")

class EvidenceVerificationResponse(BaseModel):
    verification_id: str
    user_id: Optional[str] = None
    resume_id: str
    evaluated_at: str
    total_claims: int
    supported_claims: int
    partially_supported_claims: int
    unverified_claims: int
    inaccessible_claims: int
    verification_score: int = Field(..., ge=0, le=100)
    claims: List[ClaimVerificationItem] = Field(default_factory=list)
    connected_sources: List[str] = Field(default_factory=list)
    summary_message: str
    disclaimer: str
