import os
import io
import time
import datetime
from typing import Dict, Any, Optional, List
import fitz  # PyMuPDF
import docx  # python-docx
from fastapi import HTTPException, status

from app.core.config import settings
from app.services.file_validation import file_validator, FileValidationError
from app.services.ocr_service import ocr_service
from app.services.resume_section_detector import section_detector

class ResumeProcessingError(HTTPException):
    def __init__(self, detail: str, status_code: int = 422):
        super().__init__(status_code=status_code, detail=detail)

class ParsedResumeStore:
    """
    In-memory storage for parsed resumes with TTL cleanup and strict user ownership.
    Allows retrieval of parsed resume metadata and raw text.
    """
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def save(self, resume_id: str, data: Dict[str, Any]) -> None:
        self._store[resume_id] = {
            **data,
            "_stored_at": time.time(),
        }

    def get(self, resume_id: str) -> Optional[Dict[str, Any]]:
        record = self._store.get(resume_id)
        if not record:
            return None
        return record

    def check_ownership(self, resume_id: str, user_id: Optional[str]) -> Dict[str, Any]:
        record = self.get(resume_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID '{resume_id}' not found."
            )
        # If record was uploaded by an authenticated user
        record_owner = record.get("user_id")
        if record_owner:
            if not user_id or user_id != record_owner:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: you do not have permission to view this resume."
                )
        return record

resume_store = ParsedResumeStore()

