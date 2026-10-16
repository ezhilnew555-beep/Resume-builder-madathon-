import os
import shutil
from typing import Tuple, Optional, List
import fitz  # PyMuPDF
from PIL import Image
import io
from app.core.config import settings

class OCRService:
    def __init__(self):
        self._tesseract_cmd = self._find_tesseract_binary()

    def _find_tesseract_binary(self) -> Optional[str]:
        """
        Locates the tesseract executable on PATH or common installation directories.
        """
        if settings.TESSERACT_CMD and os.path.isfile(settings.TESSERACT_CMD):
            return settings.TESSERACT_CMD

        which_path = shutil.which("tesseract")
        if which_path:
            return which_path

        # Project local paths and common Windows paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
        local_project_path = os.path.join(backend_dir, "tools", "tesseract", "tesseract.exe")

        common_win_paths = [
            local_project_path,
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
        ]
        for p in common_win_paths:
            if os.path.isfile(p):
                tessdata_dir = os.path.join(os.path.dirname(p), "tessdata")
                if os.path.isdir(tessdata_dir) and "TESSDATA_PREFIX" not in os.environ:
                    os.environ["TESSDATA_PREFIX"] = tessdata_dir
                return p

        return None

    def is_ocr_available(self) -> bool:
        """
        Returns True if Tesseract OCR binary is found and usable.
        """
        # Re-check binary in case environment changed
        if not self._tesseract_cmd:
            self._tesseract_cmd = self._find_tesseract_binary()
        return self._tesseract_cmd is not None

    def get_status_details(self) -> dict:
        """
        Returns status information and setup guidance if missing.
        """
        available = self.is_ocr_available()
        return {
            "available": available,
            "engine": "Tesseract OCR",
            "binary_path": self._tesseract_cmd if available else None,
            "setup_guide": (
                "Tesseract OCR is not installed or not found on PATH. "
                "For Windows: install via 'winget install UB-Mannheim.TesseractOCR' or download from "
                "https://github.com/UB-Mannheim/tesseract/wiki. "
                "For Ubuntu/Debian: 'sudo apt install tesseract-ocr'."
            ) if not available else "OCR engine is ready for scanned documents."
        }

    def extract_text_from_pdf_stream(
        self,
        pdf_bytes: bytes,
        max_pages: Optional[int] = None
    ) -> Tuple[bool, str, int, Optional[str]]:
        """
        Performs OCR on a PDF stream.
        Returns:
            (success, extracted_text, pages_processed, error_message_or_none)
        """
        if not self.is_ocr_available():
            return (
                False,
                "",
                0,
                "OCR fallback unavailable: Tesseract OCR is not installed on this server. "
                "Scanned or flattened image-only PDFs require Tesseract OCR to extract readable text."
            )

        try:
            import pytesseract
            if self._tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self._tesseract_cmd
                tessdata_dir = os.path.join(os.path.dirname(self._tesseract_cmd), "tessdata")
                if os.path.isdir(tessdata_dir):
                    os.environ["TESSDATA_PREFIX"] = tessdata_dir


            limit_pages = max_pages or settings.MAX_OCR_PAGES
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            total_pages = min(len(doc), limit_pages)
            extracted_pages_text: List[str] = []

            for page_idx in range(total_pages):
                page = doc[page_idx]
                # Render page at 150 DPI (good compromise between speed and OCR precision)
                pix = page.get_pixmap(dpi=150)
                img_data = pix.tobytes("png")
                pil_img = Image.open(io.BytesIO(img_data))

                page_text = pytesseract.image_to_string(pil_img, config="--psm 1")
                if page_text and page_text.strip():
                    extracted_pages_text.append(page_text.strip())

            doc.close()
            combined_text = "\n\n".join(extracted_pages_text)

            if not combined_text.strip():
                return (
                    False,
                    "",
                    total_pages,
                    "OCR completed but no readable text could be recognized from the image."
                )

            return (True, combined_text, total_pages, None)

        except Exception as e:
            return (
                False,
                "",
                0,
                f"OCR processing exception: {str(e)}"
            )

ocr_service = OCRService()
