import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Download,
  Sparkles,
  Check,
  Plus,
  Trash2,
  History,
  CheckCircle2,
  AlertCircle,
  FileText,
  TrendingUp,
  RefreshCw,
  Briefcase,
  GraduationCap,
  FolderGit2,
  Terminal,
  User,
  X,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Toast } from '../components/common/Toast';
import type { ToastMessage } from '../components/common/Toast';
import { apiService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import type {
  LiveResumeBuilderData,
  LiveResumeVersionItem,
  LiveAISuggestionItem,
  LiveBuilderAnalysisResponse,
  LiveExperienceEntry,
  LiveProjectEntry,
  LiveEducationEntry,
} from '../types';

export const sampleTemplateData: LiveResumeBuilderData = {
  contact: {
    full_name: 'Alex Rivera',
    email: 'alex.rivera@example.com',
    phone: '(555) 019-2834',
    location: 'Seattle, WA',
    linkedin: 'linkedin.com/in/alexrivera-tech',
    github: 'github.com/alexrivera-tech',
    portfolio: '',
  },
  summary:
    'Full-stack software engineer with 2+ years of hands-on experience developing web applications using React, TypeScript, Python (FastAPI), and PostgreSQL. Proven track record of optimizing database query latency by 35% and building responsive, accessible client interfaces.',
  education: [
    {
      id: 'edu-1',
      school: 'University of Washington',
      degree: 'B.S. in Computer Science',
      field_of_study: 'Software Engineering',
      start_date: '2020',
      end_date: '2024',
      gpa: '3.82 / 4.0',
      highlights: "Dean's Honor List (6 Quarters). Coursework: Distributed Systems, Databases, Cloud.",
    },
  ],
  skills: {
    languages: 'Python, TypeScript, JavaScript, SQL, HTML5, CSS3',
    frameworks: 'FastAPI, React, Node.js, Express, Tailwind CSS, Next.js',
    databases: 'PostgreSQL, Supabase, Redis',
    tools: 'Docker, Git, GitHub Actions, Linux/Bash, Postman, PyTest',
    soft_skills: 'Agile/Scrum, Technical Communication, Root-Cause Debugging',
  },
  projects: [
    {
      id: 'proj-1',
      name: 'PulseBoard — Distributed Metrics Visualizer',
      tech_stack: 'TypeScript, React, WebSockets, Python, Redis',
      url: 'https://github.com/alexrivera-tech/pulseboard',
      bullets: [
        'Engineered real-time telemetry dashboard streamed over WebSockets with <50ms latency.',
        'Integrated Redis pub/sub to handle concurrent broadcast bursts across 5,000 simulated nodes.',
      ],
    },
    {
      id: 'proj-2',
      name: 'CareerLens — Career Readiness Analyzer',
      tech_stack: 'Python, FastAPI, React, PostgreSQL',
      url: 'https://github.com/alexrivera-tech/careerlens',
      bullets: [
        'Developed deterministic ATS scoring engine analyzing section completeness and action verbs.',
        'Implemented vector PDF document compiler with automated page-overflow management.',
      ],
    },
  ],
  experience: [
    {
      id: 'exp-1',
      role: 'Associate Software Engineer',
      company: 'CloudScale Systems',
      location: 'Seattle, WA',
      start_date: 'Jan 2024',
      end_date: 'Present',
      is_current: true,
      bullets: [
        'Designed and developed 14+ RESTful API endpoints using FastAPI and Pydantic, supporting 120k daily active users.',
        'Refactored React front-end state management using TanStack Query, decreasing initial bundle load time by 28%.',
      ],
    },
  ],
  certifications: [
    {
      id: 'cert-1',
      name: 'AWS Certified Cloud Practitioner',
      issuer: 'Amazon Web Services',
      date: '2023',
      url: '',
    },
  ],
  achievements: [
    {
      id: 'ach-1',
      title: '1st Place Hackathon Winner',
      description: 'Built distributed healthcare routing service within 48 hours.',
      date: '2023',
    },
  ],
  section_order: ['contact', 'summary', 'skills', 'experience', 'projects', 'education', 'certifications', 'achievements'],
  template_id: 'modern',
};

export const createEmptyResumeData = (userEmail?: string, userName?: string): LiveResumeBuilderData => ({
  contact: {
    full_name: userName || '',
    email: userEmail || '',
    phone: '',
    location: '',
    linkedin: '',
    github: '',
    portfolio: '',
  },
  summary: '',
  education: [],
  skills: {
    languages: '',
    frameworks: '',
    databases: '',
    tools: '',
    soft_skills: '',
  },
  projects: [],
  experience: [],
  certifications: [],
  achievements: [],
  section_order: ['contact', 'summary', 'skills', 'experience', 'projects', 'education', 'certifications', 'achievements'],
  template_id: 'modern',
});

const defaultEmptyData: LiveResumeBuilderData = createEmptyResumeData();

export const ResumeBuilderPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const { user, getAccessToken } = useAuth();

  const [draftId, setDraftId] = useState<string>('');
  const [resumeData, setResumeData] = useState<LiveResumeBuilderData>(defaultEmptyData);
  const [activeTab, setActiveTab] = useState<string>('contact');
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'unsaved' | 'offline'>('saved');
  const [currentVersion, setCurrentVersion] = useState<number>(1);
  const [versions, setVersions] = useState<LiveResumeVersionItem[]>([]);
  const [isVersionsModalOpen, setIsVersionsModalOpen] = useState(false);
  const [versionNote, setVersionNote] = useState('');

  // AI Diff Suggestion State
  const [suggestions, setSuggestions] = useState<LiveAISuggestionItem[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [jobDescriptionInput, setJobDescriptionInput] = useState('');

  // Re-analysis state
  const [analysisResult, setAnalysisResult] = useState<LiveBuilderAnalysisResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isAnalysisModalOpen, setIsAnalysisModalOpen] = useState(false);

  // Export State
  const [isExporting, setIsExporting] = useState<'pdf' | 'docx' | null>(null);
  const [toast, setToast] = useState<ToastMessage | null>(null);

  const autosaveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Initialize draft on mount
  useEffect(() => {
    async function initDraft() {
      const sourceResumeId = searchParams.get('importResumeId') || sessionStorage.getItem('latest_resume_id');
      try {
        const token = user ? await getAccessToken() : null;
        const initialEmpty = createEmptyResumeData(user?.email, user?.user_metadata?.full_name);
        const res = await apiService.createResumeDraftLive(
          {
            title: 'My Professional Resume',
            source_resume_id: sourceResumeId || null,
            template_id: 'modern',
            initial_data: initialEmpty,
          },
          token
        );
        setDraftId(res.draft_id);
        setResumeData(res.data);
        setCurrentVersion(res.current_version);
        setSaveStatus('saved');
      } catch {
        // Fall back to offline local draft
        setDraftId(`local-${Date.now()}`);
        setResumeData(createEmptyResumeData(user?.email, user?.user_metadata?.full_name));
        setSaveStatus('offline');
      }
    }
    initDraft();
  }, [user]);

  // Debounced Autosave Trigger
  const triggerAutosave = (updatedData: LiveResumeBuilderData) => {
    setResumeData(updatedData);
    setSaveStatus('unsaved');

    if (autosaveTimeoutRef.current) {
      clearTimeout(autosaveTimeoutRef.current);
    }

    autosaveTimeoutRef.current = setTimeout(async () => {
      if (!draftId || draftId.startsWith('local-')) {
        setSaveStatus('offline');
        return;
      }
      setSaveStatus('saving');
      try {
        const token = user ? await getAccessToken() : null;
        await apiService.updateResumeDraftLive(
          draftId,
          updatedData,
          'My Professional Resume',
          updatedData.template_id,
          token
        );
        setSaveStatus('saved');
      } catch {
        setSaveStatus('offline');
      }
    }, 1200);
  };

  // Create Snapshot Version
  const handleCreateVersion = async () => {
    if (!draftId || draftId.startsWith('local-')) {
      setToast({
        id: Math.random().toString(),
        type: 'info',
        title: 'Offline Session',
        message: 'Draft is running in local mode. Connect backend or sign in to persist version checkpoints.',
      });
      return;
    }
    try {
      const token = user ? await getAccessToken() : null;
      const note = versionNote.trim() || `Version ${currentVersion + 1} Checkpoint`;
      const snap = await apiService.createResumeVersionLive(draftId, note, token);
      setCurrentVersion(snap.version_number);
      setVersionNote('');
      setIsVersionsModalOpen(false);
      setToast({
        id: Math.random().toString(),
        type: 'success',
        title: 'Version Saved',
        message: `Created snapshot #${snap.version_number}: "${note}".`,
      });
    } catch (err: any) {
      setToast({
        id: Math.random().toString(),
        type: 'error',
        title: 'Save Failed',
        message: err?.message || 'Could not save version snapshot.',
      });
    }
  };

  // Open Version History Modal
  const handleOpenVersionsModal = async () => {
    setIsVersionsModalOpen(true);
    if (draftId && !draftId.startsWith('local-')) {
      try {
        const token = user ? await getAccessToken() : null;
        const res = await apiService.listResumeVersionsLive(draftId, token);
        setVersions(res.versions);
      } catch (err) {
        console.warn('Could not list versions:', err);
      }
    }
  };

  // Restore previous version
  const handleRestoreVersion = (ver: LiveResumeVersionItem) => {
    triggerAutosave(ver.data_snapshot);
    setIsVersionsModalOpen(false);
    setToast({
      id: Math.random().toString(),
      type: 'info',
      title: 'Version Restored',
      message: `Restored snapshot #${ver.version_number} (${ver.note}).`,
    });
  };

  // Export to Real PDF
  const handleExportPdf = async () => {
    setIsExporting('pdf');
    try {
      const token = user ? await getAccessToken() : null;
      const blob = await apiService.exportResumePdfBlobLive(
        draftId || 'temp',
        resumeData,
        resumeData.template_id,
        token
      );
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Resume_${(resumeData.contact.full_name || 'Candidate').replace(/\s+/g, '_')}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      setToast({
        id: Math.random().toString(),
        type: 'success',
        title: 'PDF Downloaded',
        message: 'Compiled native vector PDF document with selectable text and clean margins.',
      });
    } catch (err: any) {
      setToast({
        id: Math.random().toString(),
        type: 'error',
        title: 'Export Failed',
        message: err?.message || 'Failed to generate PDF document.',
      });
    } finally {
      setIsExporting(null);
    }
  };

  // Export to Real DOCX
  const handleExportDocx = async () => {
    setIsExporting('docx');
    try {
      const token = user ? await getAccessToken() : null;
      const blob = await apiService.exportResumeDocxBlobLive(
        draftId || 'temp',
        resumeData,
        resumeData.template_id,
        token
      );
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Resume_${(resumeData.contact.full_name || 'Candidate').replace(/\s+/g, '_')}.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      setToast({
        id: Math.random().toString(),
        type: 'success',
        title: 'DOCX Downloaded',
        message: 'Generated ATS-compliant Microsoft Word document with native headings and bullet lists.',
      });
    } catch (err: any) {
      setToast({
        id: Math.random().toString(),
        type: 'error',
        title: 'Export Failed',
        message: err?.message || 'Failed to generate DOCX document.',
      });
    } finally {
      setIsExporting(null);
    }
  };

  // Fetch AI Edit Suggestions
  const handleRequestSuggestions = async (focus: string = 'general') => {
    setIsLoadingSuggestions(true);
    try {
      const token = user ? await getAccessToken() : null;
      const res = await apiService.fetchAIEditSuggestionsLive(
        draftId || 'temp',
        {
          focus_area: focus,
          job_description: jobDescriptionInput || undefined,
          current_data: resumeData,
        },
        token
      );
      setSuggestions(res.suggestions);
      setActiveTab('suggestions');
    } catch (err: any) {
      setToast({
        id: Math.random().toString(),
        type: 'error',
        title: 'Suggestions Error',
        message: err?.message || 'Could not fetch AI suggestions.',
      });
    } finally {
      setIsLoadingSuggestions(false);
    }
  };

  // Apply single AI suggestion (Diff accept)
  const handleApplySuggestion = (sugg: LiveAISuggestionItem) => {
    const updated = { ...resumeData };

    if (sugg.target_section === 'summary') {
      updated.summary = sugg.proposed_text;
    } else if (sugg.target_section === 'experience' && sugg.target_entry_id) {
      updated.experience = updated.experience.map((exp) => {
        if (exp.id === sugg.target_entry_id && sugg.target_bullet_index !== undefined && sugg.target_bullet_index !== null) {
          const newBullets = [...exp.bullets];
          newBullets[sugg.target_bullet_index] = sugg.proposed_text;
          return { ...exp, bullets: newBullets };
        }
        return exp;
      });
    } else if (sugg.target_section === 'projects' && sugg.target_entry_id) {
      updated.projects = updated.projects.map((proj) => {
        if (proj.id === sugg.target_entry_id && sugg.target_bullet_index !== undefined && sugg.target_bullet_index !== null) {
          const newBullets = [...proj.bullets];
          newBullets[sugg.target_bullet_index] = sugg.proposed_text;
          return { ...proj, bullets: newBullets };
        }
        return proj;
      });
    } else if (sugg.target_section === 'skills') {
      updated.skills.tools = sugg.proposed_text;
    }

    triggerAutosave(updated);
    setSuggestions((prev) => prev.filter((s) => s.id !== sugg.id));
    setToast({
      id: Math.random().toString(),
      type: 'success',
      title: 'Suggestion Applied',
      message: `Updated ${sugg.target_section}. Original replaced with accepted improvement.`,
    });
  };

  const handleDismissSuggestion = (suggId: string) => {
    setSuggestions((prev) => prev.filter((s) => s.id !== suggId));
  };

  // Rerun Phase 5 Analysis on Current Content
  const handleRerunAnalysis = async () => {
    setIsAnalyzing(true);
    try {
      const token = user ? await getAccessToken() : null;
      const res = await apiService.reanalyzeResumeDraftLive(draftId || 'temp', token);
      setAnalysisResult(res);
      setIsAnalysisModalOpen(true);
    } catch (err: any) {
      setToast({
        id: Math.random().toString(),
        type: 'error',
        title: 'Analysis Error',
        message: err?.message || 'Could not re-analyze resume draft.',
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Section Management Helpers
  const addProject = () => {
    const newProj: LiveProjectEntry = {
      id: `proj-${Date.now()}`,
      name: 'New Project Title',
      tech_stack: 'Python, React',
      url: '',
      bullets: ['Describe your technical contribution and measurable results.'],
    };
    triggerAutosave({ ...resumeData, projects: [...resumeData.projects, newProj] });
  };

  const removeProject = (id: string) => {
    triggerAutosave({
      ...resumeData,
      projects: resumeData.projects.filter((p) => p.id !== id),
    });
  };

  const addExperience = () => {
    const newExp: LiveExperienceEntry = {
      id: `exp-${Date.now()}`,
      role: 'Job or Internship Title',
      company: 'Organization Name',
      location: 'City, State',
      start_date: '2023',
      end_date: 'Present',
      is_current: true,
      bullets: ['Led feature implementation achieving measurable business value.'],
    };
    triggerAutosave({ ...resumeData, experience: [...resumeData.experience, newExp] });
  };

  const removeExperience = (id: string) => {
    triggerAutosave({
      ...resumeData,
      experience: resumeData.experience.filter((e) => e.id !== id),
    });
  };

  const addEducation = () => {
    const newEdu: LiveEducationEntry = {
      id: `edu-${Date.now()}`,
      school: 'University or College',
      degree: 'Degree Title',
      field_of_study: 'Major',
      start_date: '2020',
      end_date: '2024',
      gpa: '3.8',
      highlights: 'Relevant coursework and academic achievements',
    };
    triggerAutosave({ ...resumeData, education: [...resumeData.education, newEdu] });
  };

  const removeEducation = (id: string) => {
    triggerAutosave({
      ...resumeData,
      education: resumeData.education.filter((e) => e.id !== id),
    });
  };

  const editorTabs = [
    { id: 'contact', label: 'Contact', icon: User },
    { id: 'summary', label: 'Summary', icon: FileText },
    { id: 'skills', label: 'Skills', icon: Terminal },
    { id: 'projects', label: 'Projects', icon: FolderGit2 },
    { id: 'experience', label: 'Experience', icon: Briefcase },
    { id: 'education', label: 'Education', icon: GraduationCap },
    { id: 'suggestions', label: `AI Suggestions (${suggestions.length})`, icon: Sparkles },
  ];

  return (
    <div className="space-y-6">
      {/* Top Studio Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2.5">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">AI Resume Studio</h2>
            <span
              className={`text-[11px] px-2 py-0.5 rounded font-mono font-medium flex items-center gap-1 ${
                saveStatus === 'saved'
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : saveStatus === 'saving'
                  ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                  : saveStatus === 'offline'
                  ? 'bg-amber-50 text-amber-700 border border-amber-200'
                  : 'bg-slate-100 text-slate-600'
              }`}
            >
              {saveStatus === 'saving' && <RefreshCw className="w-2.5 h-2.5 animate-spin" />}
              {saveStatus === 'saved' && <CheckCircle2 className="w-2.5 h-2.5 text-emerald-600" />}
              {saveStatus === 'saved'
                ? `Saved (v${currentVersion})`
                : saveStatus === 'saving'
                ? 'Autosaving...'
                : saveStatus === 'offline'
                ? 'Local Draft'
                : 'Unsaved Changes'}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time ATS compiler with instant paper preview, version snapshots, and export.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Template Switcher */}
          <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs">
            <span className="text-[11px] font-semibold text-slate-500 px-2">Template:</span>
            {(['modern', 'classic', 'minimal'] as const).map((tId) => (
              <button
                key={tId}
                onClick={() => triggerAutosave({ ...resumeData, template_id: tId })}
                className={`px-2.5 py-1 rounded text-xs capitalize font-medium transition-colors cursor-pointer ${
                  resumeData.template_id === tId
                    ? 'bg-white text-indigo-700 shadow-2xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {tId}
              </button>
            ))}
          </div>

          {/* Form Actions: Clear or Sample Template */}
          <button
            type="button"
            onClick={() => {
              const fresh = createEmptyResumeData(user?.email, user?.user_metadata?.full_name);
              setResumeData(fresh);
              triggerAutosave(fresh);
              setToast({
                id: Math.random().toString(),
                type: 'info',
                title: 'Form Cleared',
                message: 'All resume fields reset to a blank slate.',
              });
            }}
            className="px-2.5 py-1 text-xs border border-slate-200 rounded-lg text-slate-600 hover:text-slate-900 bg-white hover:bg-slate-50 cursor-pointer"
            title="Start with an empty blank resume"
          >
            Clear to Blank
          </button>
          <button
            type="button"
            onClick={() => {
              setResumeData(sampleTemplateData);
              triggerAutosave(sampleTemplateData);
              setToast({
                id: Math.random().toString(),
                type: 'info',
                title: 'Sample Template Loaded',
                message: 'Populated with sample engineering candidate data.',
              });
            }}
            className="px-2.5 py-1 text-xs border border-indigo-200 text-indigo-700 bg-indigo-50/50 hover:bg-indigo-100/50 rounded-lg cursor-pointer"
            title="Load sample template data"
          >
            Load Sample
          </button>

          <Button
            size="sm"
            variant="outline"
            icon={<History className="w-3.5 h-3.5 text-slate-600" />}
            onClick={handleOpenVersionsModal}
          >
            Versions
          </Button>

          <Button
            size="sm"
            variant="outline"
            icon={<TrendingUp className="w-3.5 h-3.5 text-indigo-600" />}
            onClick={handleRerunAnalysis}
            isLoading={isAnalyzing}
          >
            Re-Analyze ATS
          </Button>

          {/* Export Buttons */}
          <Button
            size="sm"
            variant="outline"
            icon={<FileText className="w-3.5 h-3.5 text-blue-600" />}
            onClick={handleExportDocx}
            isLoading={isExporting === 'docx'}
          >
            Export DOCX
          </Button>

          <Button
            size="sm"
            variant="primary"
            icon={<Download className="w-3.5 h-3.5" />}
            onClick={handleExportPdf}
            isLoading={isExporting === 'pdf'}
          >
            Export PDF
          </Button>
        </div>
      </div>

      {/* Main Studio Grid: Left 5 Cols Editor, Right 7 Cols Live Paper Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Editor Tabs */}
        <div className="lg:col-span-5 space-y-4">
          <Card padding="none">
            {/* Tab Navigation */}
            <div className="flex overflow-x-auto border-b border-slate-200 p-1.5 bg-slate-50 gap-1 rounded-t-xl">
              {editorTabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors cursor-pointer ${
                      isActive
                        ? 'bg-white text-indigo-700 shadow-2xs font-semibold'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Tab Contents */}
            <div className="p-4 space-y-4 max-h-[700px] overflow-y-auto">
              {/* CONTACT TAB */}
              {activeTab === 'contact' && (
                <div className="space-y-3 text-xs">
                  <h3 className="font-semibold text-slate-800 text-sm">Personal & Contact Info</h3>
                  <div>
                    <label className="font-medium text-slate-700 block mb-1">Full Name</label>
                    <input
                      type="text"
                      value={resumeData.contact.full_name}
                      onChange={(e) =>
                        triggerAutosave({
                          ...resumeData,
                          contact: { ...resumeData.contact, full_name: e.target.value },
                        })
                      }
                      className="w-full p-2 border border-slate-200 rounded-lg text-xs"
                      placeholder="Alex Rivera"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="font-medium text-slate-700 block mb-1">Email</label>
                      <input
                        type="email"
                        value={resumeData.contact.email}
                        onChange={(e) =>
                          triggerAutosave({
                            ...resumeData,
                            contact: { ...resumeData.contact, email: e.target.value },
                          })
                        }
                        className="w-full p-2 border border-slate-200 rounded-lg text-xs"
                      />
                    </div>
                    <div>
                      <label className="font-medium text-slate-700 block mb-1">Phone</label>
                      <input
                        type="text"
                        value={resumeData.contact.phone}
                        onChange={(e) =>
                          triggerAutosave({
                            ...resumeData,
                            contact: { ...resumeData.contact, phone: e.target.value },
                          })
                        }
                        className="w-full p-2 border border-slate-200 rounded-lg text-xs"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="font-medium text-slate-700 block mb-1">Location</label>
                      <input
                        type="text"
                        value={resumeData.contact.location}
                        onChange={(e) =>
                          triggerAutosave({
                            ...resumeData,
                            contact: { ...resumeData.contact, location: e.target.value },
                          })
                        }
                        className="w-full p-2 border border-slate-200 rounded-lg text-xs"
                        placeholder="Seattle, WA"
                      />
                    </div>
                    <div>
                      <label className="font-medium text-slate-700 block mb-1">LinkedIn</label>
                      <input
                        type="text"
                        value={resumeData.contact.linkedin}
                        onChange={(e) =>
                          triggerAutosave({
                            ...resumeData,
                            contact: { ...resumeData.contact, linkedin: e.target.value },
                          })
                        }
                        className="w-full p-2 border border-slate-200 rounded-lg text-xs"
                        placeholder="linkedin.com/in/alex"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="font-medium text-slate-700 block mb-1">GitHub / Portfolio</label>
                    <input
                      type="text"
                      value={resumeData.contact.github}
                      onChange={(e) =>
                        triggerAutosave({
                          ...resumeData,
                          contact: { ...resumeData.contact, github: e.target.value },
                        })
                      }
                      className="w-full p-2 border border-slate-200 rounded-lg text-xs"
                      placeholder="github.com/alex"
                    />
                  </div>
                </div>
              )}

              {/* SUMMARY TAB */}
              {activeTab === 'summary' && (
                <div className="space-y-3 text-xs">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-slate-800 text-sm">Professional Summary</h3>
                    <Button
                      size="sm"
                      variant="outline"
                      icon={<Sparkles className="w-3 h-3 text-indigo-600" />}
                      onClick={() => handleRequestSuggestions('clarity')}
                      isLoading={isLoadingSuggestions}
                    >
                      AI Polish
                    </Button>
                  </div>
                  <textarea
                    rows={6}
                    value={resumeData.summary}
                    onChange={(e) => triggerAutosave({ ...resumeData, summary: e.target.value })}
                    className="w-full p-3 border border-slate-200 rounded-lg text-xs leading-relaxed font-sans"
                    placeholder="2-3 concise sentences highlighting core technical proficiencies and impact..."
                  />
                  <p className="text-[11px] text-slate-400">
                    Lead with your engineering specialization and quantified impact. Avoid first-person pronouns (I, me, my).
                  </p>
                </div>
              )}

              {/* SKILLS TAB */}
              {activeTab === 'skills' && (
                <div className="space-y-3 text-xs">
                  <h3 className="font-semibold text-slate-800 text-sm">Technical Skills Taxonomy</h3>
                  <div>
                    <label className="font-medium text-slate-700 block mb-1">Programming Languages</label>
                    <input
                      type="text"
                      value={resumeData.skills.languages}
                      onChange={(e) =>
                        triggerAutosave({
                          ...resumeData,
                          skills: { ...resumeData.skills, languages: e.target.value },
                        })
                      }
                      className="w-full p-2 border border-slate-200 rounded-lg text-xs"
                      placeholder="Python, TypeScript, SQL..."
                    />
                  </div>
                  <div>
                    <label className="font-medium text-slate-700 block mb-1">Frameworks & Libraries</label>
                    <input
                      type="text"
                      value={resumeData.skills.frameworks}
                      onChange={(e) =>
                        triggerAutosave({
                          ...resumeData,
                          skills: { ...resumeData.skills, frameworks: e.target.value },
                        })
                      }
                      className="w-full p-2 border border-slate-200 rounded-lg text-xs"
                      placeholder="FastAPI, React, Node.js..."
                    />
                  </div>
                  <div>
                    <label className="font-medium text-slate-700 block mb-1">Databases & Cloud</label>
                    <input
                      type="text"
                      value={resumeData.skills.databases}
                      onChange={(e) =>
                        triggerAutosave({
                          ...resumeData,
                          skills: { ...resumeData.skills, databases: e.target.value },
                        })
                      }
                      className="w-full p-2 border border-slate-200 rounded-lg text-xs"
                      placeholder="PostgreSQL, Supabase, Redis, AWS..."
                    />
                  </div>
                  <div>
                    <label className="font-medium text-slate-700 block mb-1">Developer Tools</label>
                    <input
                      type="text"
                      value={resumeData.skills.tools}
                      onChange={(e) =>
                        triggerAutosave({
                          ...resumeData,
                          skills: { ...resumeData.skills, tools: e.target.value },
                        })
                      }
                      className="w-full p-2 border border-slate-200 rounded-lg text-xs"
                      placeholder="Git, Docker, GitHub Actions, Linux..."
                    />
                  </div>
                </div>
              )}

              {/* PROJECTS TAB */}
              {activeTab === 'projects' && (
                <div className="space-y-4 text-xs">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-slate-800 text-sm">Key Technical Projects</h3>
                    <Button
                      size="sm"
                      variant="outline"
                      icon={<Plus className="w-3.5 h-3.5 text-emerald-600" />}
                      onClick={addProject}
                    >
                      Add Project
                    </Button>
                  </div>
                  {resumeData.projects.map((proj, idx) => (
                    <div key={proj.id} className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-800">Project #{idx + 1}</span>
                        <button
                          onClick={() => removeProject(proj.id)}
                          className="text-slate-400 hover:text-rose-600 cursor-pointer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      <input
                        type="text"
                        value={proj.name}
                        onChange={(e) => {
                          const updated = [...resumeData.projects];
                          updated[idx].name = e.target.value;
                          triggerAutosave({ ...resumeData, projects: updated });
                        }}
                        placeholder="Project Name"
                        className="w-full p-1.5 border border-slate-200 bg-white rounded text-xs font-semibold"
                      />
                      <input
                        type="text"
                        value={proj.tech_stack}
                        onChange={(e) => {
                          const updated = [...resumeData.projects];
                          updated[idx].tech_stack = e.target.value;
                          triggerAutosave({ ...resumeData, projects: updated });
                        }}
                        placeholder="Tech Stack (e.g. Python, React, Redis)"
                        className="w-full p-1.5 border border-slate-200 bg-white rounded text-xs"
                      />
                      {proj.bullets.map((bullet, bIdx) => (
                        <textarea
                          key={bIdx}
                          rows={2}
                          value={bullet}
                          onChange={(e) => {
                            const updated = [...resumeData.projects];
                            updated[idx].bullets[bIdx] = e.target.value;
                            triggerAutosave({ ...resumeData, projects: updated });
                          }}
                          className="w-full p-1.5 border border-slate-200 bg-white rounded text-xs font-sans"
                        />
                      ))}
                    </div>
                  ))}
                </div>
              )}

              {/* EXPERIENCE TAB */}
              {activeTab === 'experience' && (
                <div className="space-y-4 text-xs">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-slate-800 text-sm">Work & Internship Experience</h3>
                      <p className="text-[11px] text-slate-400">Optional for entry-level candidates</p>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      icon={<Plus className="w-3.5 h-3.5 text-emerald-600" />}
                      onClick={addExperience}
                    >
                      Add Experience
                    </Button>
                  </div>
                  {resumeData.experience.length === 0 ? (
                    <div className="p-4 bg-slate-50 border border-dashed border-slate-200 rounded-lg text-center text-slate-500">
                      No experience listed. As an entry-level candidate, your projects and education will be prioritized in the ATS layout.
                    </div>
                  ) : (
                    resumeData.experience.map((exp, idx) => (
                      <div key={exp.id} className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-slate-800">Experience #{idx + 1}</span>
                          <button
                            onClick={() => removeExperience(exp.id)}
                            className="text-slate-400 hover:text-rose-600 cursor-pointer"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                          <input
                            type="text"
                            value={exp.role}
                            onChange={(e) => {
                              const updated = [...resumeData.experience];
                              updated[idx].role = e.target.value;
                              triggerAutosave({ ...resumeData, experience: updated });
                            }}
                            placeholder="Job Title"
                            className="w-full p-1.5 border border-slate-200 bg-white rounded text-xs font-semibold"
                          />
                          <input
                            type="text"
                            value={exp.company}
                            onChange={(e) => {
                              const updated = [...resumeData.experience];
                              updated[idx].company = e.target.value;
                              triggerAutosave({ ...resumeData, experience: updated });
                            }}
                            placeholder="Company Name"
                            className="w-full p-1.5 border border-slate-200 bg-white rounded text-xs"
                          />
                        </div>
                        {exp.bullets.map((bullet, bIdx) => (
                          <textarea
                            key={bIdx}
                            rows={2}
                            value={bullet}
                            onChange={(e) => {
                              const updated = [...resumeData.experience];
                              updated[idx].bullets[bIdx] = e.target.value;
                              triggerAutosave({ ...resumeData, experience: updated });
                            }}
                            className="w-full p-1.5 border border-slate-200 bg-white rounded text-xs font-sans"
                          />
                        ))}
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* EDUCATION TAB */}
              {activeTab === 'education' && (
                <div className="space-y-4 text-xs">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-slate-800 text-sm">Academic Credentials</h3>
                    <Button
                      size="sm"
                      variant="outline"
                      icon={<Plus className="w-3.5 h-3.5 text-emerald-600" />}
                      onClick={addEducation}
                    >
                      Add Degree
                    </Button>
                  </div>
                  {resumeData.education.map((edu, idx) => (
                    <div key={edu.id} className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-800">Education #{idx + 1}</span>
                        <button
                          onClick={() => removeEducation(edu.id)}
                          className="text-slate-400 hover:text-rose-600 cursor-pointer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      <input
                        type="text"
                        value={edu.school}
                        onChange={(e) => {
                          const updated = [...resumeData.education];
                          updated[idx].school = e.target.value;
                          triggerAutosave({ ...resumeData, education: updated });
                        }}
                        placeholder="School or University"
                        className="w-full p-1.5 border border-slate-200 bg-white rounded text-xs font-semibold"
                      />
                      <div className="grid grid-cols-2 gap-2">
                        <input
                          type="text"
                          value={edu.degree}
                          onChange={(e) => {
                            const updated = [...resumeData.education];
                            updated[idx].degree = e.target.value;
                            triggerAutosave({ ...resumeData, education: updated });
                          }}
                          placeholder="Degree (e.g. B.S.)"
                          className="w-full p-1.5 border border-slate-200 bg-white rounded text-xs"
                        />
                        <input
                          type="text"
                          value={edu.gpa}
                          onChange={(e) => {
                            const updated = [...resumeData.education];
                            updated[idx].gpa = e.target.value;
                            triggerAutosave({ ...resumeData, education: updated });
                          }}
                          placeholder="GPA (e.g. 3.8 / 4.0)"
                          className="w-full p-1.5 border border-slate-200 bg-white rounded text-xs"
                        />
                      </div>
                      <input
                        type="text"
                        value={edu.highlights}
                        onChange={(e) => {
                          const updated = [...resumeData.education];
                          updated[idx].highlights = e.target.value;
                          triggerAutosave({ ...resumeData, education: updated });
                        }}
                        placeholder="Relevant Coursework, Honors, Dean's List..."
                        className="w-full p-1.5 border border-slate-200 bg-white rounded text-xs"
                      />
                    </div>
                  ))}
                </div>
              )}

              {/* AI SUGGESTIONS TAB (Diff view) */}
              {activeTab === 'suggestions' && (
                <div className="space-y-4 text-xs">
                  <div className="p-3 bg-indigo-50/70 border border-indigo-100 rounded-lg">
                    <h4 className="font-semibold text-indigo-950 mb-1 flex items-center">
                      <Sparkles className="w-3.5 h-3.5 mr-1 text-indigo-600" />
                      AI Diff Assistant
                    </h4>
                    <p className="text-[11px] text-slate-600 mb-2">
                      Review proposed sentence rewrites. Original content is preserved until you explicitly accept a change.
                    </p>
                    <div className="flex gap-1.5">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleRequestSuggestions('clarity')}
                        isLoading={isLoadingSuggestions}
                      >
                        Action Verbs
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleRequestSuggestions('metrics')}
                        isLoading={isLoadingSuggestions}
                      >
                        STAR Metrics
                      </Button>
                    </div>
                  </div>

                  {/* Optional Job Description input for tailoring */}
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1.5">
                    <label className="font-semibold text-slate-700 block text-[11px]">
                      Tailor to Target Job Description:
                    </label>
                    <textarea
                      rows={2}
                      value={jobDescriptionInput}
                      onChange={(e) => setJobDescriptionInput(e.target.value)}
                      placeholder="Paste target job responsibilities or qualifications..."
                      className="w-full p-2 border border-slate-200 bg-white rounded text-[11px]"
                    />
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleRequestSuggestions('job_tailor')}
                      isLoading={isLoadingSuggestions}
                      disabled={!jobDescriptionInput.trim()}
                    >
                      Tailor Wording to Job
                    </Button>
                  </div>

                  {/* Suggestion Cards */}
                  {suggestions.length === 0 ? (
                    <div className="p-6 text-center text-slate-400 bg-slate-50 rounded-lg border border-dashed border-slate-200">
                      No active suggestions. Click "Action Verbs" or "STAR Metrics" above to scan for improvements.
                    </div>
                  ) : (
                    suggestions.map((sugg) => (
                      <div key={sugg.id} className="p-3 bg-white border border-slate-200 rounded-lg shadow-2xs space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-slate-900">{sugg.title}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 font-mono capitalize">
                            {sugg.target_section}
                          </span>
                        </div>

                        {/* Diff Comparison */}
                        <div className="space-y-1.5 font-mono text-[11px]">
                          <div className="p-2 bg-rose-50 border border-rose-100 rounded text-rose-900">
                            <span className="text-rose-500 font-bold mr-1">-</span>
                            {sugg.original_text}
                          </div>
                          <div className="p-2 bg-emerald-50 border border-emerald-100 rounded text-emerald-950">
                            <span className="text-emerald-600 font-bold mr-1">+</span>
                            {sugg.proposed_text}
                          </div>
                        </div>

                        <p className="text-[11px] text-slate-500 italic">{sugg.rationale}</p>

                        {sugg.missing_facts_prompt && (
                          <div className="p-2 bg-amber-50 border border-amber-200 rounded text-[11px] text-amber-900 flex items-start gap-1.5">
                            <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                            <span>
                              <strong>Fact check needed:</strong> {sugg.missing_facts_prompt}
                            </span>
                          </div>
                        )}

                        <div className="flex justify-end gap-2 pt-1">
                          <button
                            onClick={() => handleDismissSuggestion(sugg.id)}
                            className="px-2.5 py-1 text-slate-500 hover:text-slate-800 text-[11px] cursor-pointer"
                          >
                            Dismiss
                          </button>
                          <Button
                            size="sm"
                            variant="primary"
                            icon={<Check className="w-3 h-3" />}
                            onClick={() => handleApplySuggestion(sugg)}
                          >
                            Accept Edit
                          </Button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Right Column: Live Paper Preview with 3 Templates */}
        <div className="lg:col-span-7">
          <div className="bg-slate-200/60 p-4 sm:p-6 rounded-2xl flex justify-center border border-slate-300">
            {/* The Resume Sheet */}
            <div
              className={`bg-white shadow-xl rounded-sm w-full max-w-[640px] min-h-[820px] p-8 sm:p-12 text-slate-900 text-xs leading-relaxed transition-all ${
                resumeData.template_id === 'classic'
                  ? 'font-serif'
                  : resumeData.template_id === 'minimal'
                  ? 'font-mono text-[11px]'
                  : 'font-sans'
              }`}
            >
              {/* Header */}
              <div
                className={`pb-3 mb-4 ${
                  resumeData.template_id === 'classic'
                    ? 'text-center border-b border-slate-300'
                    : resumeData.template_id === 'modern'
                    ? 'border-b-2 border-indigo-900'
                    : 'border-b border-slate-900'
                }`}
              >
                <h1
                  className={`text-xl sm:text-2xl font-bold tracking-tight ${
                    resumeData.template_id === 'modern' ? 'text-indigo-950' : 'text-slate-900'
                  }`}
                >
                  {resumeData.contact.full_name || 'Your Full Name'}
                </h1>
                <div
                  className={`text-[11px] text-slate-600 flex flex-wrap gap-x-2 gap-y-1 mt-1 ${
                    resumeData.template_id === 'classic' ? 'justify-center' : ''
                  }`}
                >
                  {resumeData.contact.location && <span>{resumeData.contact.location}</span>}
                  {resumeData.contact.phone && <span>• {resumeData.contact.phone}</span>}
                  {resumeData.contact.email && <span>• {resumeData.contact.email}</span>}
                  {resumeData.contact.linkedin && <span>• {resumeData.contact.linkedin}</span>}
                  {resumeData.contact.github && <span>• {resumeData.contact.github}</span>}
                </div>
              </div>

              {/* Summary */}
              {resumeData.summary.trim() && (
                <div className="mb-4">
                  <h2
                    className={`text-[11px] font-bold uppercase tracking-wider mb-1 ${
                      resumeData.template_id === 'modern'
                        ? 'text-indigo-900 border-b border-indigo-100 pb-0.5'
                        : 'text-slate-800 border-b border-slate-200 pb-0.5'
                    }`}
                  >
                    Professional Summary
                  </h2>
                  <p className="text-slate-700 leading-relaxed text-justify">{resumeData.summary}</p>
                </div>
              )}

              {/* Skills */}
              <div className="mb-4">
                <h2
                  className={`text-[11px] font-bold uppercase tracking-wider mb-1 ${
                    resumeData.template_id === 'modern'
                      ? 'text-indigo-900 border-b border-indigo-100 pb-0.5'
                      : 'text-slate-800 border-b border-slate-200 pb-0.5'
                  }`}
                >
                  Technical Skills
                </h2>
                <div className="space-y-0.5 text-slate-700">
                  {resumeData.skills.languages && (
                    <p>
                      <strong>Languages:</strong> {resumeData.skills.languages}
                    </p>
                  )}
                  {resumeData.skills.frameworks && (
                    <p>
                      <strong>Frameworks:</strong> {resumeData.skills.frameworks}
                    </p>
                  )}
                  {resumeData.skills.databases && (
                    <p>
                      <strong>Databases & Cloud:</strong> {resumeData.skills.databases}
                    </p>
                  )}
                  {resumeData.skills.tools && (
                    <p>
                      <strong>Tools:</strong> {resumeData.skills.tools}
                    </p>
                  )}
                </div>
              </div>

              {/* Experience (if present) */}
              {resumeData.experience.length > 0 && (
                <div className="mb-4">
                  <h2
                    className={`text-[11px] font-bold uppercase tracking-wider mb-1.5 ${
                      resumeData.template_id === 'modern'
                        ? 'text-indigo-900 border-b border-indigo-100 pb-0.5'
                        : 'text-slate-800 border-b border-slate-200 pb-0.5'
                    }`}
                  >
                    Experience
                  </h2>
                  <div className="space-y-3">
                    {resumeData.experience.map((exp) => (
                      <div key={exp.id}>
                        <div className="flex justify-between items-baseline font-semibold text-slate-900">
                          <span>
                            {exp.role} — <span className="font-normal text-slate-700">{exp.company}</span>
                          </span>
                          <span className="text-[10px] text-slate-500 font-mono">
                            {exp.start_date} - {exp.end_date}
                          </span>
                        </div>
                        <ul className="list-disc list-outside ml-4 mt-1 space-y-0.5 text-slate-700">
                          {exp.bullets.map((b, bIdx) => (
                            <li key={bIdx}>{b}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Projects */}
              {resumeData.projects.length > 0 && (
                <div className="mb-4">
                  <h2
                    className={`text-[11px] font-bold uppercase tracking-wider mb-1.5 ${
                      resumeData.template_id === 'modern'
                        ? 'text-indigo-900 border-b border-indigo-100 pb-0.5'
                        : 'text-slate-800 border-b border-slate-200 pb-0.5'
                    }`}
                  >
                    Technical Projects
                  </h2>
                  <div className="space-y-2.5">
                    {resumeData.projects.map((proj) => (
                      <div key={proj.id}>
                        <div className="flex justify-between items-baseline font-semibold text-slate-900">
                          <span>
                            {proj.name}
                            {proj.tech_stack && (
                              <span className="font-normal text-slate-500 text-[11px]"> ({proj.tech_stack})</span>
                            )}
                          </span>
                        </div>
                        <ul className="list-disc list-outside ml-4 mt-0.5 space-y-0.5 text-slate-700">
                          {proj.bullets.map((b, bIdx) => (
                            <li key={bIdx}>{b}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Education */}
              {resumeData.education.length > 0 && (
                <div className="mb-4">
                  <h2
                    className={`text-[11px] font-bold uppercase tracking-wider mb-1 ${
                      resumeData.template_id === 'modern'
                        ? 'text-indigo-900 border-b border-indigo-100 pb-0.5'
                        : 'text-slate-800 border-b border-slate-200 pb-0.5'
                    }`}
                  >
                    Education
                  </h2>
                  <div className="space-y-2">
                    {resumeData.education.map((edu) => (
                      <div key={edu.id}>
                        <div className="flex justify-between items-baseline font-semibold text-slate-900">
                          <span>{edu.school}</span>
                          <span className="text-[10px] text-slate-500 font-mono">{edu.end_date}</span>
                        </div>
                        <p className="text-slate-700">
                          {edu.degree} {edu.field_of_study && `in ${edu.field_of_study}`}
                          {edu.gpa && ` (GPA: ${edu.gpa})`}
                        </p>
                        {edu.highlights && (
                          <p className="text-[10px] text-slate-500 mt-0.5">{edu.highlights}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* VERSION HISTORY MODAL */}
      {isVersionsModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-lg w-full p-5 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-sm flex items-center">
                <History className="w-4 h-4 mr-2 text-indigo-600" />
                Resume Version History
              </h3>
              <button
                onClick={() => setIsVersionsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Create new snapshot input */}
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
              <label className="text-xs font-semibold text-slate-700 block">
                Save Checkpoint Snapshot:
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={versionNote}
                  onChange={(e) => setVersionNote(e.target.value)}
                  placeholder="e.g. Tailored for Fintech Python Role"
                  className="flex-1 p-2 border border-slate-200 bg-white rounded text-xs"
                />
                <Button size="sm" variant="primary" onClick={handleCreateVersion}>
                  Save
                </Button>
              </div>
            </div>

            {/* List of past versions */}
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {versions.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-4">No prior snapshots saved yet.</p>
              ) : (
                versions.map((v) => (
                  <div
                    key={v.version_id}
                    className="p-3 border border-slate-200 rounded-lg flex items-center justify-between text-xs hover:bg-slate-50"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900">Version #{v.version_number}</span>
                        <span className="text-[10px] text-slate-400 font-mono">
                          {new Date(v.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <p className="text-slate-600 text-[11px] mt-0.5">{v.note}</p>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleRestoreVersion(v)}
                    >
                      Restore
                    </Button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* RE-ANALYSIS MODAL */}
      {isAnalysisModalOpen && analysisResult && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-lg w-full p-5 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-sm flex items-center">
                <TrendingUp className="w-4 h-4 mr-2 text-indigo-600" />
                Updated ATS Diagnostic Score
              </h3>
              <button
                onClick={() => setIsAnalysisModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex items-center justify-around p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div className="text-center">
                <span className="text-[11px] font-semibold text-slate-400 uppercase">Overall ATS Score</span>
                <p className="text-3xl font-extrabold font-mono text-slate-900 mt-1">
                  {analysisResult.overall_score}
                  <span className="text-sm font-normal text-slate-400">/100</span>
                </p>
                <Badge variant="success" size="sm" className="mt-1">
                  {analysisResult.readiness_tier}
                </Badge>
              </div>

              <div className="space-y-1.5 text-xs text-slate-600">
                <p>
                  <strong>Detected Skills:</strong> {analysisResult.detected_skills_count}
                </p>
                <p>
                  <strong>Active Findings:</strong> {analysisResult.findings_count}
                </p>
                <p>
                  <strong>Content Quality:</strong> {analysisResult.component_scores.content_quality}%
                </p>
                <p>
                  <strong>ATS Readability:</strong> {analysisResult.component_scores.ats_readability}%
                </p>
              </div>
            </div>

            <p className="text-[11px] text-slate-500 text-center">
              Re-analysis was performed deterministically on your currently edited builder text.
            </p>

            <div className="flex justify-end">
              <Button size="sm" variant="primary" onClick={() => setIsAnalysisModalOpen(false)}>
                Continue Editing
              </Button>
            </div>
          </div>
        </div>
      )}

      <Toast toast={toast} onClose={() => setToast(null)} />
    </div>
  );
};
