import React, { useState, useEffect, useCallback } from 'react';
import {
  FileText,
  TrendingUp,
  Download,
  Eye,
  Trash2,
  GitCompare,
  BarChart3,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles,
  Info,
  RefreshCw,
  Filter,
  ArrowRight,
  ShieldCheck,
  Award,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { ProgressBar } from '../components/common/ProgressBar';
import { Toast } from '../components/common/Toast';
import type { ToastMessage } from '../components/common/Toast';
import { apiService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import type {
  LiveReportItem,
  LiveDetailedReportResponse,
  LiveReportComparisonResponse,
  LiveProgressAnalyticsSummaryResponse,
} from '../types';

export const ReportsPage: React.FC = () => {
  const { user, getAccessToken } = useAuth();

  // Navigation Tabs: 'history' | 'detail' | 'compare' | 'analytics'
  const [activeTab, setActiveTab] = useState<'history' | 'detail' | 'compare' | 'analytics'>('history');

  // Report History State
  const [reports, setReports] = useState<LiveReportItem[]>([]);
  const [totalReports, setTotalReports] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [roleFilter, setRoleFilter] = useState('');
  const [isLoadingReports, setIsLoadingReports] = useState(true);
  const [toast, setToast] = useState<ToastMessage | null>(null);

  // Detailed Report View State
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [detailedReport, setDetailedReport] = useState<LiveDetailedReportResponse | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  // Comparison State
  const [compareReportA, setCompareReportA] = useState<string>('');
  const [compareReportB, setCompareReportB] = useState<string>('');
  const [comparisonResult, setComparisonResult] = useState<LiveReportComparisonResponse | null>(null);
  const [isComparing, setIsComparing] = useState(false);
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);

  // Progress Analytics State
  const [analytics, setAnalytics] = useState<LiveProgressAnalyticsSummaryResponse | null>(null);
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(false);

  // Export PDF State
  const [isExportingPdf, setIsExportingPdf] = useState(false);

  // Save Current Session Report State
  const [isSavingCurrent, setIsSavingCurrent] = useState(false);
  const latestResumeId = sessionStorage.getItem('latest_resume_id');

  // Load Reports History
  const loadReports = useCallback(async (page: number = 1) => {
    setIsLoadingReports(true);
    try {
      const token = user ? await getAccessToken() : null;
      const res = await apiService.fetchSavedReportsLive(
        { page, page_size: 10, target_role: roleFilter || undefined },
        token
      );
      setReports(res.reports);
      setTotalReports(res.total);
      setCurrentPage(res.page);
    } catch (err: any) {
      console.error('Failed to load reports:', err);
      setToast({
        id: Math.random().toString(),
        type: 'error',
        title: 'Loading Error',
        message: err?.message || 'Could not fetch saved reports.',
      });
    } finally {
      setIsLoadingReports(false);
    }
  }, [user, getAccessToken, roleFilter]);

  // Load Detailed Report
  const loadDetailedReport = async (reportId: string) => {
    setSelectedReportId(reportId);
    setIsLoadingDetail(true);
    setActiveTab('detail');
    try {
      const token = user ? await getAccessToken() : null;
      const detail = await apiService.fetchDetailedReportLive(reportId, token);
      setDetailedReport(detail);
    } catch (err: any) {
      setToast({
        id: Math.random().toString(),
        type: 'error',
        title: 'Report Error',
        message: err?.message || 'Failed to retrieve detailed report.',
      });
    } finally {
      setIsLoadingDetail(false);
    }
  };

  // Run Comparison
  const handleRunComparison = async (idA: string, idB: string) => {
    if (!idA || !idB || idA === idB) {
      setToast({
        id: Math.random().toString(),
        type: 'error',
        title: 'Select Two Distinct Reports',
        message: 'Please choose two different reports to perform a comparative audit.',
      });
      return;
    }

    setIsComparing(true);
    setActiveTab('compare');
    try {
      const token = user ? await getAccessToken() : null;
      const result = await apiService.compareReportsLive(idA, idB, token);
      setComparisonResult(result);
    } catch (err: any) {
      setToast({
        id: Math.random().toString(),
        type: 'error',
        title: 'Comparison Failed',
        message: err?.message || 'Could not compare reports.',
      });
    } finally {
      setIsComparing(false);
    }
  };

  // Load Progress Analytics
  const loadAnalytics = useCallback(async () => {
    setIsLoadingAnalytics(true);
    try {
      const token = user ? await getAccessToken() : null;
      const data = await apiService.fetchProgressAnalyticsSummaryLive(token);
      setAnalytics(data);
    } catch (err: any) {
      console.warn('Could not load analytics:', err);
    } finally {
      setIsLoadingAnalytics(false);
    }
  }, [user, getAccessToken]);

  useEffect(() => {
    loadReports(currentPage);
  }, [loadReports, currentPage]);

  useEffect(() => {
    if (activeTab === 'analytics') {
      loadAnalytics();
    }
  }, [activeTab, loadAnalytics]);

  // Delete a Report
  const handleDeleteReport = async (reportId: string) => {
    if (!window.confirm('Are you sure you want to delete this saved evaluation report?')) {
      return;
    }
    try {
      const token = user ? await getAccessToken() : null;
      await apiService.deleteReportLive(reportId, token);
      setToast({
        id: Math.random().toString(),
        type: 'success',
        title: 'Report Deleted',
        message: 'Evaluation report removed from your history.',
      });
      loadReports(currentPage);
      if (selectedReportId === reportId) {
        setDetailedReport(null);
        setSelectedReportId(null);
      }
    } catch (err: any) {
      setToast({
        id: Math.random().toString(),
        type: 'error',
        title: 'Delete Failed',
        message: err?.message || 'Could not delete report.',
      });
    }
  };

  // Export PDF
  const handleExportPdf = async (reportId: string) => {
    setIsExportingPdf(true);
    try {
      const token = user ? await getAccessToken() : null;
      const blob = await apiService.exportReportPdfBlobLive(reportId, token);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `CareerLens_Report_${reportId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      setToast({
        id: Math.random().toString(),
        type: 'success',
        title: 'PDF Export Downloaded',
        message: 'Generated native vector PDF report with CareerLens assessment breakdown.',
      });
    } catch (err: any) {
      setToast({
        id: Math.random().toString(),
        type: 'error',
        title: 'Export Failed',
        message: err?.message || 'Failed to generate report PDF.',
      });
    } finally {
      setIsExportingPdf(false);
    }
  };

  // Save current active session analysis as a permanent report
  const handleSaveCurrentSessionReport = async () => {
    if (!latestResumeId) return;
    setIsSavingCurrent(true);
    try {
      const token = user ? await getAccessToken() : null;
      const saved = await apiService.saveReportLive(
        {
          resume_id: latestResumeId,
          target_role: 'Full Stack Software Engineer',
          report_title: `Audit Snapshot (${new Date().toLocaleDateString()})`,
        },
        token
      );
      setToast({
        id: Math.random().toString(),
        type: 'success',
        title: 'Audit Report Saved',
        message: `Saved report #${saved.id} with ATS-style score ${saved.overall_score}/100.`,
      });
      loadReports(1);
    } catch (err: any) {
      setToast({
        id: Math.random().toString(),
        type: 'error',
        title: 'Save Failed',
        message: err?.message || 'Could not save report.',
      });
    } finally {
      setIsSavingCurrent(false);
    }
  };

  // Toggle selection for comparison
  const toggleSelectForCompare = (id: string) => {
    setSelectedForCompare((prev) => {
      if (prev.includes(id)) {
        return prev.filter((item) => item !== id);
      }
      if (prev.length >= 2) {
        return [prev[1], id];
      }
      return [...prev, id];
    });
  };

  const getReadinessBadgeVariant = (score: number) => {
    if (score >= 80) return 'success';
    if (score >= 65) return 'info';
    if (score >= 50) return 'warning';
    return 'danger';
  };

  return (
    <div className="space-y-6">
      {toast && <Toast toast={toast} onClose={() => setToast(null)} />}

      {/* Top Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
              Phase 11: Reports & Analytics
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight mt-1">
            Assessment Reports & Career Progression
          </h1>
          <p className="text-slate-600 text-xs sm:text-sm mt-0.5">
            Audit historical resume evaluations, compare metric improvements before and after editing, and track long-term readiness.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {latestResumeId && (
            <Button
              variant="primary"
              size="sm"
              onClick={handleSaveCurrentSessionReport}
              disabled={isSavingCurrent}
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              <Sparkles className="w-4 h-4 mr-1.5" />
              {isSavingCurrent ? 'Saving...' : 'Save Current Analysis'}
            </Button>
          )}
        </div>
      </div>

      {/* Sub-Navigation Tabs */}
      <div className="flex items-center border-b border-slate-200 text-xs sm:text-sm font-medium gap-2 overflow-x-auto pb-px">
        <button
          onClick={() => setActiveTab('history')}
          className={`flex items-center gap-2 px-4 py-2.5 border-b-2 font-semibold transition-colors whitespace-nowrap cursor-pointer ${
            activeTab === 'history'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <FileText className="w-4 h-4" />
          Audit History ({totalReports})
        </button>

        <button
          onClick={() => setActiveTab('detail')}
          disabled={!selectedReportId && !detailedReport}
          className={`flex items-center gap-2 px-4 py-2.5 border-b-2 font-semibold transition-colors whitespace-nowrap cursor-pointer ${
            activeTab === 'detail'
              ? 'border-indigo-600 text-indigo-600'
              : detailedReport
              ? 'border-transparent text-slate-600 hover:text-slate-900'
              : 'border-transparent text-slate-300 cursor-not-allowed'
          }`}
        >
          <Eye className="w-4 h-4" />
          Detailed Assessment
        </button>

        <button
          onClick={() => setActiveTab('compare')}
          className={`flex items-center gap-2 px-4 py-2.5 border-b-2 font-semibold transition-colors whitespace-nowrap cursor-pointer ${
            activeTab === 'compare'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <GitCompare className="w-4 h-4" />
          Before & After Comparison
        </button>

        <button
          onClick={() => setActiveTab('analytics')}
          className={`flex items-center gap-2 px-4 py-2.5 border-b-2 font-semibold transition-colors whitespace-nowrap cursor-pointer ${
            activeTab === 'analytics'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          Progress Analytics
        </button>
      </div>

      {/* ============================================================= */}
      {/* TAB 1: AUDIT HISTORY                                          */}
      {/* ============================================================= */}
      {activeTab === 'history' && (
        <div className="space-y-4">
          {/* Filter & Compare Banner */}
          <Card className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2 flex-1">
              <Filter className="w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Filter by target role (e.g. Frontend)..."
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="text-xs px-3 py-1.5 rounded-lg border border-slate-200 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 w-full sm:w-64"
              />
              {roleFilter && (
                <button
                  onClick={() => setRoleFilter('')}
                  className="text-xs text-slate-400 hover:text-slate-600"
                >
                  Clear
                </button>
              )}
            </div>

            {selectedForCompare.length === 2 && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-indigo-700 font-medium">
                  2 Reports selected for audit
                </span>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => handleRunComparison(selectedForCompare[0], selectedForCompare[1])}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white"
                >
                  <GitCompare className="w-3.5 h-3.5 mr-1" />
                  Compare Selected
                </Button>
              </div>
            )}
          </Card>

          {/* Reports Table / Cards */}
          {isLoadingReports ? (
            <div className="flex flex-col items-center justify-center p-12 space-y-3">
              <RefreshCw className="w-6 h-6 text-indigo-600 animate-spin" />
              <p className="text-xs text-slate-500 font-medium">Loading saved assessment reports...</p>
            </div>
          ) : reports.length === 0 ? (
            <Card className="p-12 text-center space-y-4">
              <FileText className="w-12 h-12 text-slate-300 mx-auto" />
              <div className="space-y-1">
                <h3 className="text-base font-bold text-slate-800">No Assessment Reports Found</h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  Run a real resume analysis on the Resume Upload or Review page, then click "Save Analysis Report" to record historical benchmarks.
                </p>
              </div>
              {latestResumeId && (
                <Button variant="primary" size="sm" onClick={handleSaveCurrentSessionReport}>
                  Save Current Session Analysis
                </Button>
              )}
            </Card>
          ) : (
            <div className="space-y-3">
              {reports.map((rep) => {
                const isSelected = selectedForCompare.includes(rep.id);

                return (
                  <Card
                    key={rep.id}
                    className={`p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-colors ${
                      isSelected ? 'border-indigo-400 bg-indigo-50/20' : 'hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-start gap-3.5 flex-1">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleSelectForCompare(rep.id)}
                        className="mt-1 w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 border-slate-300 cursor-pointer"
                        title="Select for comparison"
                      />

                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="font-bold text-slate-900 text-sm sm:text-base">
                            {rep.report_title || rep.resume_name}
                          </h3>
                          <Badge variant="outline" size="sm">
                            {rep.target_role}
                          </Badge>
                          <span className="text-[11px] text-slate-400 font-mono">
                            {rep.date}
                          </span>
                        </div>

                        <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                          <span>
                            Document: <strong className="text-slate-700">{rep.resume_name}</strong>
                          </span>
                          <span>•</span>
                          <span>
                            Issues Found: <strong className="text-slate-700">{rep.issues_count}</strong>
                          </span>
                          {rep.match_score > 0 && (
                            <>
                              <span>•</span>
                              <span>
                                Job Match: <strong className="text-indigo-600">{rep.match_score}%</strong>
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Score & Actions */}
                    <div className="flex items-center gap-4 shrink-0 self-end sm:self-center">
                      <div className="text-right">
                        <div className="text-xs text-slate-400 font-medium">ATS-Style Score</div>
                        <div className="flex items-center gap-1.5 justify-end">
                          <span className="text-lg sm:text-xl font-bold font-mono text-slate-900">
                            {rep.overall_score}
                          </span>
                          <span className="text-xs text-slate-400 font-mono">/ 100</span>
                          <Badge variant={getReadinessBadgeVariant(rep.overall_score)} size="sm">
                            {rep.overall_score >= 80 ? 'Ready' : rep.overall_score >= 65 ? 'Competitive' : 'Developing'}
                          </Badge>
                        </div>
                      </div>

                      <div className="flex items-center gap-1.5 border-l border-slate-200 pl-3">
                        <button
                          onClick={() => loadDetailedReport(rep.id)}
                          className="p-2 text-slate-500 hover:text-indigo-600 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
                          title="View detailed assessment"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleExportPdf(rep.id)}
                          disabled={isExportingPdf}
                          className="p-2 text-slate-500 hover:text-indigo-600 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
                          title="Download native PDF"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteReport(rep.id)}
                          className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                          title="Delete report"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </Card>
                );
              })}

              {/* Pagination bar */}
              {totalReports > 10 && (
                <div className="flex items-center justify-between text-xs text-slate-500 pt-3">
                  <span>
                    Showing {reports.length} of {totalReports} reports
                  </span>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={currentPage <= 1}
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    >
                      Previous
                    </Button>
                    <span className="font-mono text-slate-700">Page {currentPage}</span>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={reports.length < 10}
                      onClick={() => setCurrentPage((p) => p + 1)}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ============================================================= */}
      {/* TAB 2: DETAILED ASSESSMENT REPORT                             */}
      {/* ============================================================= */}
      {activeTab === 'detail' && (
        <div className="space-y-6">
          {isLoadingDetail ? (
            <div className="flex flex-col items-center justify-center p-16 space-y-3">
              <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin" />
              <p className="text-xs text-slate-500 font-medium">Loading comprehensive assessment audit...</p>
            </div>
          ) : !detailedReport ? (
            <Card className="p-8 text-center space-y-3">
              <AlertCircle className="w-8 h-8 text-slate-400 mx-auto" />
              <p className="text-sm font-semibold text-slate-800">No Report Selected</p>
              <p className="text-xs text-slate-500">Select an assessment report from Audit History to view detailed findings.</p>
              <Button variant="outline" size="sm" onClick={() => setActiveTab('history')}>
                Return to History
              </Button>
            </Card>
          ) : (
            <div className="space-y-6">
              {/* Header Box */}
              <div className="bg-slate-900 text-white rounded-2xl p-6 sm:p-8 relative overflow-hidden shadow-xl">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-300 bg-indigo-500/20 px-2.5 py-0.5 rounded border border-indigo-400/30">
                        {detailedReport.target_role}
                      </span>
                      <span className="text-xs text-slate-400">
                        Document: {detailedReport.resume_name}
                      </span>
                    </div>

                    <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
                      {detailedReport.report_title}
                    </h2>
                    <p className="text-xs text-slate-400 font-mono">
                      Evaluation Date: {detailedReport.date} • Reference ID: {detailedReport.id}
                    </p>
                  </div>

                  <div className="flex items-center gap-4 bg-white/10 backdrop-blur-xs p-4 rounded-xl border border-white/10 shrink-0">
                    <div>
                      <div className="text-[11px] text-slate-300 font-medium uppercase tracking-wider">
                        CareerLens ATS-Style Estimate
                      </div>
                      <div className="flex items-baseline gap-1.5 mt-0.5">
                        <span className="text-3xl font-extrabold text-emerald-400">
                          {detailedReport.overall_score}
                        </span>
                        <span className="text-xs text-slate-300">/ 100</span>
                      </div>
                      <span className="text-xs text-emerald-300 font-semibold">
                        {detailedReport.readiness_tier}
                      </span>
                    </div>

                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => handleExportPdf(detailedReport.id)}
                      disabled={isExportingPdf}
                      className="bg-white text-slate-900 hover:bg-slate-100"
                    >
                      <Download className="w-4 h-4 mr-1.5" />
                      PDF Report
                    </Button>
                  </div>
                </div>
              </div>

              {/* Disclaimer */}
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-slate-600 flex items-start gap-2.5">
                <Info className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                <p className="text-[11px] leading-relaxed">
                  <strong>CareerLens Scoring Disclaimer:</strong> {detailedReport.disclaimer}
                </p>
              </div>

              {/* Component Score Breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {Object.entries(detailedReport.component_scores).map(([compKey, val]) => (
                  <Card key={compKey} className="p-4 space-y-2">
                    <div className="flex items-center justify-between text-xs text-slate-500">
                      <span className="font-semibold capitalize">{compKey.replace('_', ' ')}</span>
                      <span className="font-mono text-slate-700 font-bold">{val} / 100</span>
                    </div>
                    <ProgressBar value={val} color={val >= 75 ? 'emerald' : val >= 60 ? 'indigo' : 'amber'} size="sm" showPercentage={false} />
                    <p className="text-[10px] text-slate-400 leading-tight">
                      {detailedReport.scoring_rationale[compKey] || 'Weighted composite calculation.'}
                    </p>
                  </Card>
                ))}
              </div>

              {/* Findings & Actionable Recommendations */}
              <div className="space-y-3">
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-indigo-600" />
                  Identified Findings & Actionable Advice ({detailedReport.findings.length})
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {detailedReport.findings.map((f, fIdx) => (
                    <Card key={fIdx} className="p-4 space-y-2 border-slate-200 hover:border-slate-300">
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="font-bold text-slate-900 text-sm">{f.title}</h4>
                        <Badge
                          variant={f.severity === 'error' ? 'danger' : f.severity === 'warning' ? 'warning' : 'info'}
                          size="sm"
                        >
                          {(f.severity || 'note').toUpperCase()}
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed">{f.description}</p>
                      {f.suggestion && (
                        <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100 text-[11px] text-indigo-900 font-medium">
                          <strong>Fix:</strong> {f.suggestion}
                        </div>
                      )}
                    </Card>
                  ))}
                </div>
              </div>

              {/* Identified Skills Taxonomy */}
              <div className="space-y-3">
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Award className="w-5 h-5 text-purple-600" />
                  Detected Technical & Domain Skills
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  {Object.entries(detailedReport.extracted_skills).map(([groupName, skills]) => (
                    <Card key={groupName} className="p-3.5 space-y-2">
                      <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
                        {groupName.replace('_', ' ')}
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {skills.map((s, sIdx) => (
                          <Badge key={sIdx} variant="outline" size="sm">
                            {s.name}
                          </Badge>
                        ))}
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ============================================================= */}
      {/* TAB 3: BEFORE-AND-AFTER COMPARISON                            */}
      {/* ============================================================= */}
      {activeTab === 'compare' && (
        <div className="space-y-6">
          {/* Selectors Card */}
          <Card className="p-5 space-y-4">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <GitCompare className="w-4 h-4 text-indigo-600" />
              Compare Two Assessment Reports
            </h3>
            <p className="text-xs text-slate-500">
              Select an earlier iteration (Report A) and a revised iteration (Report B) to inspect measurable score delta and resolved findings.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700">Baseline Iteration (Report A)</label>
                <select
                  value={compareReportA}
                  onChange={(e) => setCompareReportA(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-200 bg-white"
                >
                  <option value="">-- Choose Baseline Report --</option>
                  {reports.map((r) => (
                    <option key={`a-${r.id}`} value={r.id}>
                      {r.report_title || r.resume_name} ({r.date} — Score: {r.overall_score})
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700">Revised Iteration (Report B)</label>
                <select
                  value={compareReportB}
                  onChange={(e) => setCompareReportB(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-200 bg-white"
                >
                  <option value="">-- Choose Revised Report --</option>
                  {reports.map((r) => (
                    <option key={`b-${r.id}`} value={r.id}>
                      {r.report_title || r.resume_name} ({r.date} — Score: {r.overall_score})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex justify-end">
              <Button
                variant="primary"
                size="sm"
                onClick={() => handleRunComparison(compareReportA, compareReportB)}
                disabled={!compareReportA || !compareReportB || compareReportA === compareReportB || isComparing}
              >
                {isComparing ? 'Comparing...' : 'Run Comparative Audit'}
              </Button>
            </div>
          </Card>

          {/* Comparison Results */}
          {comparisonResult && (
            <div className="space-y-6">
              {/* Delta Banner */}
              <Card className="p-6 bg-gradient-to-r from-slate-900 to-indigo-950 text-white border-transparent">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-300">
                      Comparative Audit Result
                    </span>
                    <h3 className="text-xl font-bold">
                      {comparisonResult.title_a} <ArrowRight className="inline w-4 h-4 text-slate-400 mx-1" /> {comparisonResult.title_b}
                    </h3>
                    <p className="text-xs text-slate-300">
                      Evaluated deterministic progression across document revisions.
                    </p>
                  </div>

                  <div className="flex items-center gap-4 bg-white/10 p-3.5 rounded-xl border border-white/10 shrink-0">
                    <div className="text-center">
                      <div className="text-[10px] text-slate-300 uppercase">Baseline</div>
                      <div className="text-xl font-bold font-mono">{comparisonResult.score_a}</div>
                    </div>
                    <ArrowRight className="w-4 h-4 text-slate-400" />
                    <div className="text-center">
                      <div className="text-[10px] text-slate-300 uppercase">Revised</div>
                      <div className="text-xl font-bold font-mono">{comparisonResult.score_b}</div>
                    </div>
                    <div className="border-l border-white/20 pl-3 text-center">
                      <div className="text-[10px] text-slate-300 uppercase">Score Delta</div>
                      <Badge
                        variant={comparisonResult.score_delta >= 0 ? 'success' : 'danger'}
                        size="md"
                        className="mt-0.5"
                      >
                        {comparisonResult.score_delta >= 0 ? `+${comparisonResult.score_delta}` : comparisonResult.score_delta} pts
                      </Badge>
                    </div>
                  </div>
                </div>
              </Card>

              {/* Compatibility Notice */}
              {comparisonResult.compatibility_notice && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 text-xs text-amber-900 flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <span>{comparisonResult.compatibility_notice}</span>
                </div>
              )}

              {/* Category Deltas Grid */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                {Object.entries(comparisonResult.category_deltas).map(([catKey, deltaObj]) => (
                  <Card key={catKey} className="p-4 space-y-1">
                    <span className="text-xs text-slate-500 font-semibold capitalize block">
                      {catKey.replace('_', ' ')}
                    </span>
                    <div className="flex items-baseline justify-between pt-1">
                      <span className="text-xs text-slate-400 font-mono">
                        {deltaObj.before} → {deltaObj.after}
                      </span>
                      <span
                        className={`text-sm font-bold font-mono ${
                          deltaObj.delta > 0
                            ? 'text-emerald-600'
                            : deltaObj.delta < 0
                            ? 'text-rose-600'
                            : 'text-slate-500'
                        }`}
                      >
                        {deltaObj.delta > 0 ? `+${deltaObj.delta}` : deltaObj.delta}
                      </span>
                    </div>
                  </Card>
                ))}
              </div>

              {/* Issues Diff Columns */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Resolved Issues */}
                <Card className="p-4 space-y-3 border-emerald-200 bg-emerald-50/20">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider">
                      Issues Resolved ({comparisonResult.issues_resolved.length})
                    </h4>
                  </div>
                  {comparisonResult.issues_resolved.length === 0 ? (
                    <p className="text-xs text-slate-400 italic">No previous issues were fully eliminated.</p>
                  ) : (
                    <ul className="space-y-2 text-xs">
                      {comparisonResult.issues_resolved.map((res, rIdx) => (
                        <li key={rIdx} className="bg-white p-2.5 rounded border border-emerald-200 text-slate-700">
                          <strong className="text-emerald-800">{res.title}</strong>
                        </li>
                      ))}
                    </ul>
                  )}
                </Card>

                {/* Still Present */}
                <Card className="p-4 space-y-3 border-amber-200 bg-amber-50/20">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-amber-600" />
                    <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider">
                      Still Present ({comparisonResult.issues_still_present.length})
                    </h4>
                  </div>
                  {comparisonResult.issues_still_present.length === 0 ? (
                    <p className="text-xs text-slate-400 italic">No remaining warnings carried over.</p>
                  ) : (
                    <ul className="space-y-2 text-xs">
                      {comparisonResult.issues_still_present.map((pres, pIdx) => (
                        <li key={pIdx} className="bg-white p-2.5 rounded border border-amber-200 text-slate-700">
                          <strong className="text-amber-800">{pres.title}</strong>
                        </li>
                      ))}
                    </ul>
                  )}
                </Card>

                {/* Newly Identified */}
                <Card className="p-4 space-y-3 border-slate-200 bg-slate-50/50">
                  <div className="flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-indigo-600" />
                    <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider">
                      Newly Flagged ({comparisonResult.issues_newly_identified.length})
                    </h4>
                  </div>
                  {comparisonResult.issues_newly_identified.length === 0 ? (
                    <p className="text-xs text-slate-400 italic">No new issues were introduced.</p>
                  ) : (
                    <ul className="space-y-2 text-xs">
                      {comparisonResult.issues_newly_identified.map((newIssue, nIdx) => (
                        <li key={nIdx} className="bg-white p-2.5 rounded border border-slate-200 text-slate-700">
                          <strong className="text-indigo-900">{newIssue.title}</strong>
                        </li>
                      ))}
                    </ul>
                  )}
                </Card>
              </div>

              {/* Next Steps */}
              {comparisonResult.recommended_next_actions.length > 0 && (
                <Card className="p-4 space-y-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Recommended Next Actions
                  </span>
                  <ul className="list-disc list-inside text-xs text-slate-700 space-y-1">
                    {comparisonResult.recommended_next_actions.map((act, aIdx) => (
                      <li key={aIdx}>{act}</li>
                    ))}
                  </ul>
                </Card>
              )}
            </div>
          )}
        </div>
      )}

      {/* ============================================================= */}
      {/* TAB 4: PROGRESS ANALYTICS                                      */}
      {/* ============================================================= */}
      {activeTab === 'analytics' && (
        <div className="space-y-6">
          {isLoadingAnalytics ? (
            <div className="flex flex-col items-center justify-center p-16 space-y-3">
              <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin" />
              <p className="text-xs text-slate-500 font-medium">Aggregating historical metrics and roadmap progression...</p>
            </div>
          ) : !analytics || analytics.total_analyses_completed === 0 ? (
            <Card className="p-12 text-center space-y-3">
              <BarChart3 className="w-12 h-12 text-slate-300 mx-auto" />
              <h3 className="text-base font-bold text-slate-800">No Historical Analytics Yet</h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Progress analytics require at least two saved evaluation reports over time to compute trajectory curves.
              </p>
              {latestResumeId && (
                <Button variant="primary" size="sm" onClick={handleSaveCurrentSessionReport}>
                  Save Current Evaluation
                </Button>
              )}
            </Card>
          ) : (
            <div className="space-y-6">
              {/* Analytics Summary Top Row */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <Card className="p-4 space-y-1">
                  <div className="text-xs text-slate-500 font-medium">Latest Readiness Score</div>
                  <div className="text-2xl font-bold font-mono text-slate-900">
                    {analytics.latest_score ?? '—'} <span className="text-xs text-slate-400 font-normal">/ 100</span>
                  </div>
                  {typeof analytics.previous_score === 'number' && typeof analytics.latest_score === 'number' && (
                    <div className="text-[11px] font-semibold text-emerald-600">
                      {analytics.latest_score - analytics.previous_score >= 0 ? '+' : ''}
                      {analytics.latest_score - analytics.previous_score} pts vs previous
                    </div>
                  )}
                </Card>

                <Card className="p-4 space-y-1">
                  <div className="text-xs text-slate-500 font-medium">Historical Audits</div>
                  <div className="text-2xl font-bold font-mono text-slate-900">
                    {analytics.total_analyses_completed}
                  </div>
                  <div className="text-[11px] text-slate-400 font-medium">Saved benchmarks</div>
                </Card>

                <Card className="p-4 space-y-1">
                  <div className="text-xs text-slate-500 font-medium">Roadmap Progress</div>
                  <div className="text-2xl font-bold font-mono text-slate-900">
                    {analytics.roadmap_completion_pct}%
                  </div>
                  <div className="text-[11px] text-slate-400">
                    {analytics.roadmap_tasks_completed} of {analytics.roadmap_tasks_total} tasks done
                  </div>
                </Card>

                <Card className="p-4 space-y-1">
                  <div className="text-xs text-slate-500 font-medium">Open Findings</div>
                  <div className="text-2xl font-bold font-mono text-amber-600">
                    {analytics.current_open_issues}
                  </div>
                  <div className="text-[11px] text-slate-400 font-medium">
                    {analytics.issues_resolved_total} resolved previously
                  </div>
                </Card>
              </div>

              {/* Score Progression History Cards */}
              <Card className="p-5 space-y-4">
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-indigo-600" />
                  Score Progression Trajectory
                </h3>

                <div className="space-y-3">
                  {analytics.score_progression.map((item, idx) => (
                    <div key={idx} className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 rounded-lg border border-slate-100 bg-slate-50/50">
                      <div className="space-y-0.5">
                        <span className="font-bold text-xs text-slate-800">{item.title}</span>
                        <div className="text-[11px] text-slate-400 font-mono">
                          {item.date} • Target: {item.target_role}
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-32 hidden sm:block">
                          <ProgressBar value={item.score} color="indigo" size="sm" showPercentage={false} />
                        </div>
                        <span className="font-mono font-bold text-sm text-slate-900 w-12 text-right">
                          {item.score}/100
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Three-Tier Evidence Breakdown */}
              <Card className="p-5 space-y-4">
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  Competency Verification Hierarchy
                </h3>
                <p className="text-xs text-slate-500">
                  CareerLens strictly separates self-reported learning progress from document-supported claims and third-party verified evidence.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                  <div className="p-3.5 rounded-lg border border-slate-200 bg-white space-y-1">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                      Self-Reported Progress
                    </span>
                    <div className="text-xl font-bold font-mono text-slate-800">
                      {analytics.skills_by_evidence_type.self_reported} tasks
                    </div>
                    <p className="text-[10px] text-slate-400 leading-tight">
                      Completed roadmap milestones. Does not constitute certified competence.
                    </p>
                  </div>

                  <div className="p-3.5 rounded-lg border border-indigo-200 bg-indigo-50/30 space-y-1">
                    <span className="text-[11px] font-bold text-indigo-700 uppercase tracking-wider block">
                      Resume Evidence
                    </span>
                    <div className="text-xl font-bold font-mono text-indigo-900">
                      {analytics.skills_by_evidence_type.resume_evidence} skills
                    </div>
                    <p className="text-[10px] text-indigo-600 leading-tight">
                      Demonstrated in uploaded resume projects and work bullets.
                    </p>
                  </div>

                  <div className="p-3.5 rounded-lg border border-emerald-200 bg-emerald-50/30 space-y-1">
                    <span className="text-[11px] font-bold text-emerald-700 uppercase tracking-wider block">
                      Independently Verified
                    </span>
                    <div className="text-xl font-bold font-mono text-emerald-900">
                      {analytics.skills_by_evidence_type.independently_verified} skills
                    </div>
                    <p className="text-[10px] text-emerald-600 leading-tight">
                      Corroborated by public GitHub repositories and test suites.
                    </p>
                  </div>
                </div>
              </Card>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
