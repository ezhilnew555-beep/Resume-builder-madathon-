import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  AlertCircle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Tag,
  MapPin,
  Sparkles,
  Check,
  X,
  RotateCcw,
  FileText,
  UploadCloud,
  FileCode,
  Layers,
  Cpu,
  ShieldCheck,
  Terminal,
  Bot,
  TrendingUp,
  Target,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import type { BadgeVariant } from '../components/common/Badge';
import { Tabs } from '../components/common/Tabs';
import { DemoBanner } from '../components/common/DemoBanner';
import { Toast } from '../components/common/Toast';
import type { ToastMessage } from '../components/common/Toast';
import { AIAssistantDrawer } from '../components/assistant/AIAssistantDrawer';
import { apiService } from '../services/api';
import type {
  ResumeSection,
  ReviewFinding,
  FindingSeverity,
  LiveResumeDetailResponse,
  LiveResumeAnalysisResponse,
  LiveResumeExplanationResponse,
} from '../types';
import { useAuth } from '../context/AuthContext';

export const ResumeReviewPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user, getAccessToken } = useAuth();

  const [sections, setSections] = useState<ResumeSection[]>([]);
  const [findings, setFindings] = useState<ReviewFinding[]>([]);
  const [activeFilter, setActiveFilter] = useState<string>('all');
  const [activeSectionId, setActiveSectionId] = useState<string>('summary');
  const [toast, setToast] = useState<ToastMessage | null>(null);

  // Live parsed resume & analysis state
  const [liveResume, setLiveResume] = useState<LiveResumeDetailResponse | null>(null);
  const [liveAnalysis, setLiveAnalysis] = useState<LiveResumeAnalysisResponse | null>(null);
  const [explanation, setExplanation] = useState<LiveResumeExplanationResponse | null>(null);
  const [isAssistantOpen, setIsAssistantOpen] = useState<boolean>(false);
  const [rawText, setRawText] = useState<string>('');
  const [showRawText, setShowRawText] = useState<boolean>(false);
  const [isLoadingLive, setIsLoadingLive] = useState<boolean>(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [showSampleData, setShowSampleData] = useState<boolean>(false);

  const resumeIdParam = searchParams.get('resumeId') || sessionStorage.getItem('latest_resume_id');

  useEffect(() => {
    async function loadData() {
      if (resumeIdParam) {
        setIsLoadingLive(true);
        setAnalysisError(null);
        try {
          const token = user ? await getAccessToken() : null;

          // Fetch parsed document, raw text, and run/fetch deterministic analysis in parallel
          const [details, textRes, analysisRes] = await Promise.all([
            apiService.fetchResumeDetailsLive(resumeIdParam, token),
            apiService.fetchResumeTextLive(resumeIdParam, token),
            apiService.analyzeResumeLive(resumeIdParam, {}, token).catch(async (err) => {
              console.warn('Initial analyze request failed, attempting fetch analysis:', err);
              return await apiService.fetchResumeAnalysisLive(resumeIdParam, token);
            }),
          ]);

          setLiveResume(details);
          setRawText(textRes.raw_text);
          setLiveAnalysis(analysisRes);

          // Map detected sections dictionary to ResumeSection items
          const mappedSections: ResumeSection[] = Object.entries(details.sections).map(([key, content]) => {
            const words = content.trim().split(/\s+/).filter(Boolean).length;
            const title = key
              .replace(/_/g, ' ')
              .replace(/\b\w/g, (c) => c.toUpperCase());
            return {
              id: key,
              title,
              content,
              wordCount: words,
              completeness: words > 30 ? 100 : Math.min(Math.round((words / 30) * 100), 90),
            };
          });

          if (mappedSections.length > 0) {
            setSections(mappedSections);
            setActiveSectionId(mappedSections[0].id);
          }

          // Use real live findings from analysis
          if (analysisRes?.findings) {
            setFindings(analysisRes.findings);
          }

          // Fetch grounded AI explanation & recommendations
          apiService.fetchResumeExplanationLive(resumeIdParam, token)
            .then((exp) => setExplanation(exp))
            .catch((err) => console.warn('Could not load resume explanation:', err));
        } catch (err: any) {
          console.warn('Could not load live resume or analysis from backend:', err);
          setAnalysisError(err?.message || 'Failed to complete resume analysis.');
          // Fall back to baseline mock preview
          const [defaultSections, mockFinds] = await Promise.all([
            apiService.getResumeSections(),
            apiService.getReviewFindings(),
          ]);
          setSections(defaultSections);
          setFindings(mockFinds);
        } finally {
          setIsLoadingLive(false);
        }
      } else {
        // Do not pre-fill mock data unless user explicitly toggles sample preview
        setSections([]);
        setFindings([]);
      }
    }

    loadData();
  }, [resumeIdParam, user]);

  const handleStatusChange = (id: string, newStatus: 'accepted' | 'rejected') => {
    setFindings((prev) =>
      prev.map((item) => (item.id === id ? { ...item, status: newStatus } : item))
    );

    const finding = findings.find((f) => f.id === id);
    setToast({
      id: Math.random().toString(),
      type: newStatus === 'accepted' ? 'success' : 'info',
      title: newStatus === 'accepted' ? 'Correction Staged' : 'Suggestion Dismissed',
      message: finding
        ? `"${finding.title}" marked as ${newStatus}. (Held in client session; does not alter original document).`
        : undefined,
    });
  };

  const handleResetFinding = (id: string) => {
    setFindings((prev) =>
      prev.map((item) => (item.id === id ? { ...item, status: 'pending' } : item))
    );
  };

  // Filter findings
  const filteredFindings = findings.filter((item) => {
    if (activeFilter === 'all') return true;
    return item.type === activeFilter;
  });

  const getSeverityBadge = (type: FindingSeverity) => {
    const map: Record<FindingSeverity, { label: string; variant: BadgeVariant; icon: React.ReactNode }> = {
      error: { label: 'Formatting Error', variant: 'danger', icon: <XCircle className="w-3 h-3" /> },
      improvement: { label: 'Improvement', variant: 'warning', icon: <AlertCircle className="w-3 h-3" /> },
      missing: { label: 'Missing Section', variant: 'info', icon: <HelpCircle className="w-3 h-3" /> },
      keyword: { label: 'Keyword Suggestion', variant: 'purple', icon: <Tag className="w-3 h-3" /> },
    };
    return map[type] || { label: type, variant: 'neutral', icon: null };
  };

  const activeSection = sections.find((s) => s.id === activeSectionId) || sections[0];

  const errorCount = findings.filter((f) => f.type === 'error').length;
  const improvementCount = findings.filter((f) => f.type === 'improvement').length;
  const missingCount = findings.filter((f) => f.type === 'missing').length;
  const keywordCount = findings.filter((f) => f.type === 'keyword').length;
  const acceptedCount = findings.filter((f) => f.status === 'accepted').length;

  return (
    <div className="space-y-6">
      {/* Live Status or Demo Banner */}
      {liveAnalysis ? (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-emerald-900 shadow-2xs">
          <div className="flex items-start sm:items-center space-x-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5 sm:mt-0" />
            <span>
              <strong>Deterministic Analysis Complete:</strong> Analyzed <code>{liveAnalysis.filename}</code> using CareerLens ATS diagnostic engine. Results reflect machine-parseable text and verifiable technical evidence.
            </span>
          </div>
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800 self-end sm:self-auto shrink-0">
            {liveAnalysis.readiness_tier}
          </span>
        </div>
      ) : showSampleData ? (
        <DemoBanner
          phaseNotice="Sample Mode: Benchmark Data Preview"
          message="Displaying sample candidate review data (Alex Rivera). Upload your own resume on the Resume Upload page to view live extracted sections and diagnostic findings."
        />
      ) : null}

      {!liveResume && !liveAnalysis && !showSampleData && (
        <Card padding="lg">
          <div className="py-12 px-4 text-center max-w-lg mx-auto space-y-4">
            <div className="w-14 h-14 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto border border-indigo-100 shadow-xs">
              <UploadCloud className="w-7 h-7" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">No Resume Selected for Review</h3>
              <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
                Upload your resume (PDF or DOCX) in the Resume Vault to run the automated ATS diagnostic engine, inspect detected sections, and review improvement findings tailored to your real experience.
              </p>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <Button
                variant="primary"
                size="md"
                icon={<UploadCloud className="w-4 h-4" />}
                onClick={() => navigate('/upload')}
              >
                Go to Resume Upload
              </Button>
              <Button
                variant="outline"
                size="md"
                onClick={async () => {
                  setShowSampleData(true);
                  const [defaultSections, mockFinds] = await Promise.all([
                    apiService.getResumeSections(),
                    apiService.getReviewFindings(),
                  ]);
                  setSections(defaultSections);
                  setFindings(mockFinds);
                }}
              >
                Preview Sample Review
              </Button>
            </div>
          </div>
        </Card>
      )}

      {analysisError && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl flex items-center justify-between text-xs text-rose-900">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{analysisError}</span>
          </div>
          <Button size="sm" variant="outline" onClick={() => navigate('/upload')}>
            Re-Upload Document
          </Button>
        </div>
      )}

      {(liveResume || liveAnalysis || showSampleData) && (
        <>
          {/* Top Header & Metrics */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            ATS-Style Resume Analysis & Findings
          </h2>
          <p className="text-slate-600 text-xs sm:text-sm mt-1">
            Deterministic diagnostic analysis of section completeness, action verb impact, extracted technical competencies, and ATS machine readability.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {liveResume ? (
            <>
              <Badge variant="purple" size="md">
                Live: {liveResume.filename}
              </Badge>
              <Button
                size="sm"
                variant="primary"
                icon={<Target className="w-3.5 h-3.5" />}
                onClick={() => navigate(`/match?resumeId=${liveResume.resume_id}`)}
              >
                Target Job Match
              </Button>
              <Button
                size="sm"
                variant="outline"
                icon={<FileText className="w-3.5 h-3.5" />}
                onClick={() => navigate(`/builder?importResumeId=${liveResume.resume_id}`)}
              >
                Edit in Builder
              </Button>
            </>
          ) : (
            <Button
              size="sm"
              variant="outline"
              icon={<UploadCloud className="w-3.5 h-3.5" />}
              onClick={() => navigate('/upload')}
            >
              Upload Your Resume
            </Button>
          )}
          <Button
            size="sm"
            variant="outline"
            icon={<Bot className="w-3.5 h-3.5 text-indigo-600" />}
            onClick={() => setIsAssistantOpen(true)}
          >
            AI Assistant
          </Button>
          <Badge variant="success" size="md">
            {acceptedCount} / {findings.length} Staged
          </Badge>
        </div>
      </div>

      {/* Deterministic Score & Component Breakdown Card */}
      {liveAnalysis && (
        <Card padding="lg">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
            {/* Overall Score Gauge */}
            <div className="lg:col-span-4 flex flex-col items-center justify-center text-center p-4 rounded-xl bg-slate-50 border border-slate-200/80">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                CareerLens Readiness Estimate
              </span>
              <div className="text-4xl font-extrabold text-slate-900 font-mono mt-2 mb-1">
                {liveAnalysis.overall_score}
                <span className="text-lg font-normal text-slate-400">/100</span>
              </div>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                liveAnalysis.overall_score >= 85
                  ? 'bg-emerald-100 text-emerald-800'
                  : liveAnalysis.overall_score >= 70
                  ? 'bg-indigo-100 text-indigo-800'
                  : 'bg-amber-100 text-amber-800'
              }`}>
                {liveAnalysis.readiness_tier}
              </span>
              <p className="text-[11px] text-slate-500 mt-2 max-w-xs">
                Based on transparent weighted scoring of structure, action impact, verified skills, and readability.
              </p>
            </div>

            {/* Component Breakdown Progress Bars */}
            <div className="lg:col-span-8 space-y-3.5">
              <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Scoring Component Breakdown
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* 1. Structure */}
                <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-2xs">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-semibold text-slate-700 flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5 text-indigo-600" /> Structure & Completeness
                    </span>
                    <span className="font-mono font-bold text-slate-900">
                      {liveAnalysis.component_scores.structure}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-indigo-600 rounded-full transition-all duration-300"
                      style={{ width: `${liveAnalysis.component_scores.structure}%` }}
                    />
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">Weight: 25% • Contact, Education, Skills, Hierarchy</p>
                </div>

                {/* 2. Content Quality */}
                <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-2xs">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-semibold text-slate-700 flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-emerald-600" /> Content Quality & Impact
                    </span>
                    <span className="font-mono font-bold text-slate-900">
                      {liveAnalysis.component_scores.content_quality}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-600 rounded-full transition-all duration-300"
                      style={{ width: `${liveAnalysis.component_scores.content_quality}%` }}
                    />
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">Weight: 30% • Action verbs, metrics, style & grammar</p>
                </div>

                {/* 3. Skill Evidence */}
                <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-2xs">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-semibold text-slate-700 flex items-center gap-1.5">
                      <Cpu className="w-3.5 h-3.5 text-purple-600" /> Skill Evidence Breadth
                    </span>
                    <span className="font-mono font-bold text-slate-900">
                      {liveAnalysis.component_scores.skill_evidence}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-purple-600 rounded-full transition-all duration-300"
                      style={{ width: `${liveAnalysis.component_scores.skill_evidence}%` }}
                    />
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">Weight: 25% • Verified technical skills in context</p>
                </div>

                {/* 4. ATS Readability */}
                <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-2xs">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-semibold text-slate-700 flex items-center gap-1.5">
                      <ShieldCheck className="w-3.5 h-3.5 text-blue-600" /> ATS Machine Readability
                    </span>
                    <span className="font-mono font-bold text-slate-900">
                      {liveAnalysis.component_scores.ats_readability}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-600 rounded-full transition-all duration-300"
                      style={{ width: `${liveAnalysis.component_scores.ats_readability}%` }}
                    />
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">Weight: 20% • Encoding, text density, keyword density</p>
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Grounded AI Explanation & Prioritized Recommendations */}
      {explanation && (
        <Card
          title="Grounded AI Interpretation & Prioritized Action Plan"
          subtitle={`Personalized guidance grounded in your ${liveAnalysis?.overall_score ?? explanation.overall_score}/100 ATS diagnostic`}
          headerAction={
            <div className="flex items-center space-x-2">
              <Badge variant={explanation.is_ai_generated ? 'purple' : 'default'} size="sm">
                <Sparkles className="w-3 h-3 mr-1" />
                {explanation.is_ai_generated ? `AI: ${explanation.provider}` : 'Deterministic Grounded Engine'}
              </Badge>
              <Button
                size="sm"
                variant="outline"
                icon={<Bot className="w-3.5 h-3.5 text-indigo-600" />}
                onClick={() => setIsAssistantOpen(true)}
              >
                Discuss with Assistant
              </Button>
            </div>
          }
        >
          <div className="space-y-4">
            {/* Executive Summary */}
            <div className="p-3.5 bg-indigo-50/60 border border-indigo-100 rounded-xl text-xs text-indigo-950 leading-relaxed">
              <span className="font-semibold text-indigo-900 block mb-1">Executive Summary:</span>
              {explanation.executive_summary}
            </div>

            {/* Prioritized Recommendations */}
            {explanation.prioritized_recommendations.length > 0 && (
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center">
                  <TrendingUp className="w-3.5 h-3.5 mr-1.5 text-indigo-600" />
                  Prioritized Action Items
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {explanation.prioritized_recommendations.map((rec) => (
                    <div
                      key={rec.id}
                      className="p-3 bg-white border border-slate-200 rounded-lg hover:border-indigo-300 transition-colors shadow-2xs flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-semibold text-slate-900">{rec.title}</span>
                          <span
                            className={`text-[10px] px-2 py-0.5 rounded font-semibold uppercase ${
                              rec.priority === 'high'
                                ? 'bg-rose-100 text-rose-700'
                                : rec.priority === 'medium'
                                ? 'bg-amber-100 text-amber-700'
                                : 'bg-slate-100 text-slate-700'
                            }`}
                          >
                            {rec.priority} Priority
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 mb-2">{rec.description}</p>
                      </div>
                      <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-[10px] text-slate-400">
                        <span>Effort: {rec.effort_estimate.replace('_', ' ')}</span>
                        <span className="italic">{rec.priority_reason}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
              <span>{explanation.disclaimer}</span>
              <span className="font-mono text-[10px]">Scores remain mathematically owned by Python backend</span>
            </div>
          </div>
        </Card>
      )}

      {/* Extracted Skills Taxonomy Card */}
      {liveAnalysis && liveAnalysis.extracted_skills && (
        <Card
          title="Extracted Technical Competencies"
          subtitle="Identified from resume text using domain taxonomy and evidence citations"
        >
          <div className="space-y-3">
            {Object.entries(liveAnalysis.extracted_skills).map(([category, skillList]) => {
              if (!skillList || skillList.length === 0) return null;
              return (
                <div key={category} className="flex flex-col sm:flex-row sm:items-start gap-2 pt-2 first:pt-0 border-t first:border-t-0 border-slate-100">
                  <span className="text-xs font-bold text-slate-700 w-36 shrink-0 capitalize flex items-center gap-1.5">
                    <Terminal className="w-3 h-3 text-indigo-500" />
                    {category.replace(/_/g, ' ')}:
                  </span>
                  <div className="flex flex-wrap gap-1.5 flex-1">
                    {skillList.map((skill) => (
                      <span
                        key={skill.name}
                        title={`Evidence: ${skill.evidence_snippet}`}
                        className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-xs font-medium bg-slate-100 text-slate-800 border border-slate-200 cursor-help hover:border-indigo-300 hover:bg-indigo-50/50 transition-colors"
                      >
                        {skill.name}
                        {skill.occurrences > 1 && (
                          <span className="text-[9px] bg-slate-200 text-slate-600 px-1 rounded-full font-mono">
                            {skill.occurrences}x
                          </span>
                        )}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Filter Tabs */}
      <div className="bg-white p-2 rounded-xl border border-slate-200">
        <Tabs
          activeTab={activeFilter}
          onChange={setActiveFilter}
          tabs={[
            { id: 'all', label: 'All Findings', count: findings.length },
            { id: 'error', label: 'Formatting Errors', count: errorCount },
            { id: 'improvement', label: 'Improvements', count: improvementCount },
            { id: 'missing', label: 'Missing Sections', count: missingCount },
            { id: 'keyword', label: 'Keywords', count: keywordCount },
          ]}
        />
      </div>

      {/* Main Dual-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column (5 cols): Extracted Content Preview */}
        <div className="lg:col-span-5 space-y-4">
          <Card
            title="Extracted Document Preview"
            subtitle={
              liveResume
                ? `Extracted with ${liveResume.parser_method} (${liveResume.word_count} words across ${liveResume.page_count} page${liveResume.page_count > 1 ? 's' : ''})`
                : 'Normalized text blocks parsed from uploaded document'
            }
            headerAction={
              <div className="flex items-center gap-1.5">
                <Button
                  size="sm"
                  variant={showRawText ? 'primary' : 'outline'}
                  icon={<FileCode className="w-3 h-3" />}
                  onClick={() => setShowRawText(!showRawText)}
                >
                  {showRawText ? 'View Sections' : 'Raw Text'}
                </Button>
                <Badge variant="outline" size="sm">
                  <FileText className="w-3 h-3 mr-1 text-slate-500" />
                  {showRawText ? 'Full Text' : 'Segmented'}
                </Badge>
              </div>
            }
          >
            {isLoadingLive ? (
              <div className="p-8 text-center text-xs text-slate-500">
                Loading parsed sections from backend...
              </div>
            ) : showRawText ? (
              /* Full Raw Extracted Text View */
              <div className="pt-2">
                <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
                  <span className="font-semibold text-slate-800">Verbatim Extracted Text</span>
                  <span className="font-mono">{rawText.split(/\s+/).filter(Boolean).length} words</span>
                </div>
                <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80 font-mono text-xs text-slate-800 whitespace-pre-wrap leading-relaxed max-h-[480px] overflow-y-auto">
                  {rawText || 'No raw text available.'}
                </div>
              </div>
            ) : (
              /* Section-by-Section Segmented View */
              <>
                {/* Section Selector Buttons */}
                <div className="flex flex-wrap gap-1.5 pb-3 border-b border-slate-100">
                  {sections.map((sec) => (
                    <button
                      key={sec.id}
                      onClick={() => setActiveSectionId(sec.id)}
                      className={`text-xs px-2.5 py-1 rounded-lg font-medium transition-colors cursor-pointer capitalize ${
                        activeSection?.id === sec.id
                          ? 'bg-indigo-600 text-white shadow-xs'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                    >
                      {sec.title}
                    </button>
                  ))}
                </div>

                {/* Selected Section Text Viewer */}
                {activeSection ? (
                  <div className="pt-3">
                    <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
                      <span className="font-semibold text-slate-800">{activeSection.title}</span>
                      <span className="font-mono">{activeSection.wordCount} words</span>
                    </div>
                    <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80 font-mono text-xs text-slate-800 whitespace-pre-line leading-relaxed max-h-[460px] overflow-y-auto">
                      {activeSection.content}
                    </div>
                  </div>
                ) : (
                  <div className="p-6 text-center text-xs text-slate-400">
                    No detected sections available.
                  </div>
                )}
              </>
            )}
          </Card>
        </div>

        {/* Right Column (7 cols): Findings List with Accept/Reject */}
        <div className="lg:col-span-7 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-indigo-600" />
              {activeFilter === 'all' ? 'All Findings' : `${activeFilter.toUpperCase()} Findings`} ({filteredFindings.length})
            </h3>
            <span className="text-xs text-slate-400">
              Interactive review: Accept to stage rewrite
            </span>
          </div>

          {filteredFindings.length === 0 ? (
            <Card padding="lg" className="text-center">
              <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
              <h4 className="text-sm font-bold text-slate-800">No issues in this category</h4>
              <p className="text-xs text-slate-500 mt-1">
                Your resume meets baseline quality requirements for this criteria.
              </p>
            </Card>
          ) : (
            filteredFindings.map((finding) => {
              const badgeInfo = getSeverityBadge(finding.type);
              return (
                <Card
                  key={finding.id}
                  padding="md"
                  className={`transition-all duration-150 ${
                    finding.status === 'accepted'
                      ? 'border-emerald-300 bg-emerald-50/20'
                      : finding.status === 'rejected'
                      ? 'opacity-60 bg-slate-50/50'
                      : 'hover:border-slate-300'
                  }`}
                >
                  <div className="space-y-3">
                    {/* Header: Badge, Location, Status */}
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <Badge variant={badgeInfo.variant} size="sm" icon={badgeInfo.icon}>
                          {badgeInfo.label}
                        </Badge>
                        <span className="text-[11px] font-medium text-slate-500 flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-slate-400" />
                          {finding.location}
                        </span>
                      </div>

                      {finding.status === 'accepted' && (
                        <Badge variant="success" size="sm">
                          <Check className="w-3 h-3 mr-1" /> Staged
                        </Badge>
                      )}
                      {finding.status === 'rejected' && (
                        <Badge variant="outline" size="sm">
                          <X className="w-3 h-3 mr-1" /> Dismissed
                        </Badge>
                      )}
                    </div>

                    {/* Title & Explanation */}
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">{finding.title}</h4>
                      <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                        {finding.explanation}
                      </p>
                    </div>

                    {/* Original vs Proposed Correction */}
                    {finding.originalSnippet && (
                      <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs font-mono">
                        <span className="text-[10px] uppercase font-bold text-slate-400 block mb-0.5">
                          Original Text in Resume:
                        </span>
                        <span className="text-slate-700">{finding.originalSnippet}</span>
                      </div>
                    )}

                    <div className="p-3 rounded-xl bg-indigo-50/70 border border-indigo-200 text-xs">
                      <div className="flex items-center gap-1.5 text-indigo-900 font-semibold mb-1">
                        <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                        Proposed ATS-Optimized Correction:
                      </div>
                      <p className="text-slate-800 font-medium leading-relaxed">
                        {finding.proposedCorrection}
                      </p>
                    </div>

                    {/* Interactive Accept / Reject Controls */}
                    <div className="flex items-center justify-between pt-1 border-t border-slate-100">
                      <span className="text-[11px] text-slate-400">
                        Category: {finding.category}
                      </span>

                      <div className="flex items-center gap-2">
                        {finding.status === 'pending' ? (
                          <>
                            <Button
                              size="sm"
                              variant="outline"
                              icon={<X className="w-3.5 h-3.5 text-slate-500" />}
                              onClick={() => handleStatusChange(finding.id, 'rejected')}
                            >
                              Dismiss
                            </Button>
                            <Button
                              size="sm"
                              variant="primary"
                              icon={<Check className="w-3.5 h-3.5" />}
                              onClick={() => handleStatusChange(finding.id, 'accepted')}
                            >
                              Accept Correction
                            </Button>
                          </>
                        ) : (
                          <Button
                            size="sm"
                            variant="ghost"
                            icon={<RotateCcw className="w-3.5 h-3.5" />}
                            onClick={() => handleResetFinding(finding.id)}
                          >
                            Reset Decision
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </Card>
              );
            })
          )}
        </div>
      </div>
      </>
      )}

      <AIAssistantDrawer
        isOpen={isAssistantOpen}
        onClose={() => setIsAssistantOpen(false)}
        resumeId={resumeIdParam || undefined}
      />

      <Toast toast={toast} onClose={() => setToast(null)} />
    </div>
  );
};
