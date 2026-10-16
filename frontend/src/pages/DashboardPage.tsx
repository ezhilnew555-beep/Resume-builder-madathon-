import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  TrendingUp,
  FileCheck2,
  Briefcase,
  AlertCircle,
  ArrowRight,
  UploadCloud,
  CheckCircle2,
  Sparkles,
  Target,
  Layers,
  Award,
  RefreshCw,
  ServerCrash,
  Wifi,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { ScoreGauge } from '../components/common/ScoreGauge';
import { ProgressBar } from '../components/common/ProgressBar';
import { DemoBanner } from '../components/common/DemoBanner';
import { apiService } from '../services/api';
import type { BackendDashboardData } from '../services/api';
import type { ReadinessScore, JobMatchAnalysis, CareerReport } from '../types';
import { useAuth } from '../context/AuthContext';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, getAccessToken } = useAuth();

  // Connection & loading state
  const [loading, setLoading] = useState(true);
  const [backendConnected, setBackendConnected] = useState<boolean | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [useOfflineFallback, setUseOfflineFallback] = useState(false);

  // Data states
  const [liveData, setLiveData] = useState<BackendDashboardData | null>(null);
  const [readiness, setReadiness] = useState<ReadinessScore | null>(null);
  const [jobMatch, setJobMatch] = useState<JobMatchAnalysis | null>(null);
  const [reports, setReports] = useState<CareerReport[]>([]);

  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    setConnectionError(null);

    try {
      const token = user ? await getAccessToken() : null;
      // 1. Fetch live dashboard from backend (with user token if signed in)
      const liveDashboard = await apiService.fetchLiveDashboard(token, useOfflineFallback);
      setLiveData(liveDashboard);
      setBackendConnected(true);

      const isClean = !liveDashboard.is_demo && liveDashboard.overall_readiness_score === 0;

      // Map backend live payload to UI structures
      setReadiness({
        overall: liveDashboard.overall_readiness_score,
        atsScore: liveDashboard.metrics.ats_compatibility?.value || 0,
        skillAlignment: liveDashboard.metrics.skill_alignment?.value || 0,
        experienceImpact: liveDashboard.metrics.experience_impact?.value || 0,
        presentation: liveDashboard.metrics.presentation?.value || 0,
        tier: (liveDashboard.readiness_tier || (isClean ? 'Not Evaluated' : 'Developing')) as any,
      });

      // Fetch saved reports from database if authenticated
      if (token && !useOfflineFallback) {
        try {
          const liveReports = await apiService.fetchSavedReportsLive({ page: 1, page_size: 5 }, token);
          setReports(liveReports.reports.map((r) => ({
            id: r.id,
            targetRole: r.target_role,
            resumeName: r.resume_name || 'Uploaded Resume',
            date: r.date,
            overallScore: r.overall_score,
            atsScore: r.ats_score,
            matchScore: r.match_score || 0,
            status: 'completed',
          })));
        } catch {
          setReports([]);
        }
      } else if (useOfflineFallback) {
        const reportData = await apiService.getReports();
        setReports(reportData);
      } else {
        setReports([]);
      }
    } catch (err: any) {
      setBackendConnected(false);
      setConnectionError(err?.message || 'Unable to connect to FastAPI backend at http://localhost:8000/api/v1');

      if (useOfflineFallback) {
        const [readinessData, matchData, reportData] = await Promise.all([
          apiService.getReadinessScore(),
          apiService.matchJobDescription('', '', ''),
          apiService.getReports(),
        ]);
        setReadiness(readinessData);
        setJobMatch(matchData);
        setReports(reportData);
      }
    } finally {
      setLoading(false);
    }
  }, [useOfflineFallback, user, getAccessToken]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const handleEnableOfflineDemo = async () => {
    setUseOfflineFallback(true);
    setLoading(true);
    try {
      const [readinessData, matchData, reportData] = await Promise.all([
        apiService.getReadinessScore(),
        apiService.matchJobDescription('', '', ''),
        apiService.getReports(),
      ]);
      setReadiness(readinessData);
      setJobMatch(matchData);
      setReports(reportData);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Backend Status Bar */}
      {backendConnected === true && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-xs text-emerald-950">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-semibold">FastAPI Backend Connected:</span>
            <span>Serving live demonstration payload from <code className="bg-emerald-100 px-1 py-0.5 rounded font-mono">/api/v1/dashboard</code>.</span>
          </div>
          <Badge variant="success" size="sm">
            <Wifi className="w-3 h-3 mr-1" /> Live REST API
          </Badge>
        </div>
      )}

      {/* Backend Connection Error Alert (Not silently masked) */}
      {backendConnected === false && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl space-y-3 text-xs text-rose-950">
          <div className="flex items-start gap-3">
            <ServerCrash className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-bold text-sm text-rose-950">
                FastAPI Backend Connection Unavailable
              </h4>
              <p className="mt-0.5 text-rose-900/80 leading-relaxed">
                {connectionError}. To start the backend, run: <code className="font-mono bg-rose-100 px-1.5 py-0.5 rounded text-rose-900">uvicorn app.main:app --reload</code> in the backend directory.
              </p>
            </div>
          </div>

          <div className="flex items-center justify-between pt-1 border-t border-rose-200/60">
            <span className="text-[11px] text-rose-800">
              Live API response failed. You can retry or explore cached demonstration data.
            </span>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                icon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
                onClick={() => loadDashboardData()}
                disabled={loading}
              >
                Retry Connection
              </Button>
              {!useOfflineFallback && (
                <Button
                  size="sm"
                  variant="primary"
                  onClick={handleEnableOfflineDemo}
                >
                  View Offline Client Demo
                </Button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Demo notice banner (only shown if demo data is active) */}
      {liveData?.is_demo && (
        <DemoBanner
          phaseNotice={backendConnected ? "Phase 2 Live API Feed" : "Phase 2 Verification Mode"}
          message={
            liveData?.demo_notice ||
            "Displaying benchmark employability telemetry for demonstration candidate Alex Rivera. Analytical calculations are served via FastAPI endpoints."
          }
        />
      )}

      {loading && (
        <div className="flex items-center gap-2 p-3 bg-white rounded-xl border border-slate-200 text-xs text-slate-500 animate-pulse">
          <div className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          <span>Synchronizing candidate evaluation telemetry from FastAPI...</span>
        </div>
      )}

      {/* 1. Welcome Section */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-2xl p-6 sm:p-8 text-white shadow-md relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-indigo-300 text-xs font-medium mb-3">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Target Career: {liveData?.target_career || (user ? 'Not Specified' : 'Full Stack / Backend Software Engineer')}</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Welcome back, {user?.user_metadata?.full_name || (user?.email ? user.email.split('@')[0] : (liveData?.candidate_name || 'Candidate'))}!
            </h2>
            <p className="text-slate-300 text-sm mt-2 leading-relaxed">
              {(readiness?.overall ?? 0) > 0 ? (
                <>
                  Your overall employability index is currently rated at{' '}
                  <strong className="text-emerald-400 font-bold">
                    {readiness?.overall}/100 ({readiness?.tier})
                  </strong>.
                  Resolving key requirement gaps and refining bullet metrics will improve your ATS readiness.
                </>
              ) : (
                <>
                  Your career profile is currently clean. Upload your resume or build one from scratch to calculate your live ATS readiness score and employability metrics.
                </>
              )}
            </p>

            <div className="flex flex-wrap gap-3 mt-5">
              <Button
                variant="primary"
                size="md"
                icon={<UploadCloud className="w-4 h-4" />}
                onClick={() => navigate('/upload')}
              >
                Upload New Resume
              </Button>
              <Button
                variant="outline"
                size="md"
                className="bg-white/10 text-white border-white/20 hover:bg-white/20 hover:text-white"
                icon={<Briefcase className="w-4 h-4" />}
                onClick={() => navigate('/job-match')}
              >
                Match Job Posting
              </Button>
              <Button
                variant="ghost"
                size="md"
                className="text-indigo-200 hover:text-white hover:bg-white/10"
                icon={<Target className="w-4 h-4" />}
                onClick={() => navigate('/roadmap')}
              >
                View Action Plan
              </Button>
            </div>
          </div>

          <div className="hidden lg:flex items-center justify-center p-4 bg-white/5 rounded-2xl border border-white/10 backdrop-blur-xs">
            <ScoreGauge
              score={readiness?.overall ?? 0}
              title="Career Readiness Index"
              subtitle={(readiness?.overall ?? 0) > 0 ? readiness?.tier || 'Evaluated' : 'Awaiting Resume'}
              size="lg"
            />
          </div>
        </div>
      </div>

      {/* 2. Career Readiness Overview (4 Gauges/Cards) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="hover:border-indigo-200 transition-colors">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              ATS Compatibility
            </span>
            <span className="p-1.5 rounded-lg bg-emerald-50 text-emerald-600">
              <ShieldCheck className="w-4 h-4" />
            </span>
          </div>
          <div className="flex items-baseline justify-between mb-2">
            <span className="text-2xl font-bold font-mono text-slate-900">
              {readiness?.atsScore ?? 0}%
            </span>
            <Badge variant={(readiness?.atsScore ?? 0) > 0 ? "success" : "default"} size="sm">
              {(readiness?.atsScore ?? 0) > 0 ? (liveData?.metrics.ats_compatibility?.status || "Optimal Structure") : "Not Evaluated"}
            </Badge>
          </div>
          <ProgressBar value={readiness?.atsScore ?? 0} color="emerald" size="sm" showPercentage={false} />
          <p className="text-[11px] text-slate-500 mt-2">
            {liveData?.metrics.ats_compatibility?.description || "Headers, bullet lengths, and font hierarchy follow ATS guidelines."}
          </p>
        </Card>

        <Card className="hover:border-indigo-200 transition-colors">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Skill Alignment
            </span>
            <span className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
              <Layers className="w-4 h-4" />
            </span>
          </div>
          <div className="flex items-baseline justify-between mb-2">
            <span className="text-2xl font-bold font-mono text-slate-900">
              {readiness?.skillAlignment ?? 0}%
            </span>
            <Badge variant={(readiness?.skillAlignment ?? 0) > 0 ? "warning" : "default"} size="sm">
              {(readiness?.skillAlignment ?? 0) > 0 ? (liveData?.metrics.skill_alignment?.status || "Evaluated") : "Not Evaluated"}
            </Badge>
          </div>
          <ProgressBar value={readiness?.skillAlignment ?? 0} color="indigo" size="sm" showPercentage={false} />
          <p className="text-[11px] text-slate-500 mt-2">
            {liveData?.metrics.skill_alignment?.description || "Assesses technical and tooling alignment against target job requirements."}
          </p>
        </Card>

        <Card className="hover:border-indigo-200 transition-colors">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Experience Impact
            </span>
            <span className="p-1.5 rounded-lg bg-blue-50 text-blue-600">
              <TrendingUp className="w-4 h-4" />
            </span>
          </div>
          <div className="flex items-baseline justify-between mb-2">
            <span className="text-2xl font-bold font-mono text-slate-900">
              {readiness?.experienceImpact ?? 0}%
            </span>
            <Badge variant={(readiness?.experienceImpact ?? 0) > 0 ? "info" : "default"} size="sm">
              {(readiness?.experienceImpact ?? 0) > 0 ? (liveData?.metrics.experience_impact?.status || "Quantified") : "Not Evaluated"}
            </Badge>
          </div>
          <ProgressBar value={readiness?.experienceImpact ?? 0} color="indigo" size="sm" showPercentage={false} />
          <p className="text-[11px] text-slate-500 mt-2">
            {liveData?.metrics.experience_impact?.description || "Measures business impact and quantified metrics in experience bullets."}
          </p>
        </Card>

        <Card className="hover:border-indigo-200 transition-colors">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Presentation & Tone
            </span>
            <span className="p-1.5 rounded-lg bg-purple-50 text-purple-600">
              <Award className="w-4 h-4" />
            </span>
          </div>
          <div className="flex items-baseline justify-between mb-2">
            <span className="text-2xl font-bold font-mono text-slate-900">
              {readiness?.presentation ?? 0}%
            </span>
            <Badge variant={(readiness?.presentation ?? 0) > 0 ? "purple" : "default"} size="sm">
              {(readiness?.presentation ?? 0) > 0 ? (liveData?.metrics.presentation?.status || "Executive") : "Not Evaluated"}
            </Badge>
          </div>
          <ProgressBar value={readiness?.presentation ?? 0} color="emerald" size="sm" showPercentage={false} />
          <p className="text-[11px] text-slate-500 mt-2">
            {liveData?.metrics.presentation?.description || "Professional vocabulary with strong action-verb diversity."}
          </p>
        </Card>
      </div>

      {/* Middle row: Resume Summary & Job Match Spotlight */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Resume Analysis Summary (2 cols) */}
        <Card
          className="lg:col-span-2"
          title="Active Resume Audit Summary"
          subtitle={liveData?.active_resume_summary.file_name || "Alex_Rivera_Software_Eng_v2.pdf (Parsed Oct 14, 2026)"}
          headerAction={
            <Button
              size="sm"
              variant="outline"
              icon={<FileCheck2 className="w-3.5 h-3.5" />}
              onClick={() => navigate('/review')}
            >
              Review All Findings
            </Button>
          }
        >
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-3 p-3.5 bg-slate-50 rounded-xl border border-slate-100 text-center">
              <div>
                <p className="text-slate-400 text-[11px] font-medium uppercase">Word Count</p>
                <p className="text-base font-bold font-mono text-slate-800">
                  {liveData?.active_resume_summary.word_count || 415} words
                </p>
                <span className="text-[10px] text-emerald-600">Ideal 1-page length</span>
              </div>
              <div className="border-x border-slate-200">
                <p className="text-slate-400 text-[11px] font-medium uppercase">Sections Detected</p>
                <p className="text-base font-bold font-mono text-slate-800">
                  {liveData?.active_resume_summary.sections_detected || 6} / {liveData?.active_resume_summary.sections_total || 6}
                </p>
                <span className="text-[10px] text-emerald-600">100% complete</span>
              </div>
              <div>
                <p className="text-slate-400 text-[11px] font-medium uppercase">Total Suggestions</p>
                <p className="text-base font-bold font-mono text-amber-600">
                  {liveData?.active_resume_summary.total_findings || 5} items
                </p>
                <span className="text-[10px] text-amber-700">
                  {liveData?.active_resume_summary.errors || 1} Error, {liveData?.active_resume_summary.recommendations || 4} Recs
                </span>
              </div>
            </div>

            <div>
              <h4 className="text-xs font-bold text-slate-800 mb-2.5 flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                Priority Findings Requiring Attention
              </h4>
              <div className="space-y-2">
                <div className="p-3 rounded-lg border border-rose-100 bg-rose-50/50 flex items-start justify-between gap-3 text-xs">
                  <div>
                    <div className="flex items-center gap-2">
                      <Badge variant="danger" size="sm">Formatting Error</Badge>
                      <span className="font-semibold text-slate-900">Unclickable LinkedIn URL format</span>
                    </div>
                    <p className="text-slate-600 mt-1">
                      Header has missing HTTPS prefix. Parsers may fail to resolve the link.
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => navigate('/review')}
                    className="text-xs text-rose-700 hover:bg-rose-100 shrink-0"
                  >
                    Fix in Review
                  </Button>
                </div>

                <div className="p-3 rounded-lg border border-amber-100 bg-amber-50/50 flex items-start justify-between gap-3 text-xs">
                  <div>
                    <div className="flex items-center gap-2">
                      <Badge variant="warning" size="sm">Improvement</Badge>
                      <span className="font-semibold text-slate-900">Missing quantified metric in internship bullet #3</span>
                    </div>
                    <p className="text-slate-600 mt-1">
                      "Collaborated in 5-person team" could highlight feature turnaround or test coverage.
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => navigate('/review')}
                    className="text-xs text-amber-700 hover:bg-amber-100 shrink-0"
                  >
                    Fix in Review
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* Job Match Spotlight (1 col) */}
        <Card
          title="Target Role Alignment"
          subtitle={jobMatch?.targetRole || 'Full Stack Software Engineer'}
          headerAction={
            <Badge variant="success" size="sm">
              {jobMatch?.overallMatchScore || 82}% Match
            </Badge>
          }
        >
          <div className="space-y-4">
            <div className="p-3 rounded-xl bg-indigo-50/60 border border-indigo-100">
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="font-semibold text-indigo-950">Company Target</span>
                <span className="font-medium text-indigo-700">{jobMatch?.targetCompany}</span>
              </div>
              <p className="text-[11px] text-slate-600 mt-1">
                {jobMatch?.verifiedEvidenceSummary}
              </p>
            </div>

            <div className="space-y-2">
              <span className="text-xs font-semibold text-slate-700 block">Identified Missing Skills:</span>
              {jobMatch?.skillGaps.slice(0, 2).map((gap) => (
                <div
                  key={gap.name}
                  className="p-2.5 rounded-lg border border-slate-100 bg-slate-50 flex items-center justify-between text-xs"
                >
                  <span className="font-medium text-slate-800">{gap.name}</span>
                  <Badge variant={gap.importance === 'Required' ? 'danger' : 'warning'} size="sm">
                    {gap.importance}
                  </Badge>
                </div>
              ))}
            </div>

            <Button
              variant="outline"
              size="sm"
              className="w-full"
              icon={<ArrowRight className="w-3.5 h-3.5" />}
              iconPosition="right"
              onClick={() => navigate('/job-match')}
            >
              Analyze Custom Job Description
            </Button>
          </div>
        </Card>
      </div>

      {/* Bottom Section: Skill Gap Visualizer & Recent Reports */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Skill Gap Visualization */}
        <Card
          className="lg:col-span-2"
          title="Skill Gap & Competency Breakdown"
          subtitle="Target Competency Coverage for Modern Full Stack Roles"
        >
          <div className="space-y-4">
            {(liveData?.skill_coverage && liveData.skill_coverage.length > 0) ? (
              liveData.skill_coverage.map((item) => (
                <div key={item.skill}>
                  <div className="flex justify-between items-center text-xs mb-1 font-medium">
                    <span className="text-slate-800 flex items-center gap-1.5">
                      {item.percentage >= 80 ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                      ) : (
                        <AlertCircle className="w-3.5 h-3.5 text-amber-500" />
                      )}
                      {item.skill}
                    </span>
                    <span
                      className={`font-mono font-bold ${
                        item.percentage >= 80
                          ? 'text-emerald-600'
                          : item.percentage >= 40
                          ? 'text-amber-600'
                          : 'text-rose-600'
                      }`}
                    >
                      {item.percentage}% ({item.status})
                    </span>
                  </div>
                  <ProgressBar
                    value={item.percentage}
                    color={item.percentage >= 80 ? 'emerald' : item.percentage >= 40 ? 'amber' : 'rose'}
                    size="sm"
                    showPercentage={false}
                  />
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-xs text-slate-400">
                <Layers className="w-8 h-8 mx-auto text-slate-300 mb-2" />
                <p className="font-medium text-slate-600">No skills extracted yet</p>
                <p className="text-[11px] text-slate-400 mt-1">Upload your resume to automatically detect and analyze your technical skills.</p>
              </div>
            )}
          </div>
        </Card>

        {/* Recent Reports */}
        <Card
          title="Recent Evaluations"
          subtitle="Saved database reports"
          headerAction={
            <Button
              size="sm"
              variant="ghost"
              onClick={() => navigate('/reports')}
              className="text-xs text-indigo-600"
            >
              View All
            </Button>
          }
        >
          <div className="divide-y divide-slate-100">
            {reports.length > 0 ? (
              reports.map((report) => (
                <div key={report.id} className="py-3 first:pt-0 last:pb-0 flex items-center justify-between text-xs">
                  <div>
                    <p className="font-semibold text-slate-800">{report.targetRole}</p>
                    <p className="text-[11px] text-slate-400 font-mono mt-0.5">{report.date}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold font-mono text-sm text-slate-900">{report.overallScore}</span>
                    <Badge variant={report.overallScore >= 75 ? 'success' : 'warning'} size="sm">
                      {report.overallScore >= 75 ? 'Strong' : 'Review'}
                    </Badge>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-xs text-slate-400">
                <FileCheck2 className="w-8 h-8 mx-auto text-slate-300 mb-2" />
                <p className="font-medium text-slate-600">No saved reports in database yet</p>
                <p className="text-[11px] text-slate-400 mt-1">Upload a resume or run job match to generate your first audit.</p>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};
