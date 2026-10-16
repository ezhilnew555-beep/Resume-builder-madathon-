"""
API Endpoints for Personalized Learning Roadmap and Skill Development Tracker (Phase 10).
"""

from typing import Optional
from fastapi import APIRouter, Depends, status, HTTPException

from app.schemas.learning import (
    LearningRoadmapResponse,
    RoadmapGenerateRequest,
    TaskStatusUpdateRequest,
    RoadmapPreferencesUpdateRequest,
    RoadmapRefreshRequest,
    RoadmapProgressResponse,
    RoadmapTask,
)
from app.services.learning_service import learning_service
from app.core.security import get_current_user_optional, AuthenticatedUser

router = APIRouter()


@router.post(
    "/learning/roadmap/generate",
    response_model=LearningRoadmapResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Personalized Learning Roadmap"
)
def generate_roadmap(
    request: RoadmapGenerateRequest,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> LearningRoadmapResponse:
    """
    Generates a personalized, structured learning roadmap using available
    resume analysis, target job requirements, and profile verification evidence.
    """
    user_id = current_user.id if current_user else None
    return learning_service.generate_roadmap(request, user_id=user_id)


@router.get(
    "/learning/roadmap/current",
    response_model=LearningRoadmapResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current Active Roadmap"
)
def get_current_roadmap(
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> LearningRoadmapResponse:
    """
    Retrieves the authenticated user's current active learning roadmap,
    or generates an initial personalized roadmap if none exists.
    """
    user_id = current_user.id if current_user else None
    return learning_service.get_current_roadmap(user_id=user_id)


@router.get(
    "/learning/roadmap/{roadmap_id}",
    response_model=LearningRoadmapResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Roadmap By ID"
)
def get_roadmap_by_id(
    roadmap_id: str,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> LearningRoadmapResponse:
    """
    Retrieves a specific learning roadmap by ID, with user isolation checks.
    """
    user_id = current_user.id if current_user else None
    return learning_service.get_roadmap(roadmap_id, user_id=user_id)


@router.get(
    "/learning/roadmap/{roadmap_id}/tasks/{task_id}",
    response_model=RoadmapTask,
    status_code=status.HTTP_200_OK,
    summary="Get Roadmap Task Details"
)
def get_task_details(
    roadmap_id: str,
    task_id: str,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> RoadmapTask:
    """
    Retrieves individual task instructions, resources, deliverables, and progress notes.
    """
    user_id = current_user.id if current_user else None
    roadmap = learning_service.get_roadmap(roadmap_id, user_id=user_id)
    for task in roadmap.all_tasks:
        if task.id == task_id:
            return task
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task '{task_id}' not found in roadmap '{roadmap_id}'."
    )


@router.patch(
    "/learning/roadmap/{roadmap_id}/tasks/{task_id}",
    response_model=LearningRoadmapResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Task Status & Notes"
)
def update_task_status(
    roadmap_id: str,
    task_id: str,
    update_data: TaskStatusUpdateRequest,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> LearningRoadmapResponse:
    """
    Updates the self-reported status of a task ('not_started', 'in_progress', 'completed'),
    persists candidate notes, and recomputes milestone completion metrics.
    """
    user_id = current_user.id if current_user else None
    return learning_service.update_task_status(roadmap_id, task_id, update_data, user_id=user_id)


@router.get(
    "/learning/roadmap/{roadmap_id}/progress",
    response_model=RoadmapProgressResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Roadmap Progress Statistics"
)
def get_progress_statistics(
    roadmap_id: str,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> RoadmapProgressResponse:
    """
    Returns high-level completion statistics, logged hours, remaining hours,
    and covered skills for the roadmap.
    """
    user_id = current_user.id if current_user else None
    return learning_service.get_progress_stats(roadmap_id, user_id=user_id)


@router.patch(
    "/learning/roadmap/{roadmap_id}/preferences",
    response_model=LearningRoadmapResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Study Time & Target Weeks"
)
def update_roadmap_preferences(
    roadmap_id: str,
    update_data: RoadmapPreferencesUpdateRequest,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> LearningRoadmapResponse:
    """
    Adjusts weekly available study hours or target completion duration.
    """
    user_id = current_user.id if current_user else None
    return learning_service.update_preferences(roadmap_id, update_data, user_id=user_id)


@router.post(
    "/learning/roadmap/{roadmap_id}/refresh",
    response_model=LearningRoadmapResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh Roadmap (Preserving Progress)"
)
def refresh_roadmap(
    roadmap_id: str,
    refresh_data: RoadmapRefreshRequest,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> LearningRoadmapResponse:
    """
    Refreshes the roadmap when job description or resume analysis changes.
    Preserves all previously completed tasks and user notes.
    """
    user_id = current_user.id if current_user else None
    return learning_service.refresh_roadmap(roadmap_id, refresh_data, user_id=user_id)