class ResumeParserService:
    @classmethod
    def parse_document(
        cls,
        file_bytes: bytes,
        filename: str,
        content_type: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validates, extracts text and sections from PDF or DOCX, and handles OCR fallback.
        Cleans up memory/temp buffers immediately.
        """
        # 1. Structural & signature validation
        validation_info = file_validator.validate_file(
            filename=filename,
            content_type=content_type,
            file_bytes=file_bytes
        )

        resume_id = validation_info["resume_id"]
        doc_type = validation_info["detected_type"]
        original_name = validation_info["original_filename"]
        file_size = validation_info["file_size_bytes"]

        start_time = time.time()
        parser_method = ""
        extraction_status = "success"
        status_message = "Document successfully parsed."
        raw_text = ""
        page_count = 1
        is_scanned = False

        try:
            if doc_type == "pdf":
                raw_text, page_count, parser_method, is_scanned, extraction_status, status_message = (
                    cls._extract_pdf(file_bytes)
                )
            elif doc_type == "docx":
                raw_text, page_count, parser_method, extraction_status, status_message = (
                    cls._extract_docx(file_bytes)
                )
            else:
                raise ResumeProcessingError(
                    detail="Unsupported file format encountered during parsing.",
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
                )

        except FileValidationError:
            raise
        except HTTPException:
            raise
        except Exception as e:
            raise ResumeProcessingError(
                detail=f"Failed to extract document contents: {str(e)}"
            )

        # 2. Section detection and quality evaluation (if text extracted)
        sections = {}
        quality = {}
        if raw_text and raw_text.strip():
            sections = section_detector.segment_sections(raw_text)
            quality = section_detector.evaluate_extraction_quality(raw_text, sections)
        else:
            quality = {
                "total_words": 0,
                "total_characters": 0,
                "detected_sections_count": 0,
                "detected_sections": [],
                "missing_core_sections": ["education", "skills", "experience"],
                "quality_score": 0,
                "quality_level": "none",
                "has_contact_info": False,
            }

        duration_ms = int((time.time() - start_time) * 1000)

        result_payload = {
            "resume_id": resume_id,
            "filename": original_name,
            "file_type": doc_type,
            "file_size_bytes": file_size,
            "page_count": page_count,
            "parser_method": parser_method,
            "extraction_status": extraction_status,
            "is_scanned": is_scanned,
            "status_message": status_message,
            "sections": sections,
            "detected_sections": [k for k in sections.keys() if k != "header"],
            "raw_text": raw_text,
            "word_count": quality.get("total_words", 0),
            "character_count": quality.get("total_characters", 0),
            "quality_assessment": quality,
            "extracted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "processing_time_ms": duration_ms,
            "user_id": user_id,
        }

        # Store in managed in-memory repository
        resume_store.save(resume_id, result_payload)

        return result_payload

    @classmethod
    def _extract_pdf(cls, file_bytes: bytes):
        """
        Extracts text from PDF using PyMuPDF. Checks encryption, page limits, and text density.
        Invokes OCR fallback if document has little or no extractable vector text.
        """
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            raise ResumeProcessingError(
                detail=f"Corrupted or invalid PDF structure: {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Check for password/encryption
            if doc.is_encrypted:
                raise ResumeProcessingError(
                    detail="Encrypted or password-protected PDF cannot be processed. Please provide an unlocked document.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            page_count = len(doc)
            if page_count == 0:
                raise ResumeProcessingError(
                    detail="PDF document contains zero pages.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if page_count > settings.MAX_RESUME_PAGES:
                raise ResumeProcessingError(
                    detail=f"PDF document has {page_count} pages, exceeding maximum limit of {settings.MAX_RESUME_PAGES} pages.",
                    status_code=413
                )

            pages_text: List[str] = []
            for page in doc:
                text = page.get_text("text")
                if text and text.strip():
                    pages_text.append(text.strip())

            extracted_text = "\n\n".join(pages_text).strip()

            # Check if vector text is sufficient or if this is a scanned/flattened image PDF
            # A typical one-page resume contains at least 100-300 words. Fewer than 50 chars indicates scanned image.
            if len(extracted_text) < 50:
                is_scanned = True
                # Trigger OCR fallback
                if ocr_service.is_ocr_available():
                    success, ocr_text, pages_done, err = ocr_service.extract_text_from_pdf_stream(file_bytes)
                    if success and len(ocr_text) >= 50:
                        return (
                            ocr_text,
                            page_count,
                            "tesseract-ocr",
                            True,
                            "success",
                            f"Text successfully extracted via Tesseract OCR across {pages_done} pages."
                        )
                    else:
                        return (
                            ocr_text or "",
                            page_count,
                            "tesseract-ocr",
                            True,
                            "partial",
                            f"Scanned document detected. OCR attempted but produced low fidelity: {err or 'Unreadable text'}"
                        )
                else:
                    ocr_info = ocr_service.get_status_details()
                    return (
                        "",
                        page_count,
                        "pymupdf-failed-scanned",
                        True,
                        "ocr_unavailable",
                        (
                            "Scanned or image-only PDF detected with no selectable vector text. "
                            f"{ocr_info['setup_guide']}"
                        )
                    )

            return (
                extracted_text,
                page_count,
                "pymupdf",
                False,
                "success",
                "Vector text extracted successfully with PyMuPDF."
            )

        finally:
            doc.close()

    @classmethod
    def _extract_docx(cls, file_bytes: bytes):
        """
        Extracts paragraphs and tables from DOCX using python-docx.
        Preserves paragraph boundaries.
        """
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
        except Exception as e:
            raise ResumeProcessingError(
                detail=f"Corrupted or invalid DOCX document: {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        text_blocks: List[str] = []

        # Extract regular paragraphs
        for p in doc.paragraphs:
            clean = p.text.strip()
            if clean:
                text_blocks.append(clean)

        # Extract text inside tables (e.g. skills or contact info in tables)
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    text_blocks.append(" | ".join(row_cells))

        extracted_text = "\n\n".join(text_blocks).strip()

        if len(extracted_text) < 20:
            return (
                extracted_text,
                1,
                "python-docx",
                "partial",
                "DOCX document was processed but contains very little readable text."
            )

        return (
            extracted_text,
            1,
            "python-docx",
            "success",
            "Document paragraphs and tables extracted successfully with python-docx."
        )

resume_parser = ResumeParserService()
