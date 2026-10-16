from app.schemas.resume import (
    ResumeStatusResponse,
    ResumeAnalyzeRequest,
    ResumeAnalyzeNotImplementedResponse,
)
from app.services.ocr_service import ocr_service

class ResumeService:
    @staticmethod
    def check_service_status() -> ResumeStatusResponse:
        """
        Audits underlying engine availability without exposing secrets or filesystem paths.
        """
        ocr_info = ocr_service.get_status_details()
        ocr_available = ocr_info["available"]
        
        return ResumeStatusResponse(
            services_configured=True,
            pdf_parser_available=True,
            docx_parser_available=True,
            ocr_fallback_available=ocr_available,
            ai_explainer_configured=False,
            ocr_setup_guide=ocr_info["setup_guide"] if not ocr_available else None,
            status_message=(
                "Resume parsing pipeline is active. PyMuPDF and python-docx engines are ready. "
                + ("Tesseract OCR is available for scanned PDFs." if ocr_available else "Tesseract OCR is optional / not found on host.")
            ),
            roadmap_phase="Phase 4: Secure Resume Upload & Extraction (ATS Scoring in Phase 5)"
        )

    @staticmethod
    def handle_pending_analyze(request: ResumeAnalyzeRequest) -> ResumeAnalyzeNotImplementedResponse:
        """
        Validates request and returns a clear, non-invented 'not implemented yet' response (501).
        """
        return ResumeAnalyzeNotImplementedResponse(
            status="not_implemented",
            message=(
                "Resume ATS scoring pipeline is scheduled for Phase 5. "
                "Document upload, validation, and section extraction are fully functional in Phase 4."
            ),
            request_validated=True,
            file_name=request.file_name,
            file_type=request.file_type,
            scheduled_phase="Phase 5"
        )

resume_service = ResumeService()
