import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Share2,
  ExternalLink,
  Edit2,
  Check,
  Code2,
  Award,
  Globe,
  BarChart2,
  Lock,
  GitBranch,
  ShieldCheck,
  AlertCircle,
  CheckCircle2,
  Sparkles,
  BookOpen,
  FolderGit2,
  UploadCloud,
  FileText,
  Info,
  RefreshCw,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { ScoreGauge } from '../components/common/ScoreGauge';
import { Tabs } from '../components/common/Tabs';
import type { TabItem } from '../components/common/Tabs';
import { Toast } from '../components/common/Toast';
import type { ToastMessage } from '../components/common/Toast';
import { apiService } from '../services/api';
import type {
  LiveProfileConnectionItem,
  LiveEvidenceVerificationResponse,
} from '../types';
import { useAuth } from '../context/AuthContext';

export const ProfileConnectionsPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user, getAccessToken } = useAuth();

  const [activeTab, setActiveTab] = useState<'profiles' | 'verification'>('profiles');
  const [connections, setConnections] = useState<LiveProfileConnectionItem[]>([]);
  const [isLoadingConnections, setIsLoadingConnections] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [tempUrl, setTempUrl] = useState<string>('');
  const [isSaving, setIsSaving] = useState(false);
  const [toast, setToast] = useState<ToastMessage | null>(null);

  // Evidence Verification State
  const activeResumeId = searchParams.get('resumeId') || sessionStorage.getItem('latest_resume_id') || '';
  const activeResumeName = sessionStorage.getItem('latest_resume_filename') || 'Uploaded Resume';
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<LiveEvidenceVerificationResponse | null>(null);
  const [verificationError, setVerificationError] = useState<string | null>(null);

  const loadConnections = async () => {
    setIsLoadingConnections(true);
    try {
      const token = user ? await getAccessToken() : null;
      const res = await apiService.fetchProfileConnectionsLive(token);
      setConnections(res.connections);
    } catch (err: any) {
      console.warn('Could not fetch live profile connections, using fallback:', err);
      // Fallback to initial mock if backend unreachable
      const fallback = await apiService.getProfileConnections();
      setConnections(
        fallback.map((f) => ({
          id: f.id,
          name: f.name,
          icon_name: f.iconName,
          description: f.description,
          status: f.status,
          username_or_url: f.usernameOrUrl,
          last_synced: f.lastSynced,
          retrieval_status: f.status === 'connected' ? 'Connected (Demo)' : 'Not Connected',
          metrics_preview: f.metricsPreview || [],
        }))
      );
    } finally {
      setIsLoadingConnections(false);
    }
  };

  useEffect(() => {
    loadConnections();
  }, [user]);

  const getPlatformIcon = (iconName: string) => {
    switch (iconName) {
      case 'Github':
        return (
          <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
            <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
          </svg>
        );
      case 'Linkedin':
        return (
          <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
            <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9h2.79v8.37H6.46v-8.37M7.86 6.54a1.63 1.63 0 1 0 0 3.26 1.63 1.63 0 0 0 0-3.26z" />
          </svg>
        );
      case 'Code2':
        return <Code2 className="w-5 h-5" />;
      case 'Award':
        return <Award className="w-5 h-5" />;
      case 'Globe':
        return <Globe className="w-5 h-5" />;
      case 'BarChart2':
        return <BarChart2 className="w-5 h-5" />;
      default:
        return <GitBranch className="w-5 h-5" />;
    }
  };

  const handleStartEdit = (conn: LiveProfileConnectionItem) => {
    setEditingId(conn.id);
    setTempUrl(conn.username_or_url || '');
  };

  const handleSaveConnection = async (id: string) => {
    if (!tempUrl.trim()) {
      setToast({
        id: Math.random().toString(),
        type: 'error',
        title: 'Validation Error',
        message: 'Please enter a valid username or URL.',
      });
      return;
    }

    setIsSaving(true);
    try {
      const token = user ? await getAccessToken() : null;
      const updated = await apiService.updateProfileConnectionLive(id, tempUrl.trim(), token);
      setConnections((prev) => prev.map((c) => (c.id === id ? updated : c)));
      setEditingId(null);
      setToast({
        id: Math.random().toString(),
        type: 'success',
        title: 'Profile Connected',
        message: `Successfully verified and connected ${updated.name}.`,
      });
    } catch (err: any) {
      setToast({
        id: Math.random().toString(),
        type: 'error',
        title: 'Connection Failed',
        message: err?.message || 'Could not verify profile. Please verify handle format.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDisconnect = async (id: string) => {
    try {
      const token = user ? await getAccessToken() : null;
      await apiService.disconnectProfileLive(id, token);
      setConnections((prev) =>
        prev.map((c) =>
          c.id === id
            ? {
                ...c,
                status: 'not_connected',
                username_or_url: '',
                last_synced: undefined,
                retrieval_status: 'Disconnected',
                metrics_preview: [],
                metadata: {},
              }
            : c
        )
      );
      setToast({
        id: Math.random().toString(),
        type: 'info',
        title: 'Profile Disconnected',
        message: `Detached ${id} profile handle.`,
      });
    } catch (err: any) {
      setToast({
        id: Math.random().toString(),
        type: 'error',
        title: 'Disconnect Error',
        message: err?.message || 'Failed to disconnect profile.',
      });
    }
  };

  const handleRunVerification = async () => {
    setIsVerifying(true);
    setVerificationError(null);
    try {
      const token = user ? await getAccessToken() : null;
      const res = await apiService.verifyEvidenceLive(
        activeResumeId || undefined,
        undefined,
        token
      );
      setVerificationResult(res);
      setActiveTab('verification');
    } catch (err: any) {
      setVerificationError(
        err?.message || 'Evidence verification failed. Please verify that a resume is uploaded and your backend is running.'
      );
    } finally {
      setIsVerifying(false);
    }
  };

  const githubConn = connections.find((c) => c.id === 'github' && c.status === 'connected');
  const githubRepos: any[] = githubConn?.metadata?.repositories || [];

  const mainTabs: TabItem[] = [
    {
      id: 'profiles',
      label: 'Connected Profiles & Repositories',
      count: connections.filter((c) => c.status === 'connected').length,
      icon: <Globe className="w-3.5 h-3.5 text-indigo-500" />,
    },
    {
      id: 'verification',
      label: 'Resume Claims Verification',
      count: verificationResult?.total_claims || undefined,
      icon: <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />,
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
                No active resume loaded (upload a resume to verify claims)
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {activeResumeId ? (
            <Button
              variant="primary"
              size="sm"
              onClick={handleRunVerification}
              isLoading={isVerifying}
              icon={<ShieldCheck className="w-3.5 h-3.5" />}
            >
              Verify Resume Claims
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/upload')}
              icon={<UploadCloud className="w-3.5 h-3.5" />}
            >
              Upload Resume Now
            </Button>
          )}
        </div>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Professional Profile Connections & Evidence
          </h2>
          <p className="text-slate-600 text-xs sm:text-sm mt-0.5">
            Connect developer profiles to cross-reference resume project claims with public GitHub repositories, test suites, and language telemetry.
          </p>
        </div>
      </div>

      {/* Security Guarantee Notice */}
      <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/60 flex items-start gap-3.5 text-xs text-emerald-950">
        <div className="p-2 bg-emerald-100 rounded-lg text-emerald-700 shrink-0 mt-0.5">
          <Lock className="w-4 h-4" />
        </div>
        <div>
          <h4 className="font-bold text-sm text-emerald-950">Strict Privacy & Zero-Password Protocol</h4>
          <p className="mt-1 leading-relaxed text-emerald-900/90">
            CareerLens never requests account passwords, private tokens, or proprietary access keys.
            Only public repositories and observable metrics (languages, documentation, test artifacts) are audited to confirm technical claims.
          </p>
        </div>
      </div>

      {/* Main Tabs */}
      <Tabs
        tabs={mainTabs}
        activeTab={activeTab}
        onChange={(tabId) => setActiveTab(tabId as any)}
      />

      {/* TAB 1: Connected Profiles */}
      {activeTab === 'profiles' && (
        <div className="space-y-6">
          {isLoadingConnections ? (
            <div className="p-12 text-center text-xs text-slate-500 bg-white rounded-xl border border-slate-200">
              <RefreshCw className="w-5 h-5 animate-spin text-indigo-600 mx-auto mb-2" />
              Loading profile integrations...
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {connections.map((conn) => {
                const isEditing = editingId === conn.id;
                const isConnected = conn.status === 'connected';

              return (
                <Card
                  key={conn.id}
                  className={`flex flex-col justify-between transition-all duration-150 ${
                    isConnected ? 'border-slate-300' : 'border-dashed border-slate-300 bg-slate-50/30'
                  }`}
                >
                  <div className="space-y-3">
                    {/* Header: Icon, Name, Status Badge */}
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                            isConnected
                              ? 'bg-slate-900 text-white shadow-xs'
                              : 'bg-slate-100 text-slate-500'
                          }`}
                        >
                          {getPlatformIcon(conn.icon_name)}
                        </div>
                        <div>
                          <h3 className="text-sm font-bold text-slate-900">{conn.name}</h3>
                          <p className="text-[11px] text-slate-400">
                            {conn.last_synced ? `Synced ${conn.last_synced}` : 'No sync recorded'}
                          </p>
                        </div>
                      </div>

                      <Badge variant={isConnected ? 'success' : 'default'} size="sm">
                        {isConnected ? 'Connected' : 'Not Linked'}
                      </Badge>
                    </div>

                    {/* Description */}
                    <p className="text-xs text-slate-600 leading-relaxed min-h-[36px]">
                      {conn.description}
                    </p>

                    {/* Retrieval status notice */}
                    {conn.retrieval_status && (
                      <p className="text-[11px] text-indigo-700 font-medium bg-indigo-50/50 p-2 rounded-lg border border-indigo-100">
                        {conn.retrieval_status}
                      </p>
                    )}

                    {/* URL or Edit Box */}
                    {isEditing ? (
                      <div className="space-y-2 pt-1">
                        <label className="text-[11px] font-semibold text-slate-700 block">
                          Enter Public Profile URL or Handle:
                        </label>
                        <input
                          type="text"
                          value={tempUrl}
                          onChange={(e) => setTempUrl(e.target.value)}
                          placeholder={`e.g. ${conn.name.toLowerCase()}.com/username or @username`}
                          className="w-full px-3 py-1.5 text-xs border border-indigo-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                          autoFocus
                        />
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => setEditingId(null)}
                          >
                            Cancel
                          </Button>
                          <Button
                            size="sm"
                            variant="primary"
                            isLoading={isSaving}
                            icon={<Check className="w-3.5 h-3.5" />}
                            onClick={() => handleSaveConnection(conn.id)}
                          >
                            Save
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div>
                        {isConnected ? (
                          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs flex items-center justify-between">
                            <span className="font-mono text-slate-700 truncate max-w-[200px]">
                              {conn.username_or_url}
                            </span>
                            <a
                              href={
                                conn.username_or_url.startsWith('http')
                                  ? conn.username_or_url
                                  : `https://${conn.username_or_url}`
                              }
                              target="_blank"
                              rel="noreferrer"
                              className="text-indigo-600 hover:text-indigo-800 p-1"
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                            </a>
                          </div>
                        ) : (
                          <div className="p-2 rounded-lg bg-slate-100/60 text-slate-400 text-center text-xs italic">
                            No account configured
                          </div>
                        )}

                        {/* Verified Metrics Preview */}
                        {conn.metrics_preview && conn.metrics_preview.length > 0 && (
                          <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-slate-100 text-center">
                            {conn.metrics_preview.map((m) => (
                              <div key={m.label}>
                                <p className="text-[10px] text-slate-400 uppercase font-semibold">
                                  {m.label}
                                </p>
                                <p className="text-xs font-bold font-mono text-slate-800 mt-0.5 truncate" title={m.value}>
                                  {m.value}
                                </p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Bottom Action Footer */}
                  {!isEditing && (
                    <div className="pt-4 mt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                      {isConnected ? (
                        <>
                          <button
                            type="button"
                            onClick={() => handleDisconnect(conn.id)}
                            className="text-slate-400 hover:text-rose-600 font-medium cursor-pointer transition-colors"
                          >
                            Disconnect
                          </button>
                          <Button
                            size="sm"
                            variant="outline"
                            icon={<Edit2 className="w-3 h-3" />}
                            onClick={() => handleStartEdit(conn)}
                          >
                            Edit URL
                          </Button>
                        </>
                      ) : (
                        <Button
                          size="sm"
                          variant="primary"
                          className="w-full"
                          icon={<Share2 className="w-3.5 h-3.5" />}
                          onClick={() => handleStartEdit(conn)}
                        >
                          Connect Profile
                        </Button>
                      )}
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
          )}

          {/* GitHub Repositories List (when GitHub connected) */}
          {githubConn && githubRepos.length > 0 && (
            <Card
              title="Discovered GitHub Public Repositories"
              subtitle={`Extracted ${githubRepos.length} public codebases with automated test detection`}
              headerAction={
                <Badge variant="success" size="sm">
                  {githubRepos.length} Repositories
                </Badge>
              }
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {githubRepos.map((repo) => (
                  <div
                    key={repo.name}
                    className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <FolderGit2 className="w-4 h-4 text-indigo-600 shrink-0" />
                        <span className="font-bold text-slate-900">{repo.name}</span>
                      </div>
                      <Badge variant="outline" size="sm">
                        {repo.primary_language}
                      </Badge>
                    </div>

                    <p className="text-slate-600 text-[11px] line-clamp-2">
                      {repo.description}
                    </p>

                    <div className="flex items-center justify-between pt-1 text-[11px]">
                      <div className="flex items-center gap-2">
                        {repo.has_test_suite ? (
                          <Badge variant="success" size="sm">
                            Tests Detected
                          </Badge>
                        ) : (
                          <span className="text-slate-400">No test suite</span>
                        )}
                        {repo.stars > 0 && (
                          <span className="text-amber-600 font-semibold">★ {repo.stars}</span>
                        )}
                      </div>
                      <a
                        href={repo.html_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-indigo-600 hover:text-indigo-800 flex items-center gap-1 font-medium"
                      >
                        <span>View Code</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}

      {/* TAB 2: Resume Claims Verification */}
      {activeTab === 'verification' && (
        <div className="space-y-6">
          {verificationError && (
            <div className="p-4 rounded-xl border border-rose-200 bg-rose-50 text-xs text-rose-800 flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Verification Error</p>
                <p className="mt-0.5 text-rose-700">{verificationError}</p>
              </div>
            </div>
          )}

          {!verificationResult && !isVerifying && (
            <div className="p-12 text-center bg-white rounded-xl border border-slate-200 space-y-4">
              <ShieldCheck className="w-12 h-12 text-indigo-500 mx-auto" />
              <div className="max-w-md mx-auto">
                <h3 className="font-bold text-slate-900 text-base">Verify Resume Claims Against External Profiles</h3>
                <p className="text-xs text-slate-500 mt-1">
                  CareerLens will cross-reference your resume project claims and technical competencies with your connected GitHub repositories, commit languages, README documentation, and test suites.
                </p>
              </div>
              <Button
                variant="primary"
                size="md"
                onClick={handleRunVerification}
                isLoading={isVerifying}
                icon={<ShieldCheck className="w-4 h-4" />}
              >
                Run Evidence Verification
              </Button>
            </div>
          )}

          {verificationResult && (
            <div className="space-y-6">
              {/* Top Score Banner */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card className="flex items-center gap-3">
                  <ScoreGauge
                    score={verificationResult.verification_score}
                    title="Verification"
                    size="md"
                    showLabel={false}
                  />
                  <div>
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                      Evidence Fit
                    </span>
                    <p className="text-2xl font-bold font-mono text-slate-900">
                      {verificationResult.verification_score}%
                    </p>
                    <Badge variant="success" size="sm" className="mt-1">
                      {verificationResult.supported_claims} Supported
                    </Badge>
                  </div>
                </Card>

                <Card className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold text-lg">
                    {verificationResult.supported_claims}
                  </div>
                  <div>
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                      Supported Claims
                    </span>
                    <p className="text-sm font-bold text-slate-800 mt-0.5">
                      Code & Tests Verified
                    </p>
                    <p className="text-[11px] text-slate-400">In public GitHub repos</p>
                  </div>
                </Card>

                <Card className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold text-lg">
                    {verificationResult.partially_supported_claims}
                  </div>
                  <div>
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                      Partially Supported
                    </span>
                    <p className="text-sm font-bold text-slate-800 mt-0.5">
                      Doc/Partial Tech Match
                    </p>
                    <p className="text-[11px] text-slate-400">Needs test artifacts</p>
                  </div>
                </Card>

                <Card className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-slate-100 text-slate-600 flex items-center justify-center font-bold text-lg">
                    {verificationResult.unverified_claims + verificationResult.inaccessible_claims}
                  </div>
                  <div>
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                      Unverified / Private
                    </span>
                    <p className="text-sm font-bold text-slate-800 mt-0.5">
                      No Public Repo
                    </p>
                    <p className="text-[11px] text-slate-400">May be private or enterprise</p>
                  </div>
                </Card>
              </div>

              {/* Summary Alert */}
              <div className="p-4 rounded-xl border border-indigo-200 bg-indigo-50/50 flex items-start gap-3 text-xs">
                <Sparkles className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-indigo-950">Evidence Verification Summary</p>
                  <p className="text-slate-700 mt-0.5 leading-relaxed">
                    {verificationResult.summary_message}
                  </p>
                </div>
              </div>

              {/* Claims Cards */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-slate-900">
                    Evaluated Resume Claims ({verificationResult.claims.length})
                  </h3>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleRunVerification}
                    isLoading={isVerifying}
                    icon={<RefreshCw className="w-3.5 h-3.5" />}
                  >
                    Re-verify
                  </Button>
                </div>

                <div className="space-y-4">
                  {verificationResult.claims.map((claim) => {
                    const isSupported = claim.status === 'supported';
                    const isPartial = claim.status === 'partially_supported';
                    const isUnverified = claim.status === 'unverified';

                    let badgeVariant: 'success' | 'warning' | 'default' | 'danger' = 'default';
                    if (isSupported) badgeVariant = 'success';
                    else if (isPartial) badgeVariant = 'warning';
                    else if (isUnverified) badgeVariant = 'default';
                    else badgeVariant = 'danger';

                    return (
                      <div
                        key={claim.claim_id}
                        className="p-4 rounded-xl border border-slate-200 bg-white shadow-xs space-y-3 text-xs"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              {isSupported && <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />}
                              {isPartial && <Sparkles className="w-4 h-4 text-amber-500 shrink-0" />}
                              {isUnverified && <AlertCircle className="w-4 h-4 text-slate-400 shrink-0" />}
                              <span className="font-bold text-slate-900 text-sm">
                                {claim.project_name || claim.original_claim.split(':')[0]}
                              </span>
                              <Badge variant="outline" size="sm" className="capitalize">
                                {claim.claim_type.replace('_', ' ')}
                              </Badge>
                            </div>
                            <p className="text-slate-600 italic text-[11px]">
                              "{claim.original_claim}"
                            </p>
                          </div>

                          <Badge variant={badgeVariant} size="sm" className="capitalize shrink-0">
                            {claim.status.replace('_', ' ')}
                          </Badge>
                        </div>

                        {/* Evidence Source & Excerpt */}
                        <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 space-y-2">
                          <div className="flex items-center justify-between text-[11px]">
                            <span className="font-semibold text-indigo-900">
                              Evidence Source: {claim.evidence_source}
                            </span>
                            {claim.repository_url && (
                              <a
                                href={claim.repository_url}
                                target="_blank"
                                rel="noreferrer"
                                className="text-indigo-600 hover:text-indigo-800 flex items-center gap-1 font-medium"
                              >
                                <span>Inspect Repo</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            )}
                          </div>
                          {claim.supporting_excerpt && (
                            <p className="text-slate-700 font-mono text-[11px] leading-relaxed">
                              {claim.supporting_excerpt}
                            </p>
                          )}
                          <div className="flex items-center gap-2 pt-1 text-[10px]">
                            {claim.has_test_suite && (
                              <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-semibold">
                                ✓ Automated Tests Present
                              </span>
                            )}
                            {claim.has_documentation && (
                              <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-semibold">
                                ✓ README Documentation
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Reason & Action */}
                        <div className="space-y-1.5 text-[11px]">
                          <p className="text-slate-700">
                            <strong>Audit Determination:</strong> {claim.reason}
                          </p>
                          {claim.evidence_limitations && (
                            <p className="text-slate-500">
                              <strong>Evidence Limitations:</strong> {claim.evidence_limitations}
                            </p>
                          )}
                          {claim.recommended_action && (
                            <div className="p-2.5 rounded-lg bg-indigo-50/50 border border-indigo-100 text-indigo-900 flex items-start gap-2">
                              <BookOpen className="w-3.5 h-3.5 text-indigo-600 shrink-0 mt-0.5" />
                              <span>
                                <strong>Recommended Next Step:</strong> {claim.recommended_action}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Official Disclaimer */}
              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex items-start gap-3 text-xs text-slate-500 leading-relaxed">
                <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-slate-700">Evidence Verification Disclaimer</p>
                  <p className="mt-0.5">{verificationResult.disclaimer}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      <Toast toast={toast} onClose={() => setToast(null)} />
    </div>
  );
};
