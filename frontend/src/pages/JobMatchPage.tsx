import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Briefcase,
  Building,
  Search,
  CheckCircle2,
  AlertCircle,
  Quote,
  Sparkles,
  BookOpen,
  MapPin,
  Globe,
  UploadCloud,
  FileText,
  Info,
  Bot,
  TrendingUp,
  ArrowRight,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { ScoreGauge } from '../components/common/ScoreGauge';
import { Tabs } from '../components/common/Tabs';
import type { TabItem } from '../components/common/Tabs';
import { AIAssistantDrawer } from '../components/assistant/AIAssistantDrawer';
import { apiService } from '../services/api';
import type { LiveJobMatchResponse, LiveJobMatchExplanationResponse } from '../types';
import { sampleJobDescriptions } from '../data/mockData';
import { POPULAR_COMPANIES, POPULAR_ROLES } from '../data/suggestions';
import { useAuth } from '../context/AuthContext';

export const JobMatchPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user, getAccessToken } = useAuth();

  // Active Resume Context
  const activeResumeId = searchParams.get('resumeId') || sessionStorage.getItem('latest_resume_id') || '';
  const activeResumeName = sessionStorage.getItem('latest_resume_filename') || 'Uploaded Resume';

  // Target Position Form State
  const [company, setCompany] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [jobUrl, setJobUrl] = useState('');
  const [showUrlInput, setShowUrlInput] = useState(false);
  const [isFetchingUrl, setIsFetchingUrl] = useState(false);
  const [urlFetchError, setUrlFetchError] = useState<string | null>(null);
  const [urlFetchSuccess, setUrlFetchSuccess] = useState<string | null>(null);

  // Analysis State
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<LiveJobMatchResponse | null>(null);
  const [explanation, setExplanation] = useState<LiveJobMatchExplanationResponse | null>(null);
  const [isAssistantOpen, setIsAssistantOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('verified');

  // Initial Load: If an active resume is already available and description has content, run match
  useEffect(() => {
    async function loadInitial() {
      if (activeResumeId && description && description.trim().length >= 40) {
        setIsAnalyzing(true);
        try {
          const token = user ? await getAccessToken() : null;
          const res = await apiService.matchJobLive(
            {
              company,
              role: title,
              job_description: description,
              resume_id: activeResumeId,
            },
            token
          );
          setAnalysisResult(res);
          sessionStorage.setItem('latest_match_id', res.match_id);
          sessionStorage.setItem('latest_target_role', res.role);
          sessionStorage.setItem('latest_target_company', res.company);
          apiService.fetchJobMatchExplanationLive(res.match_id, token)
            .then((exp) => setExplanation(exp))
            .catch((err) => console.warn('Could not load job match explanation:', err));
        } catch {
          // If live call fails (e.g. backend offline), gracefully clear
        } finally {
          setIsAnalyzing(false);
        }
      }
    }
    loadInitial();
  }, [activeResumeId]);

  const handleSelectSample = (sample: typeof sampleJobDescriptions[0]) => {
    setCompany(sample.company);
    setTitle(sample.title);
    setDescription(sample.text);
    setJobUrl('');
    setUrlFetchError(null);
    setUrlFetchSuccess(null);
  };

  const handleFetchUrl = async () => {
    if (!jobUrl.trim()) {
      setUrlFetchError('Please enter a valid HTTP or HTTPS job URL.');
      return;
    }

    setIsFetchingUrl(true);
    setUrlFetchError(null);
    setUrlFetchSuccess(null);

    try {
      const token = user ? await getAccessToken() : null;
      const res = await apiService.fetchJobUrlLive(jobUrl.trim(), token);
      setDescription(res.extracted_text);
      setUrlFetchSuccess(`Successfully retrieved ${res.char_count} characters from posting.`);
    } catch (err: any) {
      setUrlFetchError(err?.message || 'Failed to retrieve job description from URL. Please copy and paste text directly.');
    } finally {
      setIsFetchingUrl(false);
    }
  };

  const handleRunAnalysis = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setErrorMessage(null);

    if (!description.trim() || description.trim().length < 40) {
      setErrorMessage('Please provide a meaningful job description (at least 40 characters) containing responsibilities or qualifications.');
      return;
    }

    setIsAnalyzing(true);
    try {
      const token = user ? await getAccessToken() : null;
      const res = await apiService.matchJobLive(
        {
          company: company.trim(),
          role: title.trim(),
          job_description: description.trim(),
          job_url: jobUrl.trim() || undefined,
          resume_id: activeResumeId || undefined,
        },
        token
      );
      setAnalysisResult(res);
      sessionStorage.setItem('latest_match_id', res.match_id);
      sessionStorage.setItem('latest_target_role', (title || res.role).trim());
      sessionStorage.setItem('latest_target_company', (company || res.company).trim());
      apiService.fetchJobMatchExplanationLive(res.match_id, token)
        .then((exp) => setExplanation(exp))
        .catch((err) => console.warn('Could not load job match explanation:', err));
    } catch (err: any) {
      setErrorMessage(
        err?.message ||
          'Matching failed. Please verify that your resume is uploaded and the backend is running.'
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getTierBadge = (tier: string) => {
    switch (tier?.toLowerCase()) {
      case 'strong match':
        return <Badge variant="success" size="md">Strong Match</Badge>;
      case 'competitive candidate':
        return <Badge variant="info" size="md">Competitive Candidate</Badge>;
      case 'partial fit':
        return <Badge variant="warning" size="md">Partial Fit</Badge>;
      default:
        return <Badge variant="danger" size="md">{tier || 'Early Preparation'}</Badge>;
    }
  };

  const resultTabs: TabItem[] = [
    {
      id: 'verified',
      label: 'Verified Requirements',
      count: analysisResult?.matched_requirements?.length || 0,
      icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />,
    },
    {
      id: 'partial',
      label: 'Partial & Equivalents',
      count: analysisResult?.partial_matches?.length || 0,
      icon: <Sparkles className="w-3.5 h-3.5 text-amber-500" />,
    },
    {
      id: 'missing',
      label: 'Missing Criteria & Gaps',
      count: analysisResult?.missing_evidence?.length || 0,
      icon: <AlertCircle className="w-3.5 h-3.5 text-rose-500" />,
    },
  ];

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Active Resume / Context Indicator */}
      <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2.5">
          <FileText className="w-4 h-4 text-indigo-600 shrink-0" />
          <div>
            <span className="text-slate-500">Active Resume Source: </span>
            {activeResumeId ? (
              <span className="font-semibold text-slate-900 font-mono">
                {activeResumeName} ({activeResumeId.slice(0, 8)}...)
              </span>
            ) : (
              <span className="font-semibold text-amber-600">
                No active resume loaded (will use latest uploaded)
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/upload')}
            icon={<UploadCloud className="w-3.5 h-3.5" />}
          >
            {activeResumeId ? 'Upload New Resume' : 'Upload Resume Now'}
          </Button>
        </div>
      </div>

      <div className="text-left">
        <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
          Company & Job Description Matcher
        </h2>
        <p className="text-slate-600 text-xs sm:text-sm mt-1">
          Evaluate your resume against specific target postings with deterministic requirement extraction, credible equivalence mapping, and verified citation evidence.
        </p>
      </div>

      {/* Input Section Card */}
      <Card
        title="Target Position Specification"
        subtitle="Specify company, target role, and job description text or public posting URL"
        headerAction={
          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-slate-400 mr-1 hidden sm:inline">Pre-fill sample:</span>
            {sampleJobDescriptions.map((sample, idx) => (
              <button
                key={sample.company}
                type="button"
                onClick={() => handleSelectSample(sample)}
                className="text-[11px] px-2 py-0.5 rounded bg-slate-100 hover:bg-indigo-50 hover:text-indigo-600 font-medium text-slate-700 cursor-pointer border border-slate-200 transition-colors"
              >
                Sample {idx + 1}
              </button>
            ))}
          </div>
        }
      >
        <form onSubmit={handleRunAnalysis} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Target Company Name <span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <Building className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  list="job-company-suggestions"
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  placeholder="e.g. Infosys, Google, Microsoft, Amazon"
                  className="w-full pl-9 pr-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-slate-50/50"
                  required
                />
                <datalist id="job-company-suggestions">
                  {POPULAR_COMPANIES.map((c) => (
                    <option key={c} value={c} />
                  ))}
                </datalist>
              </div>
              <div className="flex flex-wrap items-center gap-1 pt-1.5">
                <span className="text-[10px] text-slate-400 font-medium">Quick Suggestions:</span>
                {['Infosys', 'Google', 'Microsoft', 'Amazon', 'Meta', 'Zoho', 'Tata Consultancy Services (TCS)'].map((cName) => (
                  <button
                    key={cName}
                    type="button"
                    onClick={() => setCompany(cName)}
                    className={`text-[10px] px-1.5 py-0.5 rounded border transition-colors cursor-pointer ${
                      company.toLowerCase() === cName.toLowerCase()
                        ? 'bg-indigo-100 text-indigo-700 border-indigo-300 font-semibold'
                        : 'bg-white text-slate-600 border-slate-200 hover:bg-indigo-50 hover:text-indigo-600'
                    }`}
                  >
                    {cName}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Target Job Title <span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <Briefcase className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  list="job-role-suggestions"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Data Analyst, Software Engineer, Full Stack"
                  className="w-full pl-9 pr-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-slate-50/50"
                  required
                />
                <datalist id="job-role-suggestions">
                  {POPULAR_ROLES.map((r) => (
                    <option key={r} value={r} />
                  ))}
                </datalist>
              </div>
              <div className="flex flex-wrap items-center gap-1 pt-1.5">
                <span className="text-[10px] text-slate-400 font-medium">Quick Suggestions:</span>
                {['Data Analyst', 'Software Engineer', 'Full Stack Software Engineer', 'Data Scientist', 'AI / Deep Learning Engineer', 'DevOps Engineer'].map((rName) => (
                  <button
                    key={rName}
                    type="button"
                    onClick={() => setTitle(rName)}
                    className={`text-[10px] px-1.5 py-0.5 rounded border transition-colors cursor-pointer ${
                      title.toLowerCase() === rName.toLowerCase()
                        ? 'bg-indigo-100 text-indigo-700 border-indigo-300 font-semibold'
                        : 'bg-white text-slate-600 border-slate-200 hover:bg-indigo-50 hover:text-indigo-600'
                    }`}
                  >
                    {rName}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* URL Retrieval Section */}
          <div className="border border-slate-200 rounded-xl p-3 bg-slate-50/40 space-y-2">
            <div className="flex items-center justify-between">
              <button
                type="button"
                onClick={() => setShowUrlInput(!showUrlInput)}
                className="flex items-center gap-1.5 text-xs font-semibold text-indigo-700 hover:text-indigo-900 transition-colors cursor-pointer"
              >
                <Globe className="w-3.5 h-3.5" />
                <span>{showUrlInput ? 'Hide Public Job URL Input' : 'Fetch Requirements Directly from Public Job URL (Optional)'}</span>
              </button>
              <span className="text-[10px] text-slate-400">Safe SSRF Protected</span>
            </div>

            {showUrlInput && (
              <div className="space-y-2 pt-1">
                <div className="flex flex-col sm:flex-row gap-2">
                  <input
                    type="url"
                    value={jobUrl}
                    onChange={(e) => setJobUrl(e.target.value)}
                    placeholder="https://boards.greenhouse.io/... or https://jobs.lever.co/..."
                    className="flex-1 px-3 py-1.5 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleFetchUrl}
                    isLoading={isFetchingUrl}
                    icon={<Globe className="w-3.5 h-3.5" />}
                  >
                    Fetch JD
                  </Button>
                </div>
                {urlFetchSuccess && (
                  <p className="text-[11px] text-emerald-600 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    {urlFetchSuccess}
                  </p>
                )}
                {urlFetchError && (
                  <p className="text-[11px] text-rose-600 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {urlFetchError}
                  </p>
                )}
              </div>
            )}
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-semibold text-slate-700">
                Job Description Text <span className="text-rose-500">*</span>
              </label>
              <span className="text-[11px] text-slate-400 font-mono">
                {description.length} characters (min 40)
              </span>
            </div>
            <textarea
              rows={6}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Paste responsibilities, qualification bullets, and requirements from the job posting..."
              className="w-full p-3 text-xs font-mono border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-slate-50/50 leading-relaxed"
              required
            />
          </div>

          {errorMessage && (
            <div className="p-3.5 rounded-xl border border-rose-200 bg-rose-50 text-xs text-rose-800 flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-semibold">Matching Error</p>
                <p className="mt-0.5 text-rose-700">{errorMessage}</p>
              </div>
            </div>
          )}

          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
            <div className="flex items-center gap-2 self-start sm:self-auto">
              <button
                type="button"
                onClick={() => {
                  setCompany('');
                  setTitle('');
                  setDescription('');
                  setJobUrl('');
                  setAnalysisResult(null);
                  setExplanation(null);
                  setErrorMessage(null);
                }}
                className="px-2.5 py-1 text-xs text-slate-500 hover:text-slate-800 border border-slate-200 rounded-lg bg-white hover:bg-slate-50 cursor-pointer"
              >
                Clear Inputs
              </button>
              <button
                type="button"
                onClick={() => {
                  setCompany(sampleJobDescriptions[0].company);
                  setTitle(sampleJobDescriptions[0].title);
                  setDescription(sampleJobDescriptions[0].text);
                  setErrorMessage(null);
                }}
                className="px-2.5 py-1 text-xs text-indigo-700 hover:text-indigo-900 border border-indigo-200 bg-indigo-50/50 hover:bg-indigo-100/50 rounded-lg cursor-pointer"
              >
                Fill Sample Job
              </button>
            </div>
            <Button
              type="submit"
              variant="primary"
              size="md"
              isLoading={isAnalyzing}
              icon={<Search className="w-4 h-4" />}
            >
              Analyze Match Alignment
            </Button>
          </div>
        </form>
      </Card>

      {/* Empty State when no match performed */}
      {!analysisResult && !isAnalyzing && (
        <div className="p-8 text-center bg-slate-50/70 border border-dashed border-slate-300 rounded-2xl space-y-2">
          <Briefcase className="w-8 h-8 text-slate-400 mx-auto" />
          <h4 className="text-sm font-bold text-slate-800">No Job Match Performed Yet</h4>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Enter a company name, target role title, and job requirements above, then click <strong>Analyze Match Alignment</strong> to evaluate skill gaps, ATS keywords, and candidate suitability against your active resume.
          </p>
        </div>
      )}

      {/* Analysis Results Display */}
      {analysisResult && (
        <div className="space-y-6">
          {/* Action Navigation Banner */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 bg-slate-900 text-white rounded-xl gap-4 shadow-sm">
            <div>
              <h4 className="text-sm font-bold text-white flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                Match Computed for {analysisResult.company} — {analysisResult.role}
              </h4>
              <p className="text-xs text-slate-300 mt-0.5">
                Take action on your missing requirements by generating a targeted learning roadmap or saving this assessment report.
              </p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Button
                size="sm"
                variant="outline"
                className="bg-white/10 hover:bg-white/20 text-white border-white/20"
                onClick={() => navigate('/roadmap')}
                icon={<ArrowRight className="w-3.5 h-3.5" />}
                iconPosition="right"
              >
                Create Learning Roadmap
              </Button>
              <Button
                size="sm"
                variant="primary"
                onClick={() => navigate('/reports')}
              >
                Save Evaluation Report
              </Button>
            </div>
          </div>

          {/* Top Score Summary Banner */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="flex items-center gap-3">
              <ScoreGauge
                score={analysisResult.overall_match_score}
                title="Overall Fit"
                size="md"
                showLabel={false}
              />
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Overall Fit
                </span>
                <p className="text-2xl font-bold font-mono text-slate-900">
                  {analysisResult.overall_match_score}%
                </p>
                <div className="mt-1">
                  {getTierBadge(analysisResult.readiness_tier)}
                </div>
              </div>
            </Card>

            <Card className="flex items-center gap-3">
              <ScoreGauge
                score={analysisResult.hard_skill_match_score}
                title="Required"
                size="md"
                showLabel={false}
              />
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Required Skills
                </span>
                <p className="text-2xl font-bold font-mono text-slate-900">
                  {analysisResult.hard_skill_match_score}%
                </p>
                <p className="text-[11px] text-slate-500 mt-0.5">50% weight in fit score</p>
              </div>
            </Card>

            <Card className="flex items-center gap-3">
              <ScoreGauge
                score={analysisResult.preferred_match_score}
                title="Preferred"
                size="md"
                showLabel={false}
              />
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Preferred Skills
                </span>
                <p className="text-2xl font-bold font-mono text-slate-900">
                  {analysisResult.preferred_match_score}%
                </p>
                <p className="text-[11px] text-slate-500 mt-0.5">20% weight in fit score</p>
              </div>
            </Card>

            <Card className="flex items-center gap-3">
              <ScoreGauge
                score={analysisResult.evidence_strength_score}
                title="Evidence"
                size="md"
                showLabel={false}
              />
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Evidence Strength
                </span>
                <p className="text-2xl font-bold font-mono text-slate-900">
                  {analysisResult.evidence_strength_score}%
                </p>
                <p className="text-[11px] text-slate-500 mt-0.5">Experience & project proof</p>
              </div>
            </Card>
          </div>

          {/* Evidence Summary Alert */}
          <div className="p-4 rounded-xl border border-indigo-200 bg-indigo-50/50 flex items-start gap-3 text-xs">
            <Sparkles className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-indigo-950">Deterministic Evidence Breakdown</p>
              <p className="text-slate-700 mt-0.5 leading-relaxed">
                {analysisResult.verified_evidence_summary}
              </p>
            </div>
          </div>

          {/* Phase 8 Grounded AI Explanation & Gap Closure Plan */}
          {explanation && (
            <Card
              title="Grounded AI Compatibility Analysis & Gap Closure Plan"
              subtitle={`Alignment analysis for ${explanation.role} at ${explanation.company}`}
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
                    Discuss Match with Assistant
                  </Button>
                </div>
              }
            >
              <div className="space-y-4">
                <div className="p-3.5 bg-indigo-50/70 border border-indigo-100 rounded-xl text-xs text-indigo-950 leading-relaxed">
                  <span className="font-semibold text-indigo-900 block mb-1">Executive Match Summary:</span>
                  {explanation.match_summary}
                </div>

                {explanation.prioritized_recommendations.length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center">
                      <TrendingUp className="w-3.5 h-3.5 mr-1.5 text-indigo-600" />
                      Priority Actions to Maximize Role Fit
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
                  <span className="font-mono text-[10px]">Deterministic Match Score: {explanation.overall_match_score}% (Immutable)</span>
                </div>
              </div>
            </Card>
          )}

          {/* Tabs for Requirements: Verified, Partial, Missing */}
          <div className="space-y-4">
            <Tabs
              tabs={resultTabs}
              activeTab={activeTab}
              onChange={setActiveTab}
            />

            {/* TAB 1: Verified Requirements */}
            {activeTab === 'verified' && (
              <div className="space-y-3">
                {analysisResult.matched_requirements.length === 0 ? (
                  <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200 text-xs text-slate-500">
                    No fully verified requirements found. Check Partial and Missing tabs for actionable gaps.
                  </div>
                ) : (
                  analysisResult.matched_requirements.map((req) => (
                    <div
                      key={req.name}
                      className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-xs space-y-2 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                          <span className="font-bold text-slate-900">{req.name}</span>
                          <Badge
                            variant={req.importance === 'required' ? 'default' : 'purple'}
                            size="sm"
                          >
                            {req.importance}
                          </Badge>
                          {req.demonstrated_in_project && (
                            <Badge variant="success" size="sm">
                              Project / Work Evidence
                            </Badge>
                          )}
                        </div>
                        <Badge variant="outline" size="sm">
                          {req.confidence}% Match
                        </Badge>
                      </div>

                      {req.evidence_quote && (
                        <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/80 text-slate-700 italic text-[11px] flex items-start gap-2">
                          <Quote className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5 not-italic" />
                          <span>"{req.evidence_quote}"</span>
                        </div>
                      )}

                      <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-slate-400" />
                          Location in Resume: {req.location || 'Skills / Experience'}
                        </span>
                        <span className="text-slate-500">{req.explanation}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* TAB 2: Partial Matches & Equivalents */}
            {activeTab === 'partial' && (
              <div className="space-y-3">
                {analysisResult.partial_matches.length === 0 ? (
                  <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200 text-xs text-slate-500">
                    No partial or equivalent matches detected.
                  </div>
                ) : (
                  analysisResult.partial_matches.map((req) => (
                    <div
                      key={req.name}
                      className="p-3.5 rounded-xl border border-amber-200 bg-amber-50/20 shadow-xs space-y-2 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Sparkles className="w-4 h-4 text-amber-500 shrink-0" />
                          <span className="font-bold text-slate-900">{req.name}</span>
                          <Badge variant="warning" size="sm">
                            {req.importance}
                          </Badge>
                          {req.equivalent_found && (
                            <Badge variant="info" size="sm">
                              Equivalent: {req.equivalent_found}
                            </Badge>
                          )}
                        </div>
                        <Badge variant="outline" size="sm">
                          {req.confidence}% Credible Fit
                        </Badge>
                      </div>

                      <p className="text-slate-700 text-xs">{req.explanation}</p>

                      {req.recommended_action && (
                        <div className="p-2.5 rounded-lg bg-white border border-amber-200 text-amber-900 text-[11px] flex items-start gap-2">
                          <BookOpen className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                          <span>
                            <strong>Action to Strengthen:</strong> {req.recommended_action}
                          </span>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            )}

            {/* TAB 3: Missing Criteria & Gaps */}
            {activeTab === 'missing' && (
              <div className="space-y-3">
                {analysisResult.missing_evidence.length === 0 ? (
                  <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200 text-xs text-emerald-600 font-medium">
                    Excellent! All required and preferred criteria from this job posting were detected in your resume.
                  </div>
                ) : (
                  analysisResult.missing_evidence.map((gap) => (
                    <div
                      key={gap.name}
                      className="p-3.5 rounded-xl border border-rose-200 bg-rose-50/20 shadow-xs space-y-2 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
                          <span className="font-bold text-slate-900">{gap.name}</span>
                          <Badge
                            variant={gap.importance === 'required' ? 'danger' : 'warning'}
                            size="sm"
                          >
                            {gap.importance}
                          </Badge>
                        </div>
                        <Badge variant="outline" size="sm">
                          Missing in Resume
                        </Badge>
                      </div>

                      <p className="text-slate-700 text-xs">{gap.explanation}</p>

                      {gap.recommended_action && (
                        <div className="p-2.5 rounded-lg bg-white border border-rose-200 text-rose-900 text-[11px] flex items-start gap-2">
                          <BookOpen className="w-3.5 h-3.5 text-rose-600 shrink-0 mt-0.5" />
                          <span>
                            <strong>Preparation Guide:</strong> {gap.recommended_action}
                          </span>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Actionable Strategy Recommendations */}
          {analysisResult.recommendations && analysisResult.recommendations.length > 0 && (
            <Card
              title="Tailored Application Strategy"
              subtitle={`Tactical improvements for your application to ${analysisResult.company}`}
            >
              <ul className="space-y-2.5 text-xs">
                {analysisResult.recommendations.map((rec, index) => (
                  <li
                    key={index}
                    className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 flex items-start gap-3 text-slate-700"
                  >
                    <span className="w-4 h-4 rounded-full bg-indigo-100 text-indigo-700 font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5">
                      {index + 1}
                    </span>
                    <span className="leading-relaxed">{rec}</span>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {/* Official Disclaimer */}
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex items-start gap-3 text-xs text-slate-500 leading-relaxed">
            <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-slate-700">Official Evaluation Disclaimer</p>
              <p className="mt-0.5">
                {analysisResult.disclaimer ||
                  'The CareerLens compatibility score is a deterministic employability estimate based on text parsing. It is designed for student readiness preparation and does not constitute an official employer assessment or employment guarantee.'}
              </p>
            </div>
          </div>
        </div>
      )}

      <AIAssistantDrawer
        isOpen={isAssistantOpen}
        onClose={() => setIsAssistantOpen(false)}
        matchId={analysisResult?.match_id}
        resumeId={activeResumeId || undefined}
      />
    </div>
  );
};
