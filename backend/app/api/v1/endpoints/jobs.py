from typing import Optional
from fastapi import APIRouter, Depends, status

from app.schemas.job import (
    JobMatchRequest,
    JobMatchResponse,
    FetchJobUrlRequest,
    FetchJobUrlResponse,
)
from app.services.job_service import job_service
from app.core.security import get_current_user_optional, AuthenticatedUser

router = APIRouter()

@router.post(
    "/jobs/match",
    response_model=JobMatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Match Resume against Company Job Description"
)
def match_job(
    request: JobMatchRequest,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> JobMatchResponse:
    """
    Compares candidate resume against a specific target job posting.
    Extracts required and preferred skills, evaluates evidence in experience and projects,
    recognizes credible equivalents (e.g. Postgres <-> SQL), and calculates deterministic fit scores.
    """
    user_id = current_user.id if current_user else None
    result = job_service.match_job(request, user_id=user_id)
    return JobMatchResponse(**result)

@router.get(
    "/jobs/matches/{match_id}",
    response_model=JobMatchResponse,
    summary="Get Stored Job Match Report"
)
def get_match_report(
    match_id: str,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> JobMatchResponse:
    """
    Retrieves previously computed job match analysis by ID, enforcing user ownership.
    """
    user_id = current_user.id if current_user else None
    result = job_service.get_match(match_id, user_id=user_id)
    return JobMatchResponse(**result)

@router.post(
    "/jobs/fetch-url",
    response_model=FetchJobUrlResponse,
    summary="Safely Fetch Job Description Text from Public URL"
)
def fetch_job_url(
    request: FetchJobUrlRequest,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> FetchJobUrlResponse:
    """
    Safely retrieves remote job description text while blocking SSRF, loopback attacks,
    and private intranet ranges.
    """
    result = job_service.fetch_url(request.url)
    return FetchJobUrlResponse(**result)
