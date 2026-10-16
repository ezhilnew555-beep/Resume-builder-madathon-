"""
API Endpoints for CareerLens Reports and Progress Analytics (Phase 11).
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status, Response, HTTPException

from app.schemas.report import (
    ReportsListResponse,
    ReportSaveRequest,
    DetailedReportResponse,
    ReportComparisonResponse,
    ProgressAnalyticsSummaryResponse,
)
from app.services.report_service import report_service
from app.core.security import get_current_user, get_current_user_optional, AuthenticatedUser
from app.db.supabase import supabase_service

router = APIRouter()


@router.get(
    "/reports",
    response_model=ReportsListResponse,
    summary="List Saved Candidate Evaluation Reports"
)
def list_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    target_role: Optional[str] = Query(default=None),
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> ReportsListResponse:
    """
    Lists saved candidate reports. If user is authenticated, returns reports
    belonging to that user. Supports pagination and target role filtering.
    """
    user_id = current_user.id if current_user else None
    return report_service.list_reports(
        user_id=user_id,
        page=page,
        page_size=page_size,
        target_role=target_role
    )


@router.get(
    "/reports/user",
    response_model=ReportsListResponse,
    summary="List Authenticated Student Reports (Strict)"
)
async def list_authenticated_user_reports(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> ReportsListResponse:
    """
    Fetches analysis reports belonging strictly to the authenticated student (`auth.uid() = user_id`).
    Checks local persistent store and Supabase PostgreSQL if configured.
    """
    local_reports = report_service.list_reports(user_id=current_user.id)
    if local_reports.total > 0:
        return local_reports

    if not supabase_service.is_configured:
        return ReportsListResponse(
            reports=[],
            total=0,
            message="Supabase is not configured yet. Configure SUPABASE_URL to store & query candidate reports."
        )

    records = await supabase_service.get_user_reports(current_user.id)
    items = []
    for r in records:
        from app.schemas.report import ReportItem
        items.append(
            ReportItem(
                id=str(r["id"]),
                date=str(r.get("created_at", "")),
                resume_name=r.get("resume_filename") or "Uploaded Resume",
                target_role=r.get("target_role") or "Target Role",
                overall_score=int(r.get("overall_score") or 0),
                ats_score=int(r.get("ats_score") or r.get("overall_score") or 0),
                match_score=int(r.get("match_score") or 0),
                issues_count=int(r.get("issues_count") or 0),
                status=r.get("status", "completed"),
                report_title=r.get("report_title")
            )
        )
    return ReportsListResponse(
        reports=items,
        total=len(items),
        message=f"Found {len(items)} reports for authenticated student."
    )


@router.post(
    "/reports/save",
    response_model=DetailedReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save Analysis Report Snapshot"
)
def save_report(
    request: ReportSaveRequest,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> DetailedReportResponse:
    """
    Saves and snapshots a resume analysis into a permanent versioned assessment report.
    """
    user_id = current_user.id if current_user else None
    return report_service.save_report(request, user_id=user_id)


@router.get(
    "/reports/analytics/summary",
    response_model=ProgressAnalyticsSummaryResponse,
    summary="Get Career Progress Analytics Summary"
)
def get_analytics_summary(
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> ProgressAnalyticsSummaryResponse:
    """
    Aggregates overall progression metrics: scores over time, resolved issues,
    learning roadmap progress, and skills by evidence category.
    """
    user_id = current_user.id if current_user else None
    return report_service.get_analytics_summary(user_id=user_id)


@router.get(
    "/reports/{report_id}",
    response_model=DetailedReportResponse,
    summary="Get Detailed Assessment Report"
)
def get_report_by_id(
    report_id: str,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> DetailedReportResponse:
    """
    Retrieves full report details including CareerLens ATS-style score, component breakdowns,
    identified skills, structural audit, and actionable suggestions.
    """
    user_id = current_user.id if current_user else None
    return report_service.get_report(report_id, user_id=user_id)


@router.delete(
    "/reports/{report_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Saved Assessment Report"
)
def delete_report(
    report_id: str,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> dict:
    """
    Deletes a saved report. Does not delete underlying resume files or learning roadmaps.
    """
    user_id = current_user.id if current_user else None
    success = report_service.delete_report(report_id, user_id=user_id)
    return {"success": success, "message": f"Report '{report_id}' deleted successfully."}


@router.get(
    "/reports/{report_id}/compare/{other_report_id}",
    response_model=ReportComparisonResponse,
    summary="Compare Two Assessment Reports"
)
def compare_reports(
    report_id: str,
    other_report_id: str,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> ReportComparisonResponse:
    """
    Performs deterministic before-and-after metric comparison between two saved reports:
    score deltas, category shifts, resolved issues, and still-present warnings.
    """
    user_id = current_user.id if current_user else None
    return report_service.compare_reports(report_id, other_report_id, user_id=user_id)


@router.get(
    "/reports/{report_id}/export/pdf",
    summary="Export Assessment Report as Native PDF"
)
def export_report_pdf(
    report_id: str,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
) -> Response:
    """
    Exports the detailed report to native selectable vector PDF with CareerLens branding.
    """
    user_id = current_user.id if current_user else None
    pdf_bytes = report_service.export_report_pdf(report_id, user_id=user_id)
    filename = f"CareerLens_Report_{report_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\""
        }
    )
