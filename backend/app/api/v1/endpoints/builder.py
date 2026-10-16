"""
API Endpoints for AI Resume Builder, Preview, Versioning, and Export (Phase 9).
"""

from typing import Optional
from fastapi import APIRouter, Depends, status, Response, HTTPException

from app.schemas.builder import (
    ResumeDraftCreateRequest,
    ResumeDraftUpdateRequest,
    ResumeDraftResponse,
    ResumeVersionItem,
    VersionCreateRequest,
    VersionListResponse,
    AIEditSuggestRequest,
    AIEditSuggestResponse,
    ExportRequest,
    BuilderAnalysisResponse,
)
from app.services.builder_service import builder_service
from app.services.resume_export_service import resume_export_service
from app.core.security import get_current_user_optional, AuthenticatedUser

router = APIRouter()

@router.post(
    "/builder/resumes",
    response_model=ResumeDraftResponse,
    status_code=status.HTTP_200_OK,
    summary="Create New Resume Draft"
)
def create_draft(
    request: ResumeDraftCreateRequest,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> ResumeDraftResponse:
    """
    Creates a new editable resume draft. Can initialize from a blank slate or
    import structured sections from a previously uploaded and parsed resume.
    """
    user_id = current_user.id if current_user else None
    return builder_service.create_draft(request, user_id=user_id)

@router.get(
    "/builder/resumes/{draft_id}",
    response_model=ResumeDraftResponse,
    summary="Get Resume Draft by ID"
)
def get_draft(
    draft_id: str,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> ResumeDraftResponse:
    """
    Retrieves the current draft content, enforcing ownership isolation.
    """
    user_id = current_user.id if current_user else None
    return builder_service.get_draft(draft_id, user_id=user_id)

@router.put(
    "/builder/resumes/{draft_id}",
    response_model=ResumeDraftResponse,
    summary="Update Resume Draft (Autosave)"
)
def update_draft(
    draft_id: str,
    request: ResumeDraftUpdateRequest,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> ResumeDraftResponse:
    """
    Updates the resume draft in place, preserving content and updating timestamps.
    """
    user_id = current_user.id if current_user else None
    return builder_service.update_draft(draft_id, request, user_id=user_id)

@router.post(
    "/builder/resumes/{draft_id}/version",
    response_model=ResumeVersionItem,
    status_code=status.HTTP_200_OK,
    summary="Create Snapshot Version"
)
def create_version_snapshot(
    draft_id: str,
    request: VersionCreateRequest,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> ResumeVersionItem:
    """
    Saves an immutable snapshot version so the student can compare or revert changes.
    """
    user_id = current_user.id if current_user else None
    return builder_service.create_version_snapshot(draft_id, note=request.note, user_id=user_id)

@router.get(
    "/builder/resumes/{draft_id}/versions",
    response_model=VersionListResponse,
    summary="List Saved Versions"
)
def list_versions(
    draft_id: str,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> VersionListResponse:
    """
    Lists all saved version snapshots for a draft.
    """
    user_id = current_user.id if current_user else None
    return builder_service.list_versions(draft_id, user_id=user_id)

@router.post(
    "/builder/resumes/{draft_id}/suggest",
    response_model=AIEditSuggestResponse,
    summary="Get AI-Assisted Diff Suggestions"
)
def get_ai_suggestions(
    draft_id: str,
    request: AIEditSuggestRequest,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> AIEditSuggestResponse:
    """
    Generates structured edit recommendations with original text, proposed text,
    and rationale. Never fabricates metrics or skills.
    """
    user_id = current_user.id if current_user else None
    return builder_service.suggest_edits(draft_id, request, user_id=user_id)

@router.post(
    "/builder/resumes/{draft_id}/export/docx",
    summary="Export Resume as Native DOCX Document"
)
def export_docx(
    draft_id: str,
    request: Optional[ExportRequest] = None,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
):
    """
    Compiles the current resume draft into a formatted Microsoft Word document (.docx).
    """
    user_id = current_user.id if current_user else None
    draft = builder_service.get_draft(draft_id, user_id=user_id)
    
    data = (request.data if request and request.data else draft.data)
    template_id = (request.template_id if request and request.template_id else data.template_id)

    docx_bytes = resume_export_service.export_docx(data, template_id=template_id)
    filename = f"Resume_{data.contact.full_name or 'CareerLens'}.docx".replace(" ", "_")

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.post(
    "/builder/resumes/{draft_id}/export/pdf",
    summary="Export Resume as Native Vector PDF Document"
)
def export_pdf(
    draft_id: str,
    request: Optional[ExportRequest] = None,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
):
    """
    Compiles the current resume draft into a clean, selectable vector PDF with page overflow management.
    """
    user_id = current_user.id if current_user else None
    draft = builder_service.get_draft(draft_id, user_id=user_id)
    
    data = (request.data if request and request.data else draft.data)
    template_id = (request.template_id if request and request.template_id else data.template_id)

    pdf_bytes = resume_export_service.export_pdf(data, template_id=template_id)
    filename = f"Resume_{data.contact.full_name or 'CareerLens'}.pdf".replace(" ", "_")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.post(
    "/builder/resumes/{draft_id}/analyze",
    response_model=BuilderAnalysisResponse,
    summary="Rerun Phase 5 ATS Analysis on Edited Draft"
)
def reanalyze_draft(
    draft_id: str,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> BuilderAnalysisResponse:
    """
    Extracts text from the current builder state and runs Phase 5 deterministic scoring,
    providing instant ATS feedback on edits.
    """
    user_id = current_user.id if current_user else None
    return builder_service.reanalyze_draft(draft_id, user_id=user_id)
