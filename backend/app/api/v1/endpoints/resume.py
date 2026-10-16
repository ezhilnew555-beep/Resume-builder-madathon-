from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.schemas.resume import (
    ResumeStatusResponse,
    ResumeAnalyzeRequest,
    ResumeAnalyzeNotImplementedResponse,
    ResumeUploadResponse,
    ResumeDetailResponse,
    ResumeTextResponse,
)
from app.schemas.analysis import (
    ResumeAnalysisResponse,
    ResumeAnalyzeRequestPayload,
)
from app.services.resume_service import resume_service
from app.services.resume_parser import resume_parser, resume_store
from app.services.resume_analysis_service import resume_analysis_service
from app.core.security import get_current_user_optional, AuthenticatedUser

router = APIRouter()

@router.get("/resume/status", response_model=ResumeStatusResponse, summary="Resume Service Status")
def get_resume_status() -> ResumeStatusResponse:
    """
    Returns whether PyMuPDF, python-docx, and Tesseract OCR services are operational.
    """
    return resume_service.check_service_status()

@router.post(
    "/resume/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload & Extract Resume"
)
async def upload_resume(
    file: UploadFile = File(..., description="PDF or DOCX resume document (max 5MB)"),
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> ResumeUploadResponse:
    """
    Uploads a resume file (PDF or DOCX), validates file signatures and safety,
    extracts plain text and detects sections, and applies OCR fallback if scanned.
    
    If the caller is authenticated via Supabase Bearer token, the resume is associated
    with their account and protected by access control.
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No document file provided. Please attach a valid PDF or DOCX resume."
        )

    # Read binary bytes
    try:
        file_bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}"
        )

    user_id = current_user.id if current_user else None

    # Execute parsing pipeline
    result = resume_parser.parse_document(
        file_bytes=file_bytes,
        filename=file.filename,
        content_type=file.content_type,
        user_id=user_id
    )

    return ResumeUploadResponse(**result)

@router.get(
    "/resume/{resume_id}",
    response_model=ResumeDetailResponse,
    summary="Get Parsed Resume Details"
)
def get_resume_details(
    resume_id: str,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> ResumeDetailResponse:
    """
    Retrieves parsed resume sections, extraction quality metrics, and metadata.
    Enforces user ownership if document was uploaded by an authenticated student.
    """
    user_id = current_user.id if current_user else None
    record = resume_store.check_ownership(resume_id, user_id)
    return ResumeDetailResponse(**record)

@router.get(
    "/resume/{resume_id}/text",
    response_model=ResumeTextResponse,
    summary="Get Raw Extracted Resume Text"
)
def get_resume_text(
    resume_id: str,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> ResumeTextResponse:
    """
    Retrieves raw extracted text for preview and later analysis.
    Enforces student ownership checks.
    """
    user_id = current_user.id if current_user else None
    record = resume_store.check_ownership(resume_id, user_id)
    
    raw = record.get("raw_text", "")
    lines = raw.splitlines() if raw else []

    return ResumeTextResponse(
        resume_id=record["resume_id"],
        filename=record["filename"],
        raw_text=raw,
        word_count=record.get("word_count", 0),
        character_count=record.get("character_count", 0),
        line_count=len(lines),
        parser_method=record.get("parser_method", "unknown"),
        extraction_status=record.get("extraction_status", "unknown")
    )

@router.post(
    "/resume/{resume_id}/analyze",
    response_model=ResumeAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Extracted Resume Content"
)
def run_resume_analysis(
    resume_id: str,
    payload: Optional[ResumeAnalyzeRequestPayload] = None,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> ResumeAnalysisResponse:
    """
    Performs deterministic ATS-style resume analysis on extracted vector text:
    - Extracts skills with taxonomy and evidence citations
    - Assesses section completeness and entry-level profile readiness
    - Analyzes bullet points for strong action verbs and honest impact rewrites
    - Evaluates grammar, passive voice, and first-person pronoun avoidance
    - Checks machine readability and keyword density
    - Computes transparent weighted component scores and CareerLens readiness tier
    """
    user_id = current_user.id if current_user else None
    result = resume_analysis_service.analyze_resume(
        resume_id=resume_id,
        payload=payload,
        user_id=user_id
    )
    return ResumeAnalysisResponse(**result)

@router.get(
    "/resume/{resume_id}/analysis",
    response_model=ResumeAnalysisResponse,
    summary="Get Resume Analysis Results"
)
def get_resume_analysis(
    resume_id: str,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> ResumeAnalysisResponse:
    """
    Retrieves previously computed ATS diagnostic analysis for a resume,
    enforcing student ownership checks.
    """
    user_id = current_user.id if current_user else None
    result = resume_analysis_service.get_analysis(
        resume_id=resume_id,
        user_id=user_id
    )
    return ResumeAnalysisResponse(**result)

@router.post(
    "/resume/analyze",
    response_model=ResumeAnalyzeNotImplementedResponse,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Analyze Resume Legacy Prototype (Use /resume/{resume_id}/analyze instead)"
)
def analyze_resume(request: ResumeAnalyzeRequest):
    """
    Validates legacy mock payload and advises caller to use the real /resume/{resume_id}/analyze route.
    """
    response_data = resume_service.handle_pending_analyze(request)
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content=response_data.model_dump()
    )

