from fastapi import APIRouter
from app.schemas.common import HealthResponse
from app.core.config import settings
from app.services.ai_provider import ai_provider_manager
from app.services.ocr_service import ocr_service


router = APIRouter()

@router.get("/health", response_model=HealthResponse, summary="Service Health & Component Readiness")
def check_health() -> HealthResponse:
    """
    Returns application health status, current version, deployment environment,
    and granular readiness indicators for key subsystems.
    """
    active_provider = ai_provider_manager.get_active_provider()
    
    components = {
        "database": {
            "configured": settings.is_supabase_configured,
            "status": "ready" if settings.is_supabase_configured else "not_configured"
        },
        "pdf_parser": {
            "available": True,
            "engine": "pypdf"
        },
        "docx_parser": {
            "available": True,
            "engine": "python-docx"
        },
        "ocr_fallback": {
            "available": ocr_service.is_ocr_available(),
            "engine": "Tesseract OCR"
        },
        "ai_provider": {
            "active": active_provider.provider_name,
            "available": active_provider.is_available(),
            "status": "ready"
        },
        "auth": {
            "configured": bool(settings.SUPABASE_URL and (settings.SUPABASE_ANON_KEY or settings.SUPABASE_JWT_SECRET)),
            "engine": "supabase_jwt"
        }
    }

    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        components=components
    )

