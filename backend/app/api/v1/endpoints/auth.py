from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.core.config import settings
from app.core.security import get_current_user, AuthenticatedUser

router = APIRouter()

class AuthStatusResponse(BaseModel):
    supabase_configured: bool
    supabase_url_configured: bool
    jwt_secret_configured: bool
    auth_provider: str = "Supabase Auth"
    message: str

@router.get("/auth/status", response_model=AuthStatusResponse, summary="Auth Configuration Status")
def check_auth_status() -> AuthStatusResponse:
    """
    Returns public diagnosis of Supabase authentication configuration.
    Does not expose sensitive credentials or tokens.
    """
    is_conf = settings.is_supabase_configured
    return AuthStatusResponse(
        supabase_configured=is_conf,
        supabase_url_configured=bool(settings.SUPABASE_URL),
        jwt_secret_configured=bool(settings.SUPABASE_JWT_SECRET),
        auth_provider="Supabase Auth",
        message=(
            "Supabase Auth is configured and active."
            if is_conf
            else "Supabase Auth credentials not detected. Add SUPABASE_URL and SUPABASE_ANON_KEY to .env."
        )
    )

@router.get("/auth/me", response_model=AuthenticatedUser, summary="Get Current Authenticated User")
def get_authenticated_user_profile(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> AuthenticatedUser:
    """
    Validates the caller's Supabase Bearer token and returns authenticated identity.
    Enforces that user identity is derived server-side from the token.
    """
    return current_user
