import os
import re
import uuid
import zipfile
import io
from typing import Tuple, Dict, Any, Optional
from fastapi import HTTPException, status
from app.core.config import settings

# Recognized magic byte signatures
PDF_MAGIC = b"%PDF-"
ZIP_MAGIC = b"PK\x03\x04"

class FileValidationError(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)

class FileValidationService:
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Strips dangerous characters, path traversal sequences, and control characters.
        """
        if not filename:
            return "resume_document"
        # Take basename only
        base = os.path.basename(filename)
        # Remove null bytes and non-printable characters
        base = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", base)
        # Replace dangerous path characters
        cleaned = re.sub(r'[^a-zA-Z0-9_\-\. ]', '_', base).strip()
        return cleaned[:100] if cleaned else "resume_document"

    @classmethod
    def validate_file(
        cls,
        filename: str,
        content_type: Optional[str],
        file_bytes: bytes,
        max_size_mb: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validates file size, extensions, magic bytes, and internal structure.
        Returns a dict of sanitized metadata or raises FileValidationError.
        """
        limit_mb = max_size_mb or settings.MAX_UPLOAD_SIZE_MB
        max_bytes = limit_mb * 1024 * 1024

        # 1. Check for empty file
        if not file_bytes or len(file_bytes) == 0:
            raise FileValidationError(
                detail="Uploaded file is empty (0 bytes). Please upload a valid document.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # 2. Check file size against limit
        file_size = len(file_bytes)
        if file_size > max_bytes:
            raise FileValidationError(
                detail=f"File size ({file_size / (1024 * 1024):.2f} MB) exceeds maximum allowed limit of {limit_mb} MB.",
                status_code=413
            )

        # 3. Extract and sanitize filename extension
        sanitized_name = cls.sanitize_filename(filename)
        _, ext = os.path.splitext(sanitized_name.lower())

        # 4. Check for macro-enabled document disguised or uploaded
        if ext == ".docm" or sanitized_name.lower().endswith(".docm"):
            raise FileValidationError(
                detail="Macro-enabled documents (.docm) are rejected for security reasons. Please upload a standard .docx or .pdf.",
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            )

        # 5. Check supported filename extension
        if ext not in [".pdf", ".docx"]:
            raise FileValidationError(
                detail=f"Unsupported file format '{ext}'. Only PDF (.pdf) and Microsoft Word (.docx) files are supported.",
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            )

        # 5. Validate file signatures and internal structures
        if ext == ".pdf":
            cls._validate_pdf_structure(file_bytes)
            detected_type = "pdf"
        elif ext == ".docx":
            cls._validate_docx_structure(file_bytes)
            detected_type = "docx"
        else:
            raise FileValidationError(
                detail="Unsupported document format.",
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            )

        # 6. Generate cryptographically safe internal identifier
        safe_resume_id = str(uuid.uuid4())

        return {
            "resume_id": safe_resume_id,
            "original_filename": sanitized_name,
            "detected_type": detected_type,
            "file_size_bytes": file_size,
            "content_type": content_type or f"application/{detected_type}",
        }

    @staticmethod
    def _validate_pdf_structure(file_bytes: bytes) -> None:
        """
        Verifies PDF magic bytes in header.
        """
        # PDF magic bytes %PDF- should appear in the first 1024 bytes
        header_sample = file_bytes[:1024]
        if PDF_MAGIC not in header_sample:
            raise FileValidationError(
                detail="Invalid file signature: document claims to be a PDF but does not have a valid %PDF header.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @staticmethod
    def _validate_docx_structure(file_bytes: bytes) -> None:
        """
        Verifies that DOCX is a valid OpenXML zip archive and contains required parts.
        Rejects macro-bearing word documents (vbaProject.bin).
        """
        # DOCX must begin with ZIP magic bytes PK\x03\x04
        if not file_bytes.startswith(ZIP_MAGIC):
            raise FileValidationError(
                detail="Invalid file signature: document claims to be a DOCX but is not a valid ZIP-based OpenXML package.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes), "r") as zf:
                namelist = zf.namelist()

                # Check for critical Word document parts
                if "word/document.xml" not in namelist and "[Content_Types].xml" not in namelist:
                    raise FileValidationError(
                        detail="Malformed Word document: missing word/document.xml structure.",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

                # Reject embedded VBA macros
                if any("vbaProject.bin" in name.lower() for name in namelist):
                    raise FileValidationError(
                        detail="Security violation: document contains embedded macros (vbaProject.bin).",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

                # Test archive integrity
                bad_file = zf.testzip()
                if bad_file:
                    raise FileValidationError(
                        detail=f"Corrupted Word archive component: {bad_file}.",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

        except zipfile.BadZipFile:
            raise FileValidationError(
                detail="Corrupted Word document: unable to read DOCX zip contents.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except FileValidationError:
            raise
        except Exception as e:
            raise FileValidationError(
                detail=f"Failed to inspect DOCX structure: {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST
            )

file_validator = FileValidationService()
