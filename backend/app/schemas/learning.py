from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ====================================================================
# Legacy / Existing schemas (Preserved for compatibility)
# ====================================================================
class LearningProgressItem(BaseModel):
    id: Optional[str] = None
    user_id: str
    skill_name: str
    status: str = Field(default="not_started", description="'not_started', 'in_progress', 'completed'")
    progress: int = Field(default=0, ge=0, le=100, description="Completion percentage between 0 and 100")
    updated_at: Optional[datetime] = None

class LearningProgressUpdate(BaseModel):
    status: str = Field(..., description="'not_started', 'in_progress', 'completed'")
    progress: int = Field(..., ge=0, le=100, description="Completion percentage between 0 and 100")

class LearningProgressListResponse(BaseModel):
    items: List[LearningProgressItem] = Field(default_factory=list)
    total: int = 0
    message: str = "Learning progress retrieved successfully."


# ====================================================================
# Phase 10: Personalized Learning Roadmap Schemas
# ====================================================================

class SkillGapAnalysisItem(BaseModel):
    """
    Detailed evidence and gap classification for a target role skill.
    """
    skill: str
    importance: str = Field(default="required", description="'required', 'preferred', or 'bonus'")
    evidence_found: str = Field(
        ...,
        description="Factual evidence found in resume or connected profile, or explicit note that no evidence was detected."
    )
    evidence_status: str = Field(
        default="not_demonstrated",
        description="'demonstrated', 'partial_evidence', or 'not_demonstrated'"
    )
    learning_priority: str = Field(
        default="high",
        description="'high', 'medium', or 'low'"
    )
    reason: str = Field(
        ...,
        description="Grounded explanation for why this priority was assigned without making unverified assumptions."
    )


class LearningResource(BaseModel):
    """
    Educational resource with verification status.
    """
    title: str
    url: Optional[str] = None
    resource_type: str = Field(default="documentation", description="'documentation', 'tutorial', 'project_guide', 'user_added'")
    is_verified: bool = True


class RoadmapTask(BaseModel):
    """
    Single actionable learning task within a milestone.
    """
    id: str
    milestone_week: int = Field(default=1, ge=1)
    milestone_title: str
    title: str
    instructions: str
    skill: str
    priority: str = Field(default="medium", description="'high', 'medium', or 'low'")
    estimated_hours: int = Field(default=3, ge=1)
    prerequisites: List[str] = Field(default_factory=list)
    resources: List[LearningResource] = Field(default_factory=list)
    practical_exercise: str
    deliverable: str
    completion_criteria: str
    target_role_requirement: Optional[str] = None
    status: str = Field(default="not_started", description="'not_started', 'in_progress', 'completed'")
    user_notes: Optional[str] = None
    custom_resources: List[LearningResource] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class RoadmapMilestone(BaseModel):
    """
    Week or milestone organizing roadmap tasks.
    """
    week_number: int
    title: str
    description: str
    focus_skills: List[str] = Field(default_factory=list)
    tasks: List[RoadmapTask] = Field(default_factory=list)


class LearningRoadmapResponse(BaseModel):
    """
    Complete personalized learning roadmap payload.
    """
    id: str
    user_id: Optional[str] = None
    target_role: str
    target_company: Optional[str] = None
    job_description_id: Optional[str] = None
    weekly_hours: int = 10
    target_weeks: int = 4
    skill_gaps: List[SkillGapAnalysisItem] = Field(default_factory=list)
    milestones: List[RoadmapMilestone] = Field(default_factory=list)
    all_tasks: List[RoadmapTask] = Field(default_factory=list)
    total_tasks: int = 0
    completed_tasks: int = 0
    in_progress_tasks: int = 0
    completion_percentage: int = 0
    total_estimated_hours: int = 0
    completed_hours: int = 0
    is_ai_grounded: bool = False
    provider_used: str = "deterministic_engine"
    disclaimer: str = (
        "Roadmap tasks and completion metrics reflect self-reported student progress and recommendations "
        "tailored to target job requirements. Completion does not guarantee employment or constitute third-party skill certification."
    )
    created_at: datetime
    updated_at: datetime


class RoadmapGenerateRequest(BaseModel):
    target_role: Optional[str] = None
    target_company: Optional[str] = None
    job_description: Optional[str] = None
    job_match_id: Optional[str] = None
    resume_id: Optional[str] = None
    weekly_hours: int = Field(default=10, ge=1, le=60)
    target_weeks: int = Field(default=4, ge=1, le=52)


class TaskStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(not_started|in_progress|completed)$")
    notes: Optional[str] = None
    custom_resources: Optional[List[LearningResource]] = None


class RoadmapPreferencesUpdateRequest(BaseModel):
    weekly_hours: Optional[int] = Field(None, ge=1, le=60)
    target_weeks: Optional[int] = Field(None, ge=1, le=52)


class RoadmapRefreshRequest(BaseModel):
    resume_id: Optional[str] = None
    job_match_id: Optional[str] = None
    job_description: Optional[str] = None
    target_role: Optional[str] = None
    target_company: Optional[str] = None


class RoadmapProgressResponse(BaseModel):
    roadmap_id: str
    target_role: str
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    completion_percentage: int
    total_estimated_hours: int
    completed_hours: int
    remaining_hours: int
    skills_covered_count: int
    skills_demonstrated_count: int
    status_summary: Dict[str, int]
