from typing import Optional
from fastapi import APIRouter, Depends, status

from app.schemas.evidence import (
    EvidenceVerifyRequest,
    EvidenceVerificationResponse,
)
from app.services.evidence_verification_service import evidence_verification_service
from app.core.security import get_current_user_optional, AuthenticatedUser

router = APIRouter()

@router.post(
    "/evidence/verify",
    response_model=EvidenceVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Resume Claims Against Connected External Evidence"
)
def verify_evidence(
    request: EvidenceVerifyRequest,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> EvidenceVerificationResponse:
    """
    Extracts project and technical claims from an uploaded resume and cross-references them
    against accessible GitHub repositories, commit languages, README documentation,
    and observable test artifacts.
    """
    user_id = current_user.id if current_user else None
    result = evidence_verification_service.verify_evidence(request, user_id=user_id)
    return EvidenceVerificationResponse(**result)

@router.get(
    "/evidence/{verification_id}",
    response_model=EvidenceVerificationResponse,
    summary="Get Stored Evidence Verification Report"
)
def get_verification_report(
    verification_id: str,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> EvidenceVerificationResponse:
    """
    Retrieves previously computed evidence verification report by ID with user ownership checks.
    """
    user_id = current_user.id if current_user else None
    result = evidence_verification_service.get_verification_report(verification_id, user_id=user_id)
    return EvidenceVerificationResponse(**result)
