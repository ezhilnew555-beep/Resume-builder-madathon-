from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import dashboard_service
from app.core.security import get_current_user_optional, AuthenticatedUser

router = APIRouter()

@router.get("/dashboard", response_model=DashboardResponse, summary="Demonstration or User Dashboard Data")
def get_dashboard(
    demo: bool = Query(default=False, description="Explicitly request demonstration data"),
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> DashboardResponse:
    """
    Returns dashboard metrics. If an authenticated user is present and demo=False,
    returns the user's real database-backed metrics or a clean initial state.
    If unauthenticated or demo=True, returns baseline demonstration data.
    """
    if current_user and not demo:
        return dashboard_service.get_user_dashboard(user_id=current_user.id, user_email=current_user.email)
    return dashboard_service.get_demonstration_dashboard()
