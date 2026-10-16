"""
Pydantic Schemas for AI Resume Builder, Preview, Export, and Versioning (Phase 9).
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class EducationEntry(BaseModel):
    id: str
    school: str
    degree: str
    field_of_study: str = ""
    start_date: str = ""
    end_date: str = ""
    gpa: str = ""
    highlights: str = ""

class ExperienceEntry(BaseModel):
    id: str
    role: str
    company: str
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    is_current: bool = False
    bullets: List[str] = Field(default_factory=list)

class ProjectEntry(BaseModel):
    id: str
    name: str
    tech_stack: str = ""
    url: str = ""
    bullets: List[str] = Field(default_factory=list)

class CertificationEntry(BaseModel):
    id: str
    name: str
    issuer: str
    date: str = ""
    url: str = ""

class AchievementEntry(BaseModel):
    id: str
    title: str
    description: str = ""
    date: str = ""

class SkillsData(BaseModel):
    languages: str = ""
    frameworks: str = ""
    databases: str = ""
    tools: str = ""
    soft_skills: str = ""

class ContactData(BaseModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""

class ResumeBuilderData(BaseModel):
    contact: ContactData = Field(default_factory=ContactData)
    summary: str = ""
    education: List[EducationEntry] = Field(default_factory=list)
    skills: SkillsData = Field(default_factory=SkillsData)
    projects: List[ProjectEntry] = Field(default_factory=list)
    experience: List[ExperienceEntry] = Field(default_factory=list)
    certifications: List[CertificationEntry] = Field(default_factory=list)
    achievements: List[AchievementEntry] = Field(default_factory=list)
    section_order: List[str] = Field(
        default_factory=lambda: [
            "contact", "summary", "skills", "experience", "projects", "education", "certifications", "achievements"
        ]
    )
    template_id: str = "modern"  # 'modern', 'classic', 'minimal'

class ResumeDraftCreateRequest(BaseModel):
    title: str = "My Resume Draft"
    source_resume_id: Optional[str] = None  # If importing from parsed upload
    template_id: str = "modern"
    initial_data: Optional[ResumeBuilderData] = None

class ResumeDraftUpdateRequest(BaseModel):
    title: Optional[str] = None
    data: ResumeBuilderData
    template_id: Optional[str] = None

class ResumeVersionItem(BaseModel):
    version_id: str
    version_number: int
    created_at: str
    note: str
    data_snapshot: ResumeBuilderData

class ResumeDraftResponse(BaseModel):
    draft_id: str
    user_id: Optional[str] = None
    title: str
    created_at: str
    updated_at: str
    current_version: int
    data: ResumeBuilderData
    is_saved: bool = True
    imported_from_resume_id: Optional[str] = None

class VersionCreateRequest(BaseModel):
    note: str = Field(default="Manual save checkpoint", max_length=150)

class VersionListResponse(BaseModel):
    draft_id: str
    total_versions: int
    versions: List[ResumeVersionItem]

class AISuggestionItem(BaseModel):
    id: str
    target_section: str  # 'summary', 'experience', 'projects', 'skills'
    target_entry_id: Optional[str] = None
    target_bullet_index: Optional[int] = None
    title: str
    original_text: str
    proposed_text: str
    rationale: str
    missing_facts_prompt: Optional[str] = None

class AIEditSuggestRequest(BaseModel):
    focus_area: str = "general"  # 'general', 'clarity', 'metrics', 'star_method', 'job_tailor'
    job_description: Optional[str] = None
    target_section: Optional[str] = None
    current_data: Optional[ResumeBuilderData] = None

class AIEditSuggestResponse(BaseModel):
    draft_id: str
    is_ai_generated: bool
    provider: str
    suggestions: List[AISuggestionItem]
    disclaimer: str

class ExportRequest(BaseModel):
    template_id: Optional[str] = None
    data: Optional[ResumeBuilderData] = None

class BuilderAnalysisResponse(BaseModel):
    draft_id: str
    overall_score: int
    readiness_tier: str
    component_scores: Dict[str, int]
    detected_skills_count: int
    findings_count: int
    analyzed_text_sample: str
