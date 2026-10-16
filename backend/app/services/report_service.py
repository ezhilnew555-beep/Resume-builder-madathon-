"""
Reports and Progress Analytics Service for CareerLens (Phase 11).
Handles persistent report storage, detailed analysis retrieval, before-and-after comparison,
progress analytics aggregation, and native PDF report export.
"""

import uuid
import datetime
import fitz  # PyMuPDF
from typing import Dict, Any, List, Optional, Tuple
from fastapi import HTTPException, status

from app.schemas.report import (
    ReportItem,
    ReportsListResponse,
    ReportSaveRequest,
    DetailedReportResponse,
    ReportComparisonResponse,
    ProgressAnalyticsSummaryResponse,
)
from app.services.resume_parser import resume_store
from app.services.resume_analysis_service import resume_analysis_service, analysis_store
from app.services.job_service import job_match_store
from app.services.learning_service import learning_roadmap_store
from app.services.evidence_verification_service import verification_store


class ReportStore:
    """
    In-memory storage for saved analysis reports with user ownership enforcement.
    """
    def __init__(self):
        self._reports: Dict[str, Dict[str, Any]] = {}

    def save(self, report_id: str, data: Dict[str, Any], user_id: Optional[str] = None) -> None:
        self._reports[report_id] = {
            **data,
            "id": report_id,
            "user_id": user_id,
        }

    def get(self, report_id: str) -> Optional[Dict[str, Any]]:
        return self._reports.get(report_id)

    def delete(self, report_id: str, user_id: Optional[str] = None) -> bool:
        self.check_ownership(report_id, user_id)
        if report_id in self._reports:
            del self._reports[report_id]
            return True
        return False

    def check_ownership(self, report_id: str, user_id: Optional[str]) -> Dict[str, Any]:
        record = self.get(report_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report with ID '{report_id}' not found."
            )
        owner = record.get("user_id")
        if owner and (not user_id or user_id != owner):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: you do not have permission to view or modify this report."
            )
        return record

    def list_reports(
        self,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        target_role: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        all_recs = []
        for r in self._reports.values():
            r_owner = r.get("user_id")
            if user_id:
                if r_owner != user_id:
                    continue
            if target_role and target_role.strip():
                if target_role.lower() not in r.get("target_role", "").lower():
                    continue
            all_recs.append(r)

        # Sort descending by date
        all_recs.sort(key=lambda x: x.get("date", ""), reverse=True)
        total = len(all_recs)

        start = (page - 1) * page_size
        end = start + page_size
        return all_recs[start:end], total


report_store = ReportStore()


class ReportService:
    @classmethod
    def list_reports(
        cls,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        target_role: Optional[str] = None
    ) -> ReportsListResponse:
        records, total = report_store.list_reports(
            user_id=user_id,
            page=page,
            page_size=page_size,
            target_role=target_role
        )

        items = []
        for r in records:
            items.append(
                ReportItem(
                    id=r["id"],
                    date=r.get("date", ""),
                    resume_name=r.get("resume_name", "Uploaded Resume"),
                    target_role=r.get("target_role", "Software Engineer"),
                    overall_score=int(r.get("overall_score", 0)),
                    ats_score=int(r.get("ats_score", 0)),
                    match_score=int(r.get("match_score", 0)),
                    issues_count=int(r.get("issues_count", 0)),
                    status=r.get("status", "completed"),
                    report_title=r.get("report_title")
                )
            )

        msg = "Reports retrieved successfully." if total > 0 else "No stored reports found. Run resume analysis to create a report."
        return ReportsListResponse(
            reports=items,
            total=total,
            page=page,
            page_size=page_size,
            message=msg
        )

    @classmethod
    def save_report(
        cls,
        request: ReportSaveRequest,
        user_id: Optional[str] = None
    ) -> DetailedReportResponse:
        """
        Creates and persists a comprehensive assessment report from real analysis and job match data.
        """
        # 1. Fetch Analysis
        resume_record = resume_store.check_ownership(request.resume_id, user_id)
        filename = resume_record.get("filename", "resume.pdf")

        analysis_record = analysis_store.get(request.resume_id)
        if not analysis_record:
            analysis_record = resume_analysis_service.analyze_resume(request.resume_id, user_id=user_id)

        target_role = (request.target_role or "Software Engineer").strip()
        overall_score = int(round(analysis_record.get("overall_score", 0)))
        readiness_tier = analysis_record.get("readiness_tier", "Developing")
        component_scores = analysis_record.get("component_scores", {})
        scoring_rationale = analysis_record.get("scoring_rationale", {})
        extracted_skills = analysis_record.get("extracted_skills", {})
        detected_sections = analysis_record.get("detected_sections", [])
        missing_sections = analysis_record.get("missing_sections", [])
        findings = analysis_record.get("findings", [])
        bullet_evals = analysis_record.get("bullet_point_evaluations", [])

        # 2. Link Job Match if available
        job_match_data = None
        match_score = 0
        if request.job_match_id:
            m_rec = job_match_store.get(request.job_match_id)
            if m_rec:
                target_role = m_rec.get("target_role", target_role)
                match_score = int(round(m_rec.get("overall_match_score", 0)))
                job_match_data = {
                    "match_id": m_rec.get("match_id"),
                    "target_role": target_role,
                    "company_name": m_rec.get("company_name"),
                    "overall_match_score": match_score,
                    "matching_skills_count": len(m_rec.get("matching_skills", [])),
                    "missing_skills_count": len(m_rec.get("missing_skills", [])),
                }

        # 3. Link Roadmap if available
        roadmap_summary = None
        if user_id:
            user_roadmap = learning_roadmap_store.get_by_user(user_id)
            if user_roadmap:
                roadmap_summary = {
                    "roadmap_id": user_roadmap.get("id"),
                    "completion_percentage": user_roadmap.get("completion_percentage", 0),
                    "completed_tasks": user_roadmap.get("completed_tasks", 0),
                    "total_tasks": user_roadmap.get("total_tasks", 0),
                }

        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%b %d, %Y")
        report_id = f"rep-{uuid.uuid4().hex[:12]}"
        report_title = request.report_title or f"Audit: {filename} ({target_role})"

        report_dict = {
            "id": report_id,
            "user_id": user_id,
            "report_title": report_title,
            "date": now_str,
            "resume_name": filename,
            "resume_id": request.resume_id,
            "target_role": target_role,
            "overall_score": overall_score,
            "readiness_tier": readiness_tier,
            "ats_score": overall_score,
            "match_score": match_score,
            "status": "completed",
            "issues_count": len(findings),
            "component_scores": component_scores,
            "scoring_rationale": scoring_rationale,
            "extracted_skills": extracted_skills,
            "detected_sections": detected_sections,
            "missing_sections": missing_sections,
            "findings": findings,
            "bullet_evaluations": bullet_evals,
            "job_match_summary": job_match_data,
            "roadmap_summary": roadmap_summary,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        report_store.save(report_id, report_dict, user_id=user_id)
        return DetailedReportResponse(**report_dict)

    @classmethod
    def get_report(cls, report_id: str, user_id: Optional[str] = None) -> DetailedReportResponse:
        record = report_store.check_ownership(report_id, user_id)
        return DetailedReportResponse(**record)

    @classmethod
    def delete_report(cls, report_id: str, user_id: Optional[str] = None) -> bool:
        return report_store.delete(report_id, user_id)

    @classmethod
    def compare_reports(
        cls,
        report_id_a: str,
        report_id_b: str,
        user_id: Optional[str] = None
    ) -> ReportComparisonResponse:
        """
        Calculates metric differences, resolved issues, and category improvements
        between two authorized reports.
        """
        rec_a = report_store.check_ownership(report_id_a, user_id)
        rec_b = report_store.check_ownership(report_id_b, user_id)

        # Check compatibility
        role_a = rec_a.get("target_role", "").strip()
        role_b = rec_b.get("target_role", "").strip()
        is_compatible = True
        compat_notice = None

        if role_a and role_b and role_a.lower() != role_b.lower():
            is_compatible = False
            compat_notice = (
                f"Caution: Report A was evaluated for '{role_a}' while Report B was evaluated for '{role_b}'. "
                "Differences reflect distinct target role criteria rather than pure document quality changes."
            )

        score_a = int(rec_a.get("overall_score", 0))
        score_b = int(rec_b.get("overall_score", 0))
        score_delta = score_b - score_a

        # Category Deltas
        cat_a = rec_a.get("component_scores", {})
        cat_b = rec_b.get("component_scores", {})
        category_deltas = {}
        all_keys = set(cat_a.keys()).union(set(cat_b.keys()))
        for k in all_keys:
            val_a = cat_a.get(k, 0)
            val_b = cat_b.get(k, 0)
            category_deltas[k] = {
                "before": val_a,
                "after": val_b,
                "delta": val_b - val_a
            }

        # Issues Comparison
        findings_a = rec_a.get("findings", [])
        findings_b = rec_b.get("findings", [])

        titles_b = {f.get("title", "").strip().lower() for f in findings_b}
        titles_a = {f.get("title", "").strip().lower() for f in findings_a}

        issues_resolved = [f for f in findings_a if f.get("title", "").strip().lower() not in titles_b]
        issues_still_present = [f for f in findings_a if f.get("title", "").strip().lower() in titles_b]
        issues_newly_identified = [f for f in findings_b if f.get("title", "").strip().lower() not in titles_a]

        # Job Match Delta
        job_match_delta = None
        match_a = rec_a.get("match_score", 0)
        match_b = rec_b.get("match_score", 0)
        if match_a or match_b:
            job_match_delta = {
                "score_before": match_a,
                "score_after": match_b,
                "delta": match_b - match_a
            }

        # Recommended next actions
        next_actions = []
        if issues_still_present:
            top_issue = issues_still_present[0]
            next_actions.append(f"Address lingering finding: {top_issue.get('title', 'Resume formatting issue')}.")
        if score_b < 75:
            next_actions.append("Refine bullet points using STAR format (action verb, tool, and measurable metric).")
        if issues_newly_identified:
            next_actions.append(f"Resolve newly flagged item: {issues_newly_identified[0].get('title')}.")
        if not next_actions:
            next_actions.append("Continue monitoring skill alignment as target job descriptions evolve.")

        return ReportComparisonResponse(
            report_a_id=report_id_a,
            report_b_id=report_id_b,
            date_a=rec_a.get("date", "Report A"),
            date_b=rec_b.get("date", "Report B"),
            title_a=rec_a.get("report_title") or f"Evaluation {rec_a.get('date')}",
            title_b=rec_b.get("report_title") or f"Evaluation {rec_b.get('date')}",
            score_a=score_a,
            score_b=score_b,
            score_delta=score_delta,
            is_compatible=is_compatible,
            compatibility_notice=compat_notice,
            category_deltas=category_deltas,
            issues_resolved=issues_resolved,
            issues_still_present=issues_still_present,
            issues_newly_identified=issues_newly_identified,
            job_match_delta=job_match_delta,
            recommended_next_actions=next_actions
        )

    @classmethod
    def get_analytics_summary(cls, user_id: Optional[str] = None) -> ProgressAnalyticsSummaryResponse:
        """
        Aggregates career progress analytics over time using real saved report and roadmap data.
        """
        all_recs, total = report_store.list_reports(user_id=user_id, page=1, page_size=100)

        if not all_recs:
            return ProgressAnalyticsSummaryResponse(
                total_analyses_completed=0,
                has_historical_data=False
            )

        # Sort ascending for chronological trend
        sorted_recs = sorted(all_recs, key=lambda x: x.get("created_at", x.get("date", "")))

        score_progression = [
            {
                "report_id": r["id"],
                "date": r.get("date", ""),
                "score": int(r.get("overall_score", 0)),
                "ats_score": int(r.get("ats_score", 0)),
                "match_score": int(r.get("match_score", 0)),
                "target_role": r.get("target_role", ""),
                "title": r.get("report_title") or r.get("resume_name", "")
            }
            for r in sorted_recs
        ]

        latest_rec = sorted_recs[-1]
        prev_rec = sorted_recs[-2] if len(sorted_recs) >= 2 else None

        latest_score = int(latest_rec.get("overall_score", 0))
        previous_score = int(prev_rec.get("overall_score", 0)) if prev_rec else None

        # Cumulative resolved issues across history
        issues_resolved_total = 0
        if len(sorted_recs) >= 2:
            first_findings = {f.get("title", "").strip().lower() for f in sorted_recs[0].get("findings", [])}
            latest_findings = {f.get("title", "").strip().lower() for f in latest_rec.get("findings", [])}
            issues_resolved_total = len(first_findings - latest_findings)

        current_open_issues = len(latest_rec.get("findings", []))

        # Roadmap Progress Stats from Phase 10
        roadmap_completed = 0
        roadmap_total = 0
        roadmap_pct = 0
        if user_id:
            u_roadmap = learning_roadmap_store.get_by_user(user_id)
            if u_roadmap:
                roadmap_completed = u_roadmap.get("completed_tasks", 0)
                roadmap_total = u_roadmap.get("total_tasks", 0)
                roadmap_pct = u_roadmap.get("completion_percentage", 0)

        # Distinct Skills by Evidence Type
        # 1. Self reported: completed roadmap tasks
        # 2. Resume evidence: detected skills from latest report
        # 3. Independently verified: from verification_store
        resume_skills_count = 0
        for grp in latest_rec.get("extracted_skills", {}).values():
            if isinstance(grp, list):
                resume_skills_count += len(grp)

        verified_skills_count = 0
        if user_id:
            for v_rec in verification_store._verifications.values():
                if v_rec.get("user_id") == user_id:
                    verified_skills_count += len(v_rec.get("verified_skills", []))

        return ProgressAnalyticsSummaryResponse(
            total_analyses_completed=total,
            latest_score=latest_score,
            previous_score=previous_score,
            score_progression=score_progression,
            issues_resolved_total=max(0, issues_resolved_total),
            current_open_issues=current_open_issues,
            roadmap_tasks_completed=roadmap_completed,
            roadmap_tasks_total=roadmap_total,
            roadmap_completion_pct=roadmap_pct,
            skills_by_evidence_type={
                "self_reported": roadmap_completed,
                "resume_evidence": resume_skills_count,
                "independently_verified": verified_skills_count
            },
            target_role=latest_rec.get("target_role"),
            has_historical_data=len(sorted_recs) >= 2
        )

    @classmethod
    def export_report_pdf(cls, report_id: str, user_id: Optional[str] = None) -> bytes:
        """
        Renders a native, selectable vector PDF using PyMuPDF (fitz)
        detailing the assessment findings, score breakdown, and recommendations.
        """
        rec = report_store.check_ownership(report_id, user_id)

        doc = fitz.open()
        page = doc.new_page(width=612, height=792)  # 8.5 x 11 inches
        cursor_y = 50
        margin_x = 54
        usable_width = 504

        def check_overflow(needed: float):
            nonlocal page, cursor_y
            if cursor_y + needed > 740:
                page = doc.new_page(width=612, height=792)
                cursor_y = 50

        # Header Branding
        page.draw_rect(fitz.Rect(margin_x, cursor_y, margin_x + usable_width, cursor_y + 35), color=(0.09, 0.11, 0.15), fill=(0.09, 0.11, 0.15))
        page.insert_text(fitz.Point(margin_x + 12, cursor_y + 23), "CAREERLENS ASSESSMENT REPORT", fontsize=14, fontname="helv", color=(1, 1, 1))
        cursor_y += 50

        # Metadata Row
        page.insert_text(fitz.Point(margin_x, cursor_y), f"Document: {rec.get('resume_name', 'Resume')}", fontsize=10, fontname="helv", color=(0.2, 0.2, 0.2))
        page.insert_text(fitz.Point(margin_x + 300, cursor_y), f"Date: {rec.get('date', 'Oct 2026')}", fontsize=10, fontname="helv", color=(0.4, 0.4, 0.4))
        cursor_y += 18
        page.insert_text(fitz.Point(margin_x, cursor_y), f"Target Role: {rec.get('target_role', 'Software Engineer')}", fontsize=10, fontname="helv", color=(0.2, 0.2, 0.2))
        cursor_y += 24

        # Overall Score Card
        score_box_height = 55
        page.draw_rect(fitz.Rect(margin_x, cursor_y, margin_x + usable_width, cursor_y + score_box_height), color=(0.85, 0.88, 0.95), fill=(0.95, 0.96, 0.99))
        score_val = rec.get("overall_score", 0)
        page.insert_text(fitz.Point(margin_x + 16, cursor_y + 24), "CareerLens ATS-Style Estimate:", fontsize=11, fontname="helv", color=(0.15, 0.2, 0.35))
        page.insert_text(fitz.Point(margin_x + 16, cursor_y + 44), f"{score_val} / 100 ({rec.get('readiness_tier', 'Standard')})", fontsize=16, fontname="helv", color=(0.08, 0.35, 0.25))
        cursor_y += score_box_height + 20

        # Component Scores
        check_overflow(70)
        page.insert_text(fitz.Point(margin_x, cursor_y), "SCORE BREAKDOWN BY COMPONENT", fontsize=11, fontname="helv", color=(0.1, 0.1, 0.1))
        cursor_y += 6
        page.draw_line(fitz.Point(margin_x, cursor_y), fitz.Point(margin_x + usable_width, cursor_y), color=(0.8, 0.8, 0.8), width=1)
        cursor_y += 16

        comp_scores = rec.get("component_scores", {})
        for cat_name, val in comp_scores.items():
            check_overflow(16)
            cat_display = cat_name.replace("_", " ").title()
            page.insert_text(fitz.Point(margin_x + 10, cursor_y), f"• {cat_display}: {val} / 100", fontsize=9.5, fontname="helv", color=(0.25, 0.25, 0.25))
            cursor_y += 15
        cursor_y += 10

        # Key Findings
        findings = rec.get("findings", [])
        if findings:
            check_overflow(50)
            page.insert_text(fitz.Point(margin_x, cursor_y), "IDENTIFIED FINDINGS & ACTIONABLE RECOMMENDATIONS", fontsize=11, fontname="helv", color=(0.1, 0.1, 0.1))
            cursor_y += 6
            page.draw_line(fitz.Point(margin_x, cursor_y), fitz.Point(margin_x + usable_width, cursor_y), color=(0.8, 0.8, 0.8), width=1)
            cursor_y += 16

            for f in findings[:6]:
                check_overflow(35)
                f_title = f.get("title", "Finding")
                f_desc = f.get("description", "")
                f_type = f.get("severity", f.get("type", "note")).upper()
                page.insert_text(fitz.Point(margin_x + 10, cursor_y), f"[{f_type}] {f_title}", fontsize=9.5, fontname="helv", color=(0.15, 0.2, 0.5))
                cursor_y += 13
                if f_desc:
                    page.insert_text(fitz.Point(margin_x + 20, cursor_y), f_desc[:90] + ("..." if len(f_desc) > 90 else ""), fontsize=8.5, fontname="helv", color=(0.4, 0.4, 0.4))
                    cursor_y += 14

        # Disclaimer
        check_overflow(45)
        cursor_y = max(cursor_y + 10, 710)
        page.draw_line(fitz.Point(margin_x, cursor_y), fitz.Point(margin_x + usable_width, cursor_y), color=(0.9, 0.9, 0.9), width=0.5)
        cursor_y += 14
        disclaimer = (
            "CareerLens Disclaimer: Assessment scores represent an educational ATS-style estimate. CareerLens does not claim "
            "to duplicate proprietary employer algorithms or guarantee interview invitations."
        )
        page.insert_text(fitz.Point(margin_x, cursor_y), disclaimer[:110], fontsize=7, fontname="helv", color=(0.5, 0.5, 0.5))
        page.insert_text(fitz.Point(margin_x, cursor_y + 9), disclaimer[110:], fontsize=7, fontname="helv", color=(0.5, 0.5, 0.5))

        pdf_bytes = doc.write()
        doc.close()
        return pdf_bytes


report_service = ReportService()
