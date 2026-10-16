import uuid
import datetime
from typing import Dict, Any, Optional
from fastapi import HTTPException, status

from app.schemas.evidence import EvidenceVerifyRequest, EvidenceVerificationResponse
from app.services.resume_parser import resume_store
from app.services.evidence_extractor import evidence_extractor
from app.services.profile_connection_service import profile_connection_service
from app.services.claim_evidence_matcher import claim_evidence_matcher

class EvidenceVerificationStore:
    def __init__(self):
        self._verifications: Dict[str, Dict[str, Any]] = {}

    def save(self, verification_id: str, data: Dict[str, Any]) -> None:
        self._verifications[verification_id] = data

    def get(self, verification_id: str) -> Optional[Dict[str, Any]]:
        return self._verifications.get(verification_id)

    def check_ownership(self, verification_id: str, user_id: Optional[str]) -> Dict[str, Any]:
        record = self.get(verification_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Verification report '{verification_id}' not found."
            )
        owner = record.get("user_id")
        if owner and (not user_id or user_id != owner):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: you do not have permission to view this evidence verification report."
            )
        return record

verification_store = EvidenceVerificationStore()

class EvidenceVerificationService:
    @classmethod
    def verify_evidence(
        cls,
        request: EvidenceVerifyRequest,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Orchestrates resume claim extraction, profile connection querying,
        and evidence verification comparison.
        """
        # 1. Resolve Resume Record
        resume_record = None
        if request.resume_id:
            resume_record = resume_store.check_ownership(request.resume_id, user_id)
        else:
            # Fall back to latest uploaded resume matching user_id
            for r_id, rec in reversed(list(resume_store._store.items())):
                rec_owner = rec.get("user_id")
                if not rec_owner or rec_owner == user_id:
                    resume_record = rec
                    break

        if not resume_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No resume found to verify claims against. Please upload a resume first on the Resume Upload page."
            )

        # 2. Check for dynamic GitHub connection override in request
        if request.github_username_or_url and request.github_username_or_url.strip():
            profile_connection_service.connect_profile(
                platform_id="github",
                username_or_url=request.github_username_or_url.strip(),
                user_id=user_id
            )

        # 3. Extract verifiable claims from candidate resume
        claims = evidence_extractor.extract_resume_claims(resume_record)

        # 4. Retrieve connected profiles for user
        connections = profile_connection_service.get_user_connections(user_id=user_id)

        # 5. Evaluate claims against profile evidence
        matched_results = claim_evidence_matcher.match_claims(claims, connections)

        # 6. Build and store verification report
        verif_id = f"verif-{uuid.uuid4().hex[:12]}"
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

        report_data = {
            "verification_id": verif_id,
            "user_id": user_id,
            "resume_id": resume_record.get("resume_id", "unknown"),
            "evaluated_at": now_str,
            **matched_results,
        }

        verification_store.save(verif_id, report_data)
        return report_data

    @classmethod
    def get_verification_report(
        cls,
        verification_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        return verification_store.check_ownership(verification_id, user_id=user_id)

evidence_verification_service = EvidenceVerificationService()
