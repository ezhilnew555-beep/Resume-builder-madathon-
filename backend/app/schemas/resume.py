from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any

class ResumeStatusResponse(BaseModel):
    services_configured: bool = Field(default=True, description="Whether parsing pipeline is operational")
    pdf_parser_available: bool = Field(default=True, description="Status of PyMuPDF PDF extraction engine")
    docx_parser_available: bool = Field(default=True, description="Status of python-docx extraction engine")
    ocr_fallback_available: bool = Field(default=False, description="Status of Tesseract OCR backend")
    ai_explainer_configured: bool = Field(default=False, description="Status of LLM API key for grounded explanations")
    ocr_setup_guide: Optional[str] = Field(None, description="Guidance if OCR engine is missing")
    status_message: str = Field(..., description="Human-readable configuration diagnosis")
    roadmap_phase: str = Field(default="Phase 4: Secure Resume Upload & Extraction")

class ResumeAnalyzeRequest(BaseModel):
    file_name: str = Field(..., min_length=1, max_length=255, description="File name of the uploaded resume")
    file_type: str = Field(..., description="Document type: 'pdf' or 'docx'")
    content_base64: Optional[str] = Field(None, description="Optional raw base64 content")
    target_role: Optional[str] = Field(None, max_length=150, description="Optional target career role")

class ResumeAnalyzeNotImplementedResponse(BaseModel):
    status: str = Field(default="not_implemented", description="Execution status")
    message: str = Field(..., description="Explicit disclaimer that ATS scoring is not implemented yet")
    request_validated: bool = Field(default=True, description="Whether input schema passed validation")
    file_name: str = Field(..., description="Validated file name received")
    file_type: str = Field(..., description="Validated file type received")
    scheduled_phase: str = Field(default="Phase 5", description="Phase when ATS scoring and matching will be operational")

class ResumeUploadResponse(BaseModel):
    resume_id: str = Field(..., description="Safe internal UUID for the parsed resume")
    filename: str = Field(..., description="Sanitized original document name")
    file_type: str = Field(..., description="Document format ('pdf' or 'docx')")
    file_size_bytes: int = Field(..., description="File size in bytes")
    page_count: int = Field(default=1, description="Number of pages in the document")
    parser_method: str = Field(..., description="Extraction engine used (e.g., 'pymupdf', 'python-docx', 'tesseract-ocr')")
    extraction_status: str = Field(..., description="'success', 'partial', 'ocr_unavailable', or 'failed'")
    is_scanned: bool = Field(default=False, description="Whether document was identified as a scanned image")
    detected_sections: List[str] = Field(default_factory=list, description="Canonical keys of detected sections")
    word_count: int = Field(default=0, description="Extracted word count")
    character_count: int = Field(default=0, description="Extracted character count")
    status_message: str = Field(..., description="Detailed status or setup notice")
    extracted_at: str = Field(..., description="ISO 8601 UTC timestamp")

class ResumeDetailResponse(ResumeUploadResponse):
    sections: Dict[str, str] = Field(default_factory=dict, description="Mapped content of each detected section")
    quality_assessment: Dict[str, Any] = Field(default_factory=dict, description="Extraction quality metrics and section coverage")

class ResumeTextResponse(BaseModel):
    resume_id: str = Field(..., description="Resume UUID")
    filename: str = Field(..., description="Document name")
    raw_text: str = Field(..., description="Full raw extracted text")
    word_count: int = Field(..., description="Total word count")
    character_count: int = Field(..., description="Total character count")
    line_count: int = Field(..., description="Total line count")
    parser_method: str = Field(..., description="Extraction engine used")
    extraction_status: str = Field(..., description="Extraction status")
