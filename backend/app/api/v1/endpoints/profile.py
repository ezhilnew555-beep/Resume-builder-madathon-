from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.profile import (
    ProfileResponse,
    ProfileUpdateRequest,
    ProfileConnectionUpdate,
    ProfileConnectionItem,
    ProfileConnectionsResponse,
    GitHubConnectRequest,
)
from app.core.security import get_current_user, get_current_user_optional, AuthenticatedUser
from app.services.profile_connection_service import profile_connection_service
from app.db.supabase import supabase_service

router = APIRouter()

@router.get("/profile/me", response_model=ProfileResponse, summary="Get Current Student Profile")
async def get_my_profile(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> ProfileResponse:
    """
    Retrieves profile record for the authenticated student from Supabase PostgreSQL.
    Enforces isolation: student can only fetch their own profile matching auth.uid().
    """
    if not supabase_service.is_configured:
        # Return fallback profile object reflecting token identity with setup notice
        return ProfileResponse(
            id=current_user.id,
            email=current_user.email,
            full_name=None,
            education=None,
            target_role=None
        )

    profile_data = await supabase_service.get_profile(current_user.id)
    if not profile_data:
        # User is authenticated in auth.users but has not filled in their profile record yet
        return ProfileResponse(
            id=current_user.id,
            email=current_user.email,
            full_name=None,
            education=None,
            target_role=None
        )

    return ProfileResponse(
        id=profile_data["id"],
        email=current_user.email,
        full_name=profile_data.get("full_name"),
        education=profile_data.get("education"),
        target_role=profile_data.get("target_role"),
        created_at=profile_data.get("created_at"),
        updated_at=profile_data.get("updated_at")
    )

@router.put("/profile/me", response_model=ProfileResponse, summary="Update Current Student Profile")
async def update_my_profile(
    request: ProfileUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> ProfileResponse:
    """
    Updates profile record for the authenticated student.
    Strictly forces user_id to match current_user.id from the token.
    """
    if not supabase_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase database is not configured. Add SUPABASE_URL and SUPABASE_ANON_KEY to .env to persist profiles."
        )

    update_dict = request.model_dump(exclude_unset=True)
    saved = await supabase_service.upsert_profile(current_user.id, update_dict)
    if not saved:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile record in Supabase PostgreSQL."
        )

    return ProfileResponse(
        id=saved["id"],
        email=current_user.email,
        full_name=saved.get("full_name"),
        education=saved.get("education"),
        target_role=saved.get("target_role"),
        created_at=saved.get("created_at"),
        updated_at=saved.get("updated_at")
    )

# ----------------------------------------------------------------------
# PHASE 7: PROFILE CONNECTIONS ENDPOINTS
# ----------------------------------------------------------------------

@router.get(
    "/profiles/connections",
    response_model=ProfileConnectionsResponse,
    summary="Get Connected External Profiles"
)
@router.get(
    "/profile/connections",
    response_model=ProfileConnectionsResponse,
    include_in_schema=False
)
def get_profile_connections(
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> ProfileConnectionsResponse:
    """
    Lists external developer profiles and their current sync/verification state.
    """
    user_id = current_user.id if current_user else None
    conns = profile_connection_service.get_user_connections(user_id=user_id)
    connected_count = len([c for c in conns if c.get("status") == "connected"])
    return ProfileConnectionsResponse(
        connections=[ProfileConnectionItem(**c) for c in conns],
        total_connected=connected_count,
        message=f"{connected_count} external profiles connected."
    )

@router.post(
    "/profiles/connections",
    response_model=ProfileConnectionItem,
    summary="Link or Update an External Profile"
)
@router.post(
    "/profile/connections",
    response_model=ProfileConnectionItem,
    include_in_schema=False
)
def update_profile_connection(
    request: ProfileConnectionUpdate,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> ProfileConnectionItem:
    """
    Links an external profile (GitHub, LeetCode, Portfolio, Kaggle, HackerRank, LinkedIn)
    and verifies access without requesting credentials.
    """
    user_id = current_user.id if current_user else None
    result = profile_connection_service.connect_profile(
        platform_id=request.platform_id,
        username_or_url=request.username_or_url,
        user_id=user_id
    )
    return ProfileConnectionItem(**result)

@router.post(
    "/profiles/github/connect",
    response_model=ProfileConnectionItem,
    summary="Connect GitHub Account"
)
def connect_github_profile(
    request: GitHubConnectRequest,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> ProfileConnectionItem:
    """
    Explicit shortcut to connect a public GitHub account or profile URL.
    Validates host, checks public repositories, languages, and test suites.
    """
    user_id = current_user.id if current_user else None
    result = profile_connection_service.connect_profile(
        platform_id="github",
        username_or_url=request.username_or_url,
        user_id=user_id
    )
    return ProfileConnectionItem(**result)

@router.delete(
    "/profiles/connections/{platform_id}",
    status_code=status.HTTP_200_OK,
    summary="Disconnect an External Profile"
)
@router.delete(
    "/profile/connections/{platform_id}",
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
def disconnect_profile(
    platform_id: str,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
):
    """
    Disconnects and removes stored metadata for the specified platform.
    """
    user_id = current_user.id if current_user else None
    profile_connection_service.disconnect_profile(platform_id, user_id=user_id)
    return {"message": f"Successfully disconnected {platform_id} profile."}
