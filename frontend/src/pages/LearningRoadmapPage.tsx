import React, { useState, useEffect, useCallback } from 'react';
import {
  Clock,
  ExternalLink,
  BookOpen,
  Check,
  CheckCircle2,
  Circle,
  PlayCircle,
  Sparkles,
  RefreshCw,
  Sliders,
  Filter,
  AlertCircle,
  Calendar,
  ChevronDown,
  ChevronUp,
  FolderGit2,
  Target,
  Info,
  X,
  Plus,
  ShieldCheck,
  Code2,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { ProgressBar } from '../components/common/ProgressBar';
import { Toast } from '../components/common/Toast';
import type { ToastMessage } from '../components/common/Toast';
import { apiService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { POPULAR_COMPANIES, POPULAR_ROLES } from '../data/suggestions';
import type {
  LiveLearningRoadmapResponse,
  RoadmapTaskStatus,
  SkillPriority,
} from '../types';

export const LearningRoadmapPage: React.FC = () => {
  const { user, getAccessToken } = useAuth();

  const [roadmap, setRoadmap] = useState<LiveLearningRoadmapResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<ToastMessage | null>(null);

  // Filters
  const [priorityFilter, setPriorityFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'not_started' | 'in_progress' | 'completed'>('all');
  const [activeMilestoneTab, setActiveMilestoneTab] = useState<'all' | number>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Expandable Task Cards
  const [expandedTaskIds, setExpandedTaskIds] = useState<Set<string>>(new Set());

  // Task Notes & Custom Resource Edit State
  const [editingNotesTaskId, setEditingNotesTaskId] = useState<string | null>(null);
  const [notesDraft, setNotesDraft] = useState('');
  const [addingResourceTaskId, setAddingResourceTaskId] = useState<string | null>(null);
  const [customResourceTitle, setCustomResourceTitle] = useState('');
  const [customResourceUrl, setCustomResourceUrl] = useState('');

  // Modals
  const [isRegenModalOpen, setIsRegenModalOpen] = useState(false);
  const [regenRole, setRegenRole] = useState('');
  const [regenCompany, setRegenCompany] = useState('');
  const [regenJobDescription, setRegenJobDescription] = useState('');
  const [isRegenerating, setIsRegenerating] = useState(false);

  const [isPrefsModalOpen, setIsPrefsModalOpen] = useState(false);
  const [prefWeeklyHours, setPrefWeeklyHours] = useState(10);
  const [prefTargetWeeks, setPrefTargetWeeks] = useState(4);
  const [isSavingPrefs, setIsSavingPrefs] = useState(false);

  // Load Roadmap on mount
  const loadRoadmap = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const token = user ? await getAccessToken() : null;
      const data = await apiService.fetchCurrentLearningRoadmapLive(token);
      setRoadmap(data);
      setPrefWeeklyHours(data.weekly_hours);
      setPrefTargetWeeks(data.target_weeks);
      setRegenRole(data.target_role);
      setRegenCompany(data.target_company || '');
      // Expand first milestone tasks by default
      if (data.all_tasks.length > 0) {
        setExpandedTaskIds(new Set([data.all_tasks[0].id]));
      }
    } catch (err: any) {
      console.error('Failed to load roadmap:', err);
      setError(err?.message || 'Could not load personalized learning roadmap.');
    } finally {
      setIsLoading(false);
    }
  }, [user, getAccessToken]);

  useEffect(() => {
    loadRoadmap();
  }, [loadRoadmap]);

  const toggleTaskExpanded = (id: string) => {
    setExpandedTaskIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // Update Task Status
  const handleStatusChange = async (taskId: string, newStatus: RoadmapTaskStatus) => {
    if (!roadmap) return;
    try {
      const token = user ? await getAccessToken() : null;
      const updated = await apiService.updateRoadmapTaskStatusLive(
        roadmap.id,
        taskId,
        { status: newStatus },
        token
      );
      setRoadmap(updated);
      setToast({
        id: Math.random().toString(),
        type: 'success',
        title: 'Task Status Updated',
        message: `Task marked as ${newStatus.replace('_', ' ')}. Completion metrics recalculated.`,
      });
    } catch (err: any) {
      setToast({
        id: Math.random().toString(),
        type: 'error',
        title: 'Update Failed',
        message: err?.message || 'Failed to update task status.',
      });
    }
  };

  // Save Notes for Task
  const handleSaveNotes = async (taskId: string) => {
    if (!roadmap) return;
    try {
      const currentTask = roadmap.all_tasks.find((t) => t.id === taskId);
      const token = user ? await getAccessToken() : null;
      const updated = await apiService.updateRoadmapTaskStatusLive(
        roadmap.id,
        taskId,
        {
          status: currentTask ? currentTask.status : 'not_started',
          notes: notesDraft,
        },
        token
      );
      setRoadmap(updated);
      setEditingNotesTaskId(null);
      setToast({
        id: Math.random().toString(),
        type: 'success',
        title: 'Notes Saved',
        message: 'Personal reflection and repository notes successfully saved.',
      });
    } catch (err: any) {
      setToast({
        id: Math.random().toString(),
        type: 'error',
        title: 'Save Error',
        message: err?.message || 'Failed to save notes.',
      });
    }
  };

  // Add Custom User Resource
  const handleAddCustomResource = async (taskId: string) => {
    if (!roadmap || !customResourceTitle.trim()) return;
    try {
      const currentTask = roadmap.all_tasks.find((t) => t.id === taskId);
      const existingResources = currentTask?.custom_resources || [];
      const newRes = {
        title: customResourceTitle.trim(),
        url: customResourceUrl.trim() || null,
        resource_type: 'user_added',
        is_verified: false,
      };

      const token = user ? await getAccessToken() : null;
      const updated = await apiService.updateRoadmapTaskStatusLive(
        roadmap.id,
        taskId,
        {
          status: currentTask ? currentTask.status : 'not_started',
          custom_resources: [...existingResources, newRes],
        },
        token
      );
      setRoadmap(updated);
      setAddingResourceTaskId(null);
      setCustomResourceTitle('');
      setCustomResourceUrl('');
      setToast({
        id: Math.random().toString(),
        type: 'success',
        title: 'Resource Added',
        message: 'Custom study resource appended to task.',
      });
    } catch (err: any) {
      setToast({
        id: Math.random().toString(),
        type: 'error',
        title: 'Failed to Add Resource',
        message: err?.message || 'Could not attach custom resource.',
      });
    }
  };

  // Save Preferences
  const handleSavePreferences = async () => {
    if (!roadmap) return;
    setIsSavingPrefs(true);
    try {
      const token = user ? await getAccessToken() : null;
      const updated = await apiService.updateRoadmapPreferencesLive(
        roadmap.id,
        {
          weekly_hours: Number(prefWeeklyHours),
          target_weeks: Number(prefTargetWeeks),
        },
        token
      );
      setRoadmap(updated);
      setIsPrefsModalOpen(false);
      setToast({
        id: Math.random().toString(),
        type: 'success',
        title: 'Preferences Updated',
        message: `Pacing adjusted to ${prefWeeklyHours} hrs/week across ${prefTargetWeeks} weeks.`,
      });
    } catch (err: any) {
      setToast({
        id: Math.random().toString(),
        type: 'error',
        title: 'Update Failed',
        message: err?.message || 'Could not update preferences.',
      });
    } finally {
      setIsSavingPrefs(false);
    }
  };

  // Regenerate / Refresh Roadmap
  const handleRegenerateRoadmap = async () => {
    if (!roadmap) return;
    setIsRegenerating(true);
    try {
      const token = user ? await getAccessToken() : null;
      const cleanRole = regenRole ? regenRole.trim() : '';
      const cleanCompany = regenCompany ? regenCompany.trim() : '';
      const cleanJd = regenJobDescription ? regenJobDescription.trim() : '';

      // Check if target role was changed by student
      const staleMatchRole = sessionStorage.getItem('latest_target_role') || '';
      const isCustomizedRole = cleanRole && staleMatchRole && cleanRole.toLowerCase() !== staleMatchRole.toLowerCase();

      const updated = await apiService.refreshLearningRoadmapLive(
        roadmap.id,
        {
          target_role: cleanRole || undefined,
          target_company: cleanCompany || undefined,
          job_description: cleanJd || undefined,
          resume_id: sessionStorage.getItem('latest_resume_id') || undefined,
          job_match_id: isCustomizedRole ? undefined : (sessionStorage.getItem('latest_match_id') || undefined),
        },
        token
      );
      setRoadmap(updated);
      setPrefWeeklyHours(updated.weekly_hours);
      setPrefTargetWeeks(updated.target_weeks);
      setIsRegenModalOpen(false);
      setToast({
        id: Math.random().toString(),
        type: 'success',
        title: 'Roadmap Refreshed',
        message: `Tailored curriculum regenerated for ${cleanRole || updated.target_role}. All completed tasks preserved.`,
      });
    } catch (err: any) {
      setToast({
        id: Math.random().toString(),
        type: 'error',
        title: 'Regeneration Failed',
        message: err?.message || 'Could not refresh roadmap.',
      });
    } finally {
      setIsRegenerating(false);
    }
  };

  // Task filtering
  const filteredTasks = (roadmap?.all_tasks || []).filter((task) => {
    if (priorityFilter !== 'all' && task.priority !== priorityFilter) return false;
    if (statusFilter !== 'all' && task.status !== statusFilter) return false;
    if (activeMilestoneTab !== 'all' && task.milestone_week !== activeMilestoneTab) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = task.title.toLowerCase().includes(q);
      const matchSkill = task.skill.toLowerCase().includes(q);
      const matchInstructions = task.instructions.toLowerCase().includes(q);
      if (!matchTitle && !matchSkill && !matchInstructions) return false;
    }
    return true;
  });

  const getPriorityBadgeVariant = (p: SkillPriority) => {
    switch (p) {
      case 'high':
        return 'danger';
      case 'medium':
        return 'warning';
      case 'low':
        return 'success';
      default:
        return 'default';
    }
  };

  const getEvidenceStatusBadge = (status: string) => {
    switch (status) {
      case 'demonstrated':
        return (
          <Badge variant="success" size="sm" icon={<Check className="w-3 h-3 text-emerald-600" />}>
            Demonstrated
          </Badge>
        );
      case 'partial_evidence':
        return (
          <Badge variant="warning" size="sm" icon={<AlertCircle className="w-3 h-3 text-amber-600" />}>
            Partial Evidence
          </Badge>
        );
      case 'not_demonstrated':
      default:
        return (
          <Badge variant="default" size="sm" className="bg-slate-100 text-slate-700">
            Not Demonstrated
          </Badge>
        );
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px] space-y-4">
        <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin" />
        <p className="text-sm text-slate-600 font-medium">
          Synthesizing resume weaknesses, job requirements, and verified profile evidence...
        </p>
      </div>
    );
  }

  if (error || !roadmap) {
    return (
      <div className="space-y-6">
        <Card className="border-rose-200 bg-rose-50/50 p-8 text-center space-y-4">
          <AlertCircle className="w-10 h-10 text-rose-500 mx-auto" />
          <h3 className="text-lg font-bold text-slate-900">Unable to Load Learning Roadmap</h3>
          <p className="text-sm text-slate-600 max-w-lg mx-auto">
            {error || 'No active learning roadmap found. Generate a personalized roadmap tailored to your target job.'}
          </p>
          <div className="flex justify-center gap-3 pt-2">
            <Button variant="primary" onClick={() => loadRoadmap()}>
              Retry
            </Button>
            <Button variant="secondary" onClick={() => setIsRegenModalOpen(true)}>
              Create New Roadmap
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  const remainingHours = Math.max(0, roadmap.total_estimated_hours - roadmap.completed_hours);

  return (
    <div className="space-y-6">
      {toast && <Toast toast={toast} onClose={() => setToast(null)} />}

      {/* Target Role & Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-2xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-300 bg-indigo-500/20 px-2.5 py-0.5 rounded-full border border-indigo-400/30">
                Phase 10: Personalized Skill Roadmap
              </span>
              {roadmap.is_ai_grounded && (
                <Badge variant="purple" size="sm" icon={<Sparkles className="w-3 h-3 text-purple-300" />}>
                  AI Grounded
                </Badge>
              )}
              {roadmap.target_company && (
                <span className="text-xs text-indigo-200 font-medium">
                  Tailored for {roadmap.target_company}
                </span>
              )}
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              {roadmap.target_role} Learning Roadmap
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              Targeted milestone curriculum resolving verified resume gaps against real employer expectations.
              Paced for <strong>{roadmap.weekly_hours} hours/week</strong> across <strong>{roadmap.target_weeks} weeks</strong>.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 shrink-0">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsPrefsModalOpen(true)}
              className="bg-white/10 hover:bg-white/20 text-white border-white/20"
            >
              <Sliders className="w-4 h-4 mr-1.5" />
              Adjust Schedule
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsRegenModalOpen(true)}
              className="bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm"
            >
              <RefreshCw className="w-4 h-4 mr-1.5" />
              Regenerate Roadmap
            </Button>
          </div>
        </div>
      </div>

      {/* Progress & Overview Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-medium">Curriculum Progress</span>
            <Target className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900">{roadmap.completion_percentage}%</span>
            <span className="text-xs text-slate-500">completed</span>
          </div>
          <ProgressBar value={roadmap.completion_percentage} color="indigo" size="sm" showPercentage={false} />
        </Card>

        <Card className="p-4 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-medium">Tasks Completed</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900">{roadmap.completed_tasks}</span>
            <span className="text-xs text-slate-500">of {roadmap.total_tasks} milestones</span>
          </div>
          <p className="text-[11px] text-slate-500 font-medium">
            {roadmap.in_progress_tasks} task{roadmap.in_progress_tasks === 1 ? '' : 's'} currently in progress
          </p>
        </Card>

        <Card className="p-4 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-medium">Estimated Study Time</span>
            <Clock className="w-4 h-4 text-blue-600" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900">{roadmap.completed_hours}</span>
            <span className="text-xs text-slate-500">/ {roadmap.total_estimated_hours} hrs</span>
          </div>
          <p className="text-[11px] text-slate-500 font-medium">
            ~{remainingHours} study hours remaining
          </p>
        </Card>

        <Card className="p-4 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-medium">Pacing & Duration</span>
            <Calendar className="w-4 h-4 text-purple-600" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900">{roadmap.target_weeks}</span>
            <span className="text-xs text-slate-500">Weeks</span>
          </div>
          <p className="text-[11px] text-slate-500 font-medium">
            {roadmap.weekly_hours} dedicated hrs/week
          </p>
        </Card>
      </div>

      {/* Grounding & Ethics Disclosure Pill */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-slate-600 flex items-start gap-2.5">
        <Info className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <p className="font-medium text-slate-800">
            Evidence-Grounded Recommendation & Self-Reported Tracking Policy
          </p>
          <p className="text-slate-500 leading-relaxed text-[11px]">
            {roadmap.disclaimer} Absence of evidence in your resume indicates missing documentation in provided files, not confirmed lack of competence.
          </p>
        </div>
      </div>

      {/* High-Priority Skill Gaps Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-slate-900 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-indigo-600" />
              Target Role Skill Gap Analysis
            </h2>
            <p className="text-xs text-slate-500">
              Correlating target job requirements against detected resume claims and verified GitHub profiles.
            </p>
          </div>
          <span className="text-xs text-slate-400 font-medium">
            {roadmap.skill_gaps.length} Competencies Evaluated
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {roadmap.skill_gaps.map((gap, idx) => (
            <Card key={idx} className="p-4 flex flex-col justify-between space-y-3 hover:border-slate-300 transition-colors">
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-bold text-slate-900 text-sm">{gap.skill}</h3>
                  <Badge variant={getPriorityBadgeVariant(gap.learning_priority)} size="sm">
                    {gap.learning_priority.toUpperCase()} PRIORITY
                  </Badge>
                </div>

                <div className="flex items-center gap-2 text-xs">
                  <span className="text-slate-500 capitalize">{gap.importance} requirement</span>
                  <span className="text-slate-300">•</span>
                  {getEvidenceStatusBadge(gap.evidence_status)}
                </div>

                <p className="text-xs text-slate-600 leading-relaxed line-clamp-3">
                  {gap.reason}
                </p>
              </div>

              <div className="pt-2 border-t border-slate-100 text-[11px] text-slate-500 font-mono">
                Evidence: {gap.evidence_found}
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Filter and Milestone Tabs Bar */}
      <Card className="p-4 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5 mr-1">
              <Filter className="w-3.5 h-3.5 text-slate-500" />
              Filter By:
            </span>

            {/* Status Filter */}
            <div className="flex items-center bg-slate-100 rounded-lg p-0.5 text-xs">
              {(['all', 'not_started', 'in_progress', 'completed'] as const).map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-2.5 py-1 rounded-md capitalize font-medium transition-colors ${
                    statusFilter === st ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {st.replace('_', ' ')}
                </button>
              ))}
            </div>

            {/* Priority Filter */}
            <div className="flex items-center bg-slate-100 rounded-lg p-0.5 text-xs">
              {(['all', 'high', 'medium', 'low'] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => setPriorityFilter(p)}
                  className={`px-2.5 py-1 rounded-md capitalize font-medium transition-colors ${
                    priorityFilter === p ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          {/* Search Box */}
          <div className="w-full md:w-64">
            <input
              type="text"
              placeholder="Search skill or task..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full text-xs px-3 py-1.5 rounded-lg border border-slate-200 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 bg-white"
            />
          </div>
        </div>

        {/* Milestone Week Tabs */}
        <div className="flex items-center gap-2 border-t border-slate-100 pt-3 overflow-x-auto pb-1">
          <button
            onClick={() => setActiveMilestoneTab('all')}
            className={`text-xs px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-colors ${
              activeMilestoneTab === 'all'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            All Milestones ({roadmap.all_tasks.length})
          </button>
          {roadmap.milestones.map((m) => (
            <button
              key={m.week_number}
              onClick={() => setActiveMilestoneTab(m.week_number)}
              className={`text-xs px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-colors ${
                activeMilestoneTab === m.week_number
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              Week {m.week_number} ({m.tasks.length})
            </button>
          ))}
        </div>
      </Card>

      {/* Task List */}
      <div className="space-y-4">
        {filteredTasks.length === 0 ? (
          <Card className="p-8 text-center space-y-2">
            <BookOpen className="w-8 h-8 text-slate-400 mx-auto" />
            <h4 className="text-sm font-bold text-slate-800">No Matching Roadmap Tasks</h4>
            <p className="text-xs text-slate-500">
              No tasks match the selected priority, status, or search filters.
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setStatusFilter('all');
                setPriorityFilter('all');
                setActiveMilestoneTab('all');
                setSearchQuery('');
              }}
              className="mt-2"
            >
              Reset Filters
            </Button>
          </Card>
        ) : (
          filteredTasks.map((task) => {
            const isExpanded = expandedTaskIds.has(task.id);
            const isEditingNotes = editingNotesTaskId === task.id;
            const isAddingResource = addingResourceTaskId === task.id;

            return (
              <Card
                key={task.id}
                className={`transition-all duration-200 overflow-hidden ${
                  task.status === 'completed'
                    ? 'border-emerald-200 bg-emerald-50/20'
                    : task.status === 'in_progress'
                    ? 'border-indigo-200 bg-indigo-50/15'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                {/* Header row */}
                <div className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-start gap-3 flex-1">
                    <button
                      onClick={() =>
                        handleStatusChange(
                          task.id,
                          task.status === 'completed'
                            ? 'in_progress'
                            : task.status === 'in_progress'
                            ? 'not_started'
                            : 'completed'
                        )
                      }
                      title={`Click to toggle status (Currently: ${task.status.replace('_', ' ')})`}
                      className="mt-0.5 shrink-0 focus:outline-hidden"
                    >
                      {task.status === 'completed' ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-600 fill-emerald-100" />
                      ) : task.status === 'in_progress' ? (
                        <PlayCircle className="w-5 h-5 text-indigo-600 fill-indigo-100 animate-pulse" />
                      ) : (
                        <Circle className="w-5 h-5 text-slate-300 hover:text-slate-400" />
                      )}
                    </button>

                    <div className="space-y-1 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-[11px] font-semibold text-slate-500 font-mono">
                          {task.milestone_title.split(':')[0]}
                        </span>
                        <span className="text-slate-300">•</span>
                        <Badge variant="purple" size="sm">
                          {task.skill}
                        </Badge>
                        <Badge variant={getPriorityBadgeVariant(task.priority)} size="sm">
                          {task.priority.toUpperCase()}
                        </Badge>
                        <span className="text-xs text-slate-500 flex items-center gap-1 ml-auto sm:ml-0">
                          <Clock className="w-3.5 h-3.5 text-slate-400" />
                          {task.estimated_hours} hrs
                        </span>
                      </div>

                      <h3
                        className={`text-sm sm:text-base font-bold ${
                          task.status === 'completed' ? 'text-slate-700 line-through' : 'text-slate-900'
                        }`}
                      >
                        {task.title}
                      </h3>
                    </div>
                  </div>

                  {/* Actions & Status Pill */}
                  <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                    <select
                      value={task.status}
                      onChange={(e) => handleStatusChange(task.id, e.target.value as RoadmapTaskStatus)}
                      className={`text-xs font-semibold px-2.5 py-1.5 rounded-lg border cursor-pointer focus:outline-hidden ${
                        task.status === 'completed'
                          ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                          : task.status === 'in_progress'
                          ? 'bg-indigo-50 border-indigo-200 text-indigo-700'
                          : 'bg-slate-50 border-slate-200 text-slate-600'
                      }`}
                    >
                      <option value="not_started">Pending / Not Started</option>
                      <option value="in_progress">In Progress</option>
                      <option value="completed">Completed (Self-Reported)</option>
                    </select>

                    <button
                      onClick={() => toggleTaskExpanded(task.id)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
                      title={isExpanded ? 'Collapse task' : 'Expand details'}
                    >
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="border-t border-slate-100 p-4 sm:p-5 bg-slate-50/50 space-y-4 text-xs">
                    {/* Step-by-Step Instructions */}
                    <div className="space-y-1.5">
                      <span className="font-bold text-slate-800 text-[11px] uppercase tracking-wider flex items-center gap-1.5">
                        <BookOpen className="w-3.5 h-3.5 text-indigo-600" />
                        Step-by-Step Action Plan
                      </span>
                      <div className="bg-white p-3 rounded-lg border border-slate-200 text-slate-700 leading-relaxed whitespace-pre-line font-mono text-[11px]">
                        {task.instructions}
                      </div>
                    </div>

                    {/* Practical Exercise & Expected Deliverable */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div className="bg-white p-3 rounded-lg border border-slate-200 space-y-1">
                        <span className="font-bold text-slate-800 text-[11px] uppercase tracking-wider flex items-center gap-1 text-indigo-900">
                          <Code2 className="w-3.5 h-3.5 text-indigo-600" />
                          Practical Exercise
                        </span>
                        <p className="text-slate-600 leading-relaxed">{task.practical_exercise}</p>
                      </div>

                      <div className="bg-white p-3 rounded-lg border border-slate-200 space-y-1">
                        <span className="font-bold text-slate-800 text-[11px] uppercase tracking-wider flex items-center gap-1 text-emerald-900">
                          <FolderGit2 className="w-3.5 h-3.5 text-emerald-600" />
                          Expected Deliverable
                        </span>
                        <p className="text-slate-600 leading-relaxed">{task.deliverable}</p>
                        <p className="text-[10px] text-slate-400 pt-1">
                          <strong>Criteria:</strong> {task.completion_criteria}
                        </p>
                      </div>
                    </div>

                    {/* Prerequisites and Relevance */}
                    <div className="flex flex-wrap items-center gap-4 text-slate-600">
                      {task.prerequisites.length > 0 && (
                        <div>
                          <strong className="text-slate-800">Prerequisites:</strong>{' '}
                          {task.prerequisites.join(', ')}
                        </div>
                      )}
                      {task.target_role_requirement && (
                        <div>
                          <strong className="text-slate-800">Target Role Relevance:</strong>{' '}
                          {task.target_role_requirement}
                        </div>
                      )}
                    </div>

                    {/* Verified Learning Resources */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-800 text-[11px] uppercase tracking-wider flex items-center gap-1.5">
                          <ExternalLink className="w-3.5 h-3.5 text-blue-600" />
                          Verified Learning Resources
                        </span>
                        <button
                          onClick={() => setAddingResourceTaskId(isAddingResource ? null : task.id)}
                          className="text-[11px] text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1"
                        >
                          <Plus className="w-3 h-3" />
                          Add Custom Resource
                        </button>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {task.resources.map((res, rIdx) => (
                          <div
                            key={rIdx}
                            className="bg-white p-2.5 rounded-lg border border-slate-200 flex items-center justify-between gap-2"
                          >
                            <div className="truncate">
                              <span className="font-medium text-slate-900 truncate block">{res.title}</span>
                              <span className="text-[10px] text-emerald-600 font-medium">Official Documentation</span>
                            </div>
                            {res.url ? (
                              <a
                                href={res.url}
                                target="_blank"
                                rel="noreferrer"
                                className="p-1 rounded text-slate-400 hover:text-indigo-600 hover:bg-slate-100 shrink-0"
                                title="Open resource in new tab"
                              >
                                <ExternalLink className="w-3.5 h-3.5" />
                              </a>
                            ) : (
                              <Badge variant="outline" size="sm">
                                Search Reference
                              </Badge>
                            )}
                          </div>
                        ))}

                        {/* Custom User Added Resources */}
                        {task.custom_resources?.map((cRes, cIdx) => (
                          <div
                            key={`c-${cIdx}`}
                            className="bg-indigo-50/50 p-2.5 rounded-lg border border-indigo-100 flex items-center justify-between gap-2"
                          >
                            <div className="truncate">
                              <span className="font-medium text-slate-900 truncate block">{cRes.title}</span>
                              <span className="text-[10px] text-indigo-600 font-medium">User Added Resource</span>
                            </div>
                            {cRes.url && (
                              <a
                                href={cRes.url}
                                target="_blank"
                                rel="noreferrer"
                                className="p-1 rounded text-slate-400 hover:text-indigo-600 hover:bg-white shrink-0"
                              >
                                <ExternalLink className="w-3.5 h-3.5" />
                              </a>
                            )}
                          </div>
                        ))}
                      </div>

                      {/* Add Resource Input Form */}
                      {isAddingResource && (
                        <div className="bg-white p-3 rounded-lg border border-indigo-200 space-y-2 mt-2">
                          <span className="font-semibold text-slate-800 text-xs">Add Study Resource</span>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            <input
                              type="text"
                              placeholder="Resource Title (e.g. FullStack Tutorial)"
                              value={customResourceTitle}
                              onChange={(e) => setCustomResourceTitle(e.target.value)}
                              className="text-xs px-2.5 py-1.5 rounded border border-slate-200 focus:outline-hidden focus:ring-1 focus:ring-indigo-500"
                            />
                            <input
                              type="url"
                              placeholder="URL (optional)"
                              value={customResourceUrl}
                              onChange={(e) => setCustomResourceUrl(e.target.value)}
                              className="text-xs px-2.5 py-1.5 rounded border border-slate-200 focus:outline-hidden focus:ring-1 focus:ring-indigo-500"
                            />
                          </div>
                          <div className="flex justify-end gap-2 pt-1">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setAddingResourceTaskId(null)}
                            >
                              Cancel
                            </Button>
                            <Button
                              variant="primary"
                              size="sm"
                              onClick={() => handleAddCustomResource(task.id)}
                            >
                              Attach Resource
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Candidate Reflection & Project Notes */}
                    <div className="space-y-1.5 pt-2 border-t border-slate-100">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-800 text-[11px] uppercase tracking-wider flex items-center gap-1.5">
                          <FolderGit2 className="w-3.5 h-3.5 text-purple-600" />
                          Candidate Notes & Evidence Links
                        </span>
                        {!isEditingNotes && (
                          <button
                            onClick={() => {
                              setEditingNotesTaskId(task.id);
                              setNotesDraft(task.user_notes || '');
                            }}
                            className="text-[11px] text-indigo-600 hover:text-indigo-800 font-medium"
                          >
                            {task.user_notes ? 'Edit Notes' : '+ Add Notes / Repo Link'}
                          </button>
                        )}
                      </div>

                      {isEditingNotes ? (
                        <div className="space-y-2">
                          <textarea
                            rows={3}
                            value={notesDraft}
                            onChange={(e) => setNotesDraft(e.target.value)}
                            placeholder="Enter your GitHub repository URL, key lessons learned, or blockers faced..."
                            className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 bg-white"
                          />
                          <div className="flex justify-end gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setEditingNotesTaskId(null)}
                            >
                              Cancel
                            </Button>
                            <Button
                              variant="primary"
                              size="sm"
                              onClick={() => handleSaveNotes(task.id)}
                            >
                              Save Notes
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <p className="text-slate-600 italic text-[11px]">
                          {task.user_notes || 'No candidate notes recorded yet.'}
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </Card>
            );
          })
        )}
      </div>

      {/* Adjust Schedule Preferences Modal */}
      {isPrefsModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <Card className="w-full max-w-md p-6 space-y-4 shadow-2xl bg-white">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Sliders className="w-4 h-4 text-indigo-600" />
                Adjust Study Schedule
              </h3>
              <button
                onClick={() => setIsPrefsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div className="space-y-1.5">
                <label className="font-semibold text-slate-700">Weekly Available Study Time (Hours)</label>
                <input
                  type="number"
                  min={1}
                  max={60}
                  value={prefWeeklyHours}
                  onChange={(e) => setPrefWeeklyHours(Math.max(1, Number(e.target.value)))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                />
                <span className="text-[11px] text-slate-500">
                  Recommended: 10–15 hours/week for working students.
                </span>
              </div>

              <div className="space-y-1.5">
                <label className="font-semibold text-slate-700">Target Duration (Weeks)</label>
                <input
                  type="number"
                  min={1}
                  max={52}
                  value={prefTargetWeeks}
                  onChange={(e) => setPrefTargetWeeks(Math.max(1, Number(e.target.value)))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                />
                <span className="text-[11px] text-slate-500">
                  Total curriculum span across milestones.
                </span>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
              <Button variant="outline" size="sm" onClick={() => setIsPrefsModalOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleSavePreferences}
                disabled={isSavingPrefs}
              >
                {isSavingPrefs ? 'Saving...' : 'Apply Schedule'}
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Regenerate Roadmap Modal */}
      {isRegenModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <Card className="w-full max-w-lg p-6 space-y-4 shadow-2xl bg-white max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <RefreshCw className="w-4 h-4 text-indigo-600" />
                Regenerate Personalized Roadmap
              </h3>
              <button
                onClick={() => setIsRegenModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="bg-indigo-50/50 border border-indigo-100 rounded-lg p-3 text-xs text-indigo-900 flex items-start gap-2">
              <Info className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
              <span>
                <strong>Progress Preservation:</strong> All previously completed tasks, notes, and milestones are preserved and will not be discarded.
              </span>
            </div>

            <div className="space-y-3 text-xs">
              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Target Role Title</label>
                <input
                  type="text"
                  list="roadmap-role-suggestions"
                  placeholder="e.g. Data Analyst, Software Engineer, Data Scientist"
                  value={regenRole}
                  onChange={(e) => setRegenRole(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                />
                <datalist id="roadmap-role-suggestions">
                  {POPULAR_ROLES.map((r) => (
                    <option key={r} value={r} />
                  ))}
                </datalist>
                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  <span className="text-[10px] text-slate-400 font-medium">Suggestions:</span>
                  {['Data Analyst', 'Software Engineer', 'Data Scientist', 'AI / Deep Learning Engineer', 'Frontend Developer / Engineer', 'Backend Developer / Engineer', 'DevOps Engineer'].map((roleSuggestion) => (
                    <button
                      key={roleSuggestion}
                      type="button"
                      onClick={() => setRegenRole(roleSuggestion)}
                      className={`text-[10px] px-2 py-0.5 rounded-md border transition-colors cursor-pointer ${
                        regenRole.toLowerCase() === roleSuggestion.toLowerCase()
                          ? 'bg-indigo-100 text-indigo-700 border-indigo-300 font-semibold'
                          : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-indigo-50 hover:text-indigo-600'
                      }`}
                    >
                      {roleSuggestion}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Target Company (Optional)</label>
                <input
                  type="text"
                  list="roadmap-company-suggestions"
                  placeholder="e.g. Infosys, Google, Microsoft, Amazon"
                  value={regenCompany}
                  onChange={(e) => setRegenCompany(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                />
                <datalist id="roadmap-company-suggestions">
                  {POPULAR_COMPANIES.map((c) => (
                    <option key={c} value={c} />
                  ))}
                </datalist>
                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  <span className="text-[10px] text-slate-400 font-medium">Suggestions:</span>
                  {['Infosys', 'Google', 'Microsoft', 'Amazon', 'Meta', 'Zoho', 'Tata Consultancy Services (TCS)'].map((compSuggestion) => (
                    <button
                      key={compSuggestion}
                      type="button"
                      onClick={() => setRegenCompany(compSuggestion)}
                      className={`text-[10px] px-2 py-0.5 rounded-md border transition-colors cursor-pointer ${
                        regenCompany.toLowerCase() === compSuggestion.toLowerCase()
                          ? 'bg-indigo-100 text-indigo-700 border-indigo-300 font-semibold'
                          : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-indigo-50 hover:text-indigo-600'
                      }`}
                    >
                      {compSuggestion}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Custom Job Description Text (Optional)</label>
                <textarea
                  rows={4}
                  placeholder="Paste requirements, preferred qualifications, and technical stack..."
                  value={regenJobDescription}
                  onChange={(e) => setRegenJobDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                />
                <span className="text-[11px] text-slate-500">
                  If left empty, your existing Phase 6 job match and Phase 5 resume analysis will be automatically synthesized.
                </span>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
              <Button variant="outline" size="sm" onClick={() => setIsRegenModalOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleRegenerateRoadmap}
                disabled={isRegenerating}
              >
                {isRegenerating ? 'Synthesizing...' : 'Regenerate Curriculum'}
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
