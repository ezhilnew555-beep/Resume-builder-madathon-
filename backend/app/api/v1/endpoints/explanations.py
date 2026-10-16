"""
AI Explanation and Contextual Assistant Endpoints for CareerLens (Phase 8).
Provides grounded explanations, prioritized recommendations, and chat assistance.
"""

from typing import Optional
from fastapi import APIRouter, Depends, status, HTTPException

from app.schemas.explanation import (
    ResumeExplanationResponse,
    JobMatchExplanationResponse,
    AssistantChatRequest,
    AssistantChatResponse,
)
from app.services.explanation_service import explanation_service
from app.services.assistant_service import assistant_service
from app.core.security import get_current_user_optional, AuthenticatedUser

router = APIRouter()

@router.post(
    "/explanations/resume/{resume_id}",
    response_model=ResumeExplanationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Grounded Explanations for Resume Review Findings"
)
def get_resume_explanation(
    resume_id: str,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> ResumeExplanationResponse:
    """
    Translates deterministic resume findings into clear, grounded, actionable advice.
    Numerical scores and tiers are strictly immutable.
    """
    user_id = current_user.id if current_user else None
    result = explanation_service.explain_resume(resume_id=resume_id, user_id=user_id)
    return ResumeExplanationResponse(**result)

@router.post(
    "/explanations/jobs/{match_id}",
    response_model=JobMatchExplanationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Grounded Explanations for Job Match Compatibility"
)
def get_job_match_explanation(
    match_id: str,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> JobMatchExplanationResponse:
    """
    Generates explainable alignment analysis for a candidate resume against
    a specific target job posting while preserving match scores.
    """
    user_id = current_user.id if current_user else None
    result = explanation_service.explain_job_match(match_id=match_id, user_id=user_id)
    return JobMatchExplanationResponse(**result)

@router.post(
    "/assistant/chat",
    response_model=AssistantChatResponse,
    status_code=status.HTTP_200_OK,
    summary="CareerLens Contextual Career Assistant Chat"
)
def assistant_chat(
    request: AssistantChatRequest,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> AssistantChatResponse:
    """
    Answers student questions grounded strictly in their permitted reports
    (resume review, job match, and GitHub evidence verification).
    """
    user_id = current_user.id if current_user else None
    result = assistant_service.chat(request=request, user_id=user_id)
    return result
