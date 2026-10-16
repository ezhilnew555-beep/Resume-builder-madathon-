import type {
  ReadinessScore,
  ResumeSection,
  ReviewFinding,
  JobMatchAnalysis,
  ProfileConnection,
  LearningTask,
  CareerReport,
  StudentProfile,
  LiveResumeUploadResponse,
  LiveResumeDetailResponse,
  LiveResumeTextResponse,
  LiveResumeStatus,
  LiveResumeAnalysisResponse,
  LiveJobMatchResponse,
  LiveFetchJobUrlResponse,
  LiveProfileConnectionItem,
  LiveProfileConnectionsResponse,
  LiveEvidenceVerificationResponse,
  LiveResumeExplanationResponse,
  LiveJobMatchExplanationResponse,
  LiveAssistantChatRequest,
  LiveAssistantChatResponse,
  LiveResumeBuilderData,
  LiveResumeDraftResponse,
  LiveResumeVersionItem,
  LiveVersionListResponse,
  LiveAIEditSuggestResponse,
  LiveBuilderAnalysisResponse,
  LiveLearningRoadmapResponse,
  LiveRoadmapProgressResponse,
  LiveRoadmapGenerateRequest,
  LiveTaskStatusUpdateRequest,
  LiveRoadmapPreferencesUpdateRequest,
  LiveRoadmapRefreshRequest,
  LiveRoadmapTask,
  LiveReportsListResponse,
  LiveReportSaveRequest,
  LiveDetailedReportResponse,
  LiveReportComparisonResponse,
  LiveProgressAnalyticsSummaryResponse,
} from '../types';
import {
  mockReadinessScore,
  mockResumeSections,
  mockReviewFindings,
  mockJobMatchAnalysis,
  mockProfileConnections,
  mockLearningTasks,
  mockReports,
  mockStudentProfile,
} from '../data/mockData';

// Configurable base URL through Vite environment variable
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface HealthCheckResult {
  connected: boolean;
  status: string;
  version?: string;
  environment?: string;
  error?: string;
}

export interface BackendDashboardData {
  is_demo: boolean;
  demo_notice: string;
  candidate_name: string;
  target_career: string;
  overall_readiness_score: number;
  readiness_tier: string;
  metrics: {
    [key: string]: {
      value: number;
      label: string;
      status: string;
      description: string;
    };
  };
  active_resume_summary: {
    file_name: string;
    word_count: number;
    sections_detected: number;
    sections_total: number;
    total_findings: number;
    errors: number;
    recommendations: number;
  };
  skill_coverage: {
    skill: string;
    percentage: number;
    status: string;
  }[];
  recent_reports: {
    id: string;
    date: string;
    target_role: string;
    overall_score: number;
  }[];
}

export interface BackendResumeStatus {
  services_configured: boolean;
  pdf_parser_available: boolean;
  docx_parser_available: boolean;
  ocr_fallback_available: boolean;
  ai_explainer_configured: boolean;
  status_message: string;
  roadmap_phase: string;
}

export interface BackendReportsResponse {
  reports: Array<{
    id: string;
    date: string;
    resume_name: string;
    target_role: string;
    overall_score: number;
    ats_score: number;
    match_score: number;
  }>;
  total: number;
  message: string;
}

export interface UploadResumeResponse {
  success: boolean;
  message: string;
  fileInfo: {
    fileName: string;
    fileSize: number;
    fileType: string;
    uploadedAt: string;
  };
  notice: string;
}

export const apiService = {
  /**
   * Check real health status of FastAPI backend
   */
  async getHealthStatus(): Promise<HealthCheckResult> {
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        signal: AbortSignal.timeout(2500),
      });

      if (!response.ok) {
        return {
          connected: false,
          status: 'error',
          error: `HTTP ${response.status}: ${response.statusText}`,
        };
      }

      const data = await response.json();
      return {
        connected: true,
        status: data.status || 'healthy',
        version: data.version,
        environment: data.environment,
      };
    } catch (err: any) {
      return {
        connected: false,
        status: 'disconnected',
        error: err?.message || 'Failed to reach FastAPI backend',
      };
    }
  },

  /**
   * Fetch live dashboard response from backend
   * Supports user-specific telemetry when token is provided, or optional demonstration mode.
   * Throws an error if backend is unavailable so caller can display error & retry state.
   */
  async fetchLiveDashboard(token?: string | null, demo: boolean = false): Promise<BackendDashboardData> {
    const headers: Record<string, string> = { 'Accept': 'application/json' };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const query = demo ? '?demo=true' : '';
    const response = await fetch(`${API_BASE_URL}/dashboard${query}`, {
      method: 'GET',
      headers,
      signal: AbortSignal.timeout(3000),
    });

    if (!response.ok) {
      throw new Error(`Failed to load dashboard from FastAPI backend: HTTP ${response.status}`);
    }

    return await response.json();
  },

  /**
   * Query resume service availability from backend
   */
  async fetchResumeStatus(): Promise<LiveResumeStatus> {
    const response = await fetch(`${API_BASE_URL}/resume/status`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(3000),
    });

    if (!response.ok) {
      throw new Error(`Failed to query resume service status: HTTP ${response.status}`);
    }

    return await response.json();
  },

  /**
   * Test resume analysis endpoint (expects 501 Not Implemented)
   */
  async testResumeAnalyze(fileName: string, fileType: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/resume/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ file_name: fileName, file_type: fileType }),
      signal: AbortSignal.timeout(3000),
    });

    return await response.json();
  },

  /**
   * Test jobs match endpoint
   */
  async testJobMatch(company: string, role: string, jobDescription: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/jobs/match`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({
        company,
        role,
        job_description: jobDescription,
      }),
      signal: AbortSignal.timeout(3000),
    });

    return await response.json();
  },

  /**
   * Fetch reports from backend (returns empty list)
   */
  async fetchLiveReports(): Promise<BackendReportsResponse> {
    const response = await fetch(`${API_BASE_URL}/reports`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(3000),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch reports from backend: HTTP ${response.status}`);
    }

    return await response.json();
  },

  /**
   * Fetch authenticated student profile from backend /api/v1/profile/me
   */
  async fetchUserProfileLive(token: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/profile/me`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      signal: AbortSignal.timeout(3000),
    });
    if (!response.ok) {
      throw new Error(`Failed to fetch profile: HTTP ${response.status}`);
    }
    return await response.json();
  },

  /**
   * Update student profile in Supabase PostgreSQL via /api/v1/profile/me
   */
  async updateUserProfileLive(token: string, data: { full_name?: string; education?: string; target_role?: string }): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/profile/me`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(data),
      signal: AbortSignal.timeout(3000),
    });
    if (!response.ok) {
      throw new Error(`Failed to update profile: HTTP ${response.status}`);
    }
    return await response.json();
  },

  /**
   * Upload and parse resume file (PDF or DOCX) via real FastAPI backend
   */
  async uploadResumeFileLive(file: File, token?: string | null): Promise<LiveResumeUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const headers: Record<string, string> = {
      'Accept': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/resume/upload`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      let errorMsg = `Upload failed with HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) {
          errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
        }
      } catch {
        // Fall back to default error text
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  },

  /**
   * Fetch parsed resume details and detected sections
   */
  async fetchResumeDetailsLive(resumeId: string, token?: string | null): Promise<LiveResumeDetailResponse> {
    const headers: Record<string, string> = {
      'Accept': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/resume/${resumeId}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      let errorMsg = `Failed to fetch resume details: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = errJson.detail;
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  },

  /**
   * Fetch raw extracted text for preview
   */
  async fetchResumeTextLive(resumeId: string, token?: string | null): Promise<LiveResumeTextResponse> {
    const headers: Record<string, string> = {
      'Accept': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/resume/${resumeId}/text`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      let errorMsg = `Failed to fetch resume text: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = errJson.detail;
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  },

  /**
   * Run deterministic ATS resume analysis via POST /api/v1/resume/{resume_id}/analyze
   */
  async analyzeResumeLive(
    resumeId: string,
    options?: { target_role?: string; job_description?: string },
    token?: string | null
  ): Promise<LiveResumeAnalysisResponse> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/resume/${resumeId}/analyze`, {
      method: 'POST',
      headers,
      body: JSON.stringify(options || {}),
    });

    if (!response.ok) {
      let errorMsg = `Analysis failed with HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  },

  /**
   * Fetch previously computed resume analysis via GET /api/v1/resume/{resume_id}/analysis
   */
  async fetchResumeAnalysisLive(resumeId: string, token?: string | null): Promise<LiveResumeAnalysisResponse> {
    const headers: Record<string, string> = {
      'Accept': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/resume/${resumeId}/analysis`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      let errorMsg = `Failed to fetch analysis: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = errJson.detail;
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  },

  /**
   * Run real Phase 6 deterministic job matching against parsed resume
   */
  async matchJobLive(
    data: {
      company: string;
      role: string;
      job_description?: string;
      job_url?: string;
      resume_id?: string;
    },
    token?: string | null
  ): Promise<LiveJobMatchResponse> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/jobs/match`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      let errorMsg = `Job match failed with status ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) {
          errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
        }
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  },

  /**
   * Retrieve saved job match result by match ID
   */
  async getJobMatchLive(matchId: string, token?: string | null): Promise<LiveJobMatchResponse> {
    const headers: Record<string, string> = {
      'Accept': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/jobs/matches/${matchId}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      let errorMsg = `Failed to fetch match result: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = errJson.detail;
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  },

  /**
   * Fetch and extract clean text from a public job posting URL (with SSRF protection on backend)
   */
  async fetchJobUrlLive(url: string, token?: string | null): Promise<LiveFetchJobUrlResponse> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/jobs/fetch-url`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ url }),
    });

    if (!response.ok) {
      let errorMsg = `URL retrieval failed with status ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) {
          errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
        }
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  },

  /**
   * Phase 7: Fetch live profile connections via GET /api/v1/profiles/connections
   */
  async fetchProfileConnectionsLive(token?: string | null): Promise<LiveProfileConnectionsResponse> {
    const headers: Record<string, string> = {
      'Accept': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/profiles/connections`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      let errorMsg = `Failed to fetch connections: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = errJson.detail;
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  },

  /**
   * Phase 7: Connect or update a profile connection via POST /api/v1/profiles/connections
   */
  async updateProfileConnectionLive(
    platformId: string,
    usernameOrUrl: string,
    token?: string | null
  ): Promise<LiveProfileConnectionItem> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/profiles/connections`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        platform_id: platformId,
        username_or_url: usernameOrUrl,
      }),
    });

    if (!response.ok) {
      let errorMsg = `Connection failed with status ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) {
          errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
        }
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  },

  /**
   * Phase 7: Explicit shortcut to connect GitHub via POST /api/v1/profiles/github/connect
   */
  async connectGitHubLive(usernameOrUrl: string, token?: string | null): Promise<LiveProfileConnectionItem> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/profiles/github/connect`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ username_or_url: usernameOrUrl }),
    });

    if (!response.ok) {
      let errorMsg = `GitHub connection failed with status ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) {
          errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
        }
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  },

  /**
   * Phase 7: Disconnect a profile via DELETE /api/v1/profiles/connections/{platformId}
   */
  async disconnectProfileLive(platformId: string, token?: string | null): Promise<void> {
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/profiles/connections/${platformId}`, {
      method: 'DELETE',
      headers,
    });

    if (!response.ok) {
      let errorMsg = `Failed to disconnect profile: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = errJson.detail;
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }
  },

  /**
   * Phase 7: Trigger live evidence verification via POST /api/v1/evidence/verify
   */
  async verifyEvidenceLive(
    resumeId?: string,
    githubOverride?: string,
    token?: string | null
  ): Promise<LiveEvidenceVerificationResponse> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/evidence/verify`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        resume_id: resumeId,
        github_username_or_url: githubOverride,
      }),
    });

    if (!response.ok) {
      let errorMsg = `Verification failed with status ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) {
          errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
        }
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  },

  /**
   * Phase 7: Fetch previous verification report via GET /api/v1/evidence/{verificationId}
   */
  async getEvidenceVerificationLive(
    verificationId: string,
    token?: string | null
  ): Promise<LiveEvidenceVerificationResponse> {
    const headers: Record<string, string> = {
      'Accept': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/evidence/${verificationId}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      let errorMsg = `Failed to fetch verification report: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = errJson.detail;
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  },

  /**
   * Phase 8: Fetch grounded AI explanation for resume review findings
   */
  async fetchResumeExplanationLive(
    resumeId: string,
    token?: string | null
  ): Promise<LiveResumeExplanationResponse> {
    const headers: Record<string, string> = {
      'Accept': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/explanations/resume/${resumeId}`, {
      method: 'POST',
      headers,
    });

    if (!response.ok) {
      let errorMsg = `Failed to generate resume explanation: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = errJson.detail;
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  },

  /**
   * Phase 8: Fetch grounded AI explanation for company job match
   */
  async fetchJobMatchExplanationLive(
    matchId: string,
    token?: string | null
  ): Promise<LiveJobMatchExplanationResponse> {
    const headers: Record<string, string> = {
      'Accept': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/explanations/jobs/${matchId}`, {
      method: 'POST',
      headers,
    });

    if (!response.ok) {
      let errorMsg = `Failed to generate job match explanation: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = errJson.detail;
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  },

  /**
   * Phase 8: Send query to contextual AI assistant grounded in user reports
   */
  async sendAssistantChatLive(
    request: LiveAssistantChatRequest,
    token?: string | null
  ): Promise<LiveAssistantChatResponse> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/assistant/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      let errorMsg = `Assistant chat failed: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = errJson.detail;
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  },

  /**
   * Phase 9: Create new resume draft (blank or imported from parsed resume)
   */
  async createResumeDraftLive(
    request: {
      title?: string;
      source_resume_id?: string | null;
      template_id?: string;
      initial_data?: LiveResumeBuilderData;
    },
    token?: string | null
  ): Promise<LiveResumeDraftResponse> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/builder/resumes`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to create resume draft: HTTP ${response.status}`);
    }
    return await response.json();
  },

  /**
   * Phase 9: Fetch resume draft by ID
   */
  async fetchResumeDraftLive(
    draftId: string,
    token?: string | null
  ): Promise<LiveResumeDraftResponse> {
    const headers: Record<string, string> = { 'Accept': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/builder/resumes/${draftId}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch draft: HTTP ${response.status}`);
    }
    return await response.json();
  },

  /**
   * Phase 9: Update resume draft (Autosave)
   */
  async updateResumeDraftLive(
    draftId: string,
    data: LiveResumeBuilderData,
    title?: string,
    templateId?: string,
    token?: string | null
  ): Promise<LiveResumeDraftResponse> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/builder/resumes/${draftId}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify({ title, data, template_id: templateId }),
    });

    if (!response.ok) {
      throw new Error(`Autosave failed: HTTP ${response.status}`);
    }
    return await response.json();
  },

  /**
   * Phase 9: Save version snapshot
   */
  async createResumeVersionLive(
    draftId: string,
    note: string,
    token?: string | null
  ): Promise<LiveResumeVersionItem> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/builder/resumes/${draftId}/version`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ note }),
    });

    if (!response.ok) {
      throw new Error(`Failed to create version: HTTP ${response.status}`);
    }
    return await response.json();
  },

  /**
   * Phase 9: List saved versions
   */
  async listResumeVersionsLive(
    draftId: string,
    token?: string | null
  ): Promise<LiveVersionListResponse> {
    const headers: Record<string, string> = { 'Accept': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/builder/resumes/${draftId}/versions`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error(`Failed to list versions: HTTP ${response.status}`);
    }
    return await response.json();
  },

  /**
   * Phase 9: Get AI edit suggestions (clarity, STAR metrics, job tailor)
   */
  async fetchAIEditSuggestionsLive(
    draftId: string,
    request: {
      focus_area?: string;
      job_description?: string;
      target_section?: string;
      current_data?: LiveResumeBuilderData;
    },
    token?: string | null
  ): Promise<LiveAIEditSuggestResponse> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/builder/resumes/${draftId}/suggest`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch AI suggestions: HTTP ${response.status}`);
    }
    return await response.json();
  },

  /**
   * Phase 9: Rerun Phase 5 ATS scoring on draft
   */
  async reanalyzeResumeDraftLive(
    draftId: string,
    token?: string | null
  ): Promise<LiveBuilderAnalysisResponse> {
    const headers: Record<string, string> = { 'Accept': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/builder/resumes/${draftId}/analyze`, {
      method: 'POST',
      headers,
    });

    if (!response.ok) {
      throw new Error(`Re-analysis failed: HTTP ${response.status}`);
    }
    return await response.json();
  },

  /**
   * Phase 9: Export resume to native DOCX (returns download Blob)
   */
  async exportResumeDocxBlobLive(
    draftId: string,
    data?: LiveResumeBuilderData,
    templateId?: string,
    token?: string | null
  ): Promise<Blob> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/builder/resumes/${draftId}/export/docx`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ data, template_id: templateId }),
    });

    if (!response.ok) {
      throw new Error(`DOCX export failed with HTTP ${response.status}`);
    }
    return await response.blob();
  },

  /**
   * Phase 9: Export resume to native vector PDF (returns download Blob)
   */
  async exportResumePdfBlobLive(
    draftId: string,
    data?: LiveResumeBuilderData,
    templateId?: string,
    token?: string | null
  ): Promise<Blob> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/builder/resumes/${draftId}/export/pdf`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ data, template_id: templateId }),
    });

    if (!response.ok) {
      throw new Error(`PDF export failed with HTTP ${response.status}`);
    }
    return await response.blob();
  },

  /**
   * Phase 10: Generate personalized learning roadmap via POST /api/v1/learning/roadmap/generate
   */
  async generateLearningRoadmapLive(
    request: LiveRoadmapGenerateRequest,
    token?: string | null
  ): Promise<LiveLearningRoadmapResponse> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/learning/roadmap/generate`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      let errorMsg = `Failed to generate learning roadmap: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }
    return await response.json();
  },

  /**
   * Phase 10: Fetch current user's active learning roadmap via GET /api/v1/learning/roadmap/current
   */
  async fetchCurrentLearningRoadmapLive(token?: string | null): Promise<LiveLearningRoadmapResponse> {
    const headers: Record<string, string> = { 'Accept': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/learning/roadmap/current`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      let errorMsg = `Failed to fetch active roadmap: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }
    return await response.json();
  },

  /**
   * Phase 10: Fetch roadmap by ID via GET /api/v1/learning/roadmap/{roadmap_id}
   */
  async fetchLearningRoadmapByIdLive(roadmapId: string, token?: string | null): Promise<LiveLearningRoadmapResponse> {
    const headers: Record<string, string> = { 'Accept': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/learning/roadmap/${roadmapId}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      let errorMsg = `Failed to fetch roadmap: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }
    return await response.json();
  },

  /**
   * Phase 10: Fetch task details via GET /api/v1/learning/roadmap/{roadmap_id}/tasks/{task_id}
   */
  async fetchRoadmapTaskDetailsLive(
    roadmapId: string,
    taskId: string,
    token?: string | null
  ): Promise<LiveRoadmapTask> {
    const headers: Record<string, string> = { 'Accept': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/learning/roadmap/${roadmapId}/tasks/${taskId}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      let errorMsg = `Failed to fetch task details: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }
    return await response.json();
  },

  /**
   * Phase 10: Update task status/notes via PATCH /api/v1/learning/roadmap/{roadmap_id}/tasks/{task_id}
   */
  async updateRoadmapTaskStatusLive(
    roadmapId: string,
    taskId: string,
    updateData: LiveTaskStatusUpdateRequest,
    token?: string | null
  ): Promise<LiveLearningRoadmapResponse> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/learning/roadmap/${roadmapId}/tasks/${taskId}`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify(updateData),
    });

    if (!response.ok) {
      let errorMsg = `Failed to update task status: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }
    return await response.json();
  },

  /**
   * Phase 10: Update preferences via PATCH /api/v1/learning/roadmap/{roadmap_id}/preferences
   */
  async updateRoadmapPreferencesLive(
    roadmapId: string,
    updateData: LiveRoadmapPreferencesUpdateRequest,
    token?: string | null
  ): Promise<LiveLearningRoadmapResponse> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/learning/roadmap/${roadmapId}/preferences`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify(updateData),
    });

    if (!response.ok) {
      let errorMsg = `Failed to update preferences: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }
    return await response.json();
  },

  /**
   * Phase 10: Refresh roadmap via POST /api/v1/learning/roadmap/{roadmap_id}/refresh
   */
  async refreshLearningRoadmapLive(
    roadmapId: string,
    refreshData: LiveRoadmapRefreshRequest,
    token?: string | null
  ): Promise<LiveLearningRoadmapResponse> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/learning/roadmap/${roadmapId}/refresh`, {
      method: 'POST',
      headers,
      body: JSON.stringify(refreshData),
    });

    if (!response.ok) {
      let errorMsg = `Failed to refresh roadmap: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }
    return await response.json();
  },

  /**
   * Phase 10: Fetch roadmap progress statistics via GET /api/v1/learning/roadmap/{roadmap_id}/progress
   */
  async fetchRoadmapProgressLive(
    roadmapId: string,
    token?: string | null
  ): Promise<LiveRoadmapProgressResponse> {
    const headers: Record<string, string> = { 'Accept': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/learning/roadmap/${roadmapId}/progress`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      let errorMsg = `Failed to fetch progress stats: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }
    return await response.json();
  },

  /**
   * Phase 11: List saved evaluation reports via GET /api/v1/reports
   */
  async fetchSavedReportsLive(
    options?: { page?: number; page_size?: number; target_role?: string },
    token?: string | null
  ): Promise<LiveReportsListResponse> {
    const headers: Record<string, string> = { 'Accept': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const params = new URLSearchParams();
    if (options?.page) params.append('page', String(options.page));
    if (options?.page_size) params.append('page_size', String(options.page_size));
    if (options?.target_role) params.append('target_role', options.target_role);

    const queryStr = params.toString() ? `?${params.toString()}` : '';
    const response = await fetch(`${API_BASE_URL}/reports${queryStr}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error(`Failed to load saved reports: HTTP ${response.status}`);
    }
    return await response.json();
  },

  /**
   * Phase 11: Save and snapshot an analysis report via POST /api/v1/reports/save
   */
  async saveReportLive(
    request: LiveReportSaveRequest,
    token?: string | null
  ): Promise<LiveDetailedReportResponse> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/reports/save`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      let errorMsg = `Failed to save assessment report: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }
    return await response.json();
  },

  /**
   * Phase 11: Get detailed report by ID via GET /api/v1/reports/{report_id}
   */
  async fetchDetailedReportLive(
    reportId: string,
    token?: string | null
  ): Promise<LiveDetailedReportResponse> {
    const headers: Record<string, string> = { 'Accept': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/reports/${reportId}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      let errorMsg = `Failed to fetch detailed report: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }
    return await response.json();
  },

  /**
   * Phase 11: Delete a saved report via DELETE /api/v1/reports/{report_id}
   */
  async deleteReportLive(
    reportId: string,
    token?: string | null
  ): Promise<boolean> {
    const headers: Record<string, string> = { 'Accept': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/reports/${reportId}`, {
      method: 'DELETE',
      headers,
    });

    if (!response.ok) {
      let errorMsg = `Failed to delete report: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }
    const data = await response.json();
    return data.success;
  },

  /**
   * Phase 11: Compare two reports via GET /api/v1/reports/{report_id}/compare/{other_report_id}
   */
  async compareReportsLive(
    reportIdA: string,
    reportIdB: string,
    token?: string | null
  ): Promise<LiveReportComparisonResponse> {
    const headers: Record<string, string> = { 'Accept': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/reports/${reportIdA}/compare/${reportIdB}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      let errorMsg = `Failed to compare reports: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }
    return await response.json();
  },

  /**
   * Phase 11: Fetch career progress analytics summary via GET /api/v1/reports/analytics/summary
   */
  async fetchProgressAnalyticsSummaryLive(
    token?: string | null
  ): Promise<LiveProgressAnalyticsSummaryResponse> {
    const headers: Record<string, string> = { 'Accept': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/reports/analytics/summary`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      let errorMsg = `Failed to fetch progress analytics: HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.detail) errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }
    return await response.json();
  },

  /**
   * Phase 11: Export detailed assessment report as native PDF (returns Blob)
   */
  async exportReportPdfBlobLive(
    reportId: string,
    token?: string | null
  ): Promise<Blob> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/reports/${reportId}/export/pdf`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error(`Report PDF export failed with HTTP ${response.status}`);
    }
    return await response.blob();
  },



  // -------------------------------------------------------------
  // Client-side demonstration helpers (strictly separated)
  // -------------------------------------------------------------

  async getReadinessScore(): Promise<ReadinessScore> {
    return { ...mockReadinessScore };
  },

  async getResumeSections(): Promise<ResumeSection[]> {
    return [...mockResumeSections];
  },

  async getReviewFindings(): Promise<ReviewFinding[]> {
    return [...mockReviewFindings];
  },

  async uploadResumeFile(file: File): Promise<UploadResumeResponse> {
    return {
      success: true,
      message: 'Resume file staged successfully in client preview.',
      fileInfo: {
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type || (file.name.endsWith('.pdf') ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
        uploadedAt: new Date().toLocaleTimeString(),
      },
      notice: 'Backend extraction & OCR engine will be connected in Phase 3. Currently operating in client validation mode.',
    };
  },

  async matchJobDescription(company: string, title: string, description: string): Promise<JobMatchAnalysis> {
    return {
      ...mockJobMatchAnalysis,
      targetCompany: company.trim() || mockJobMatchAnalysis.targetCompany,
      targetRole: title.trim() || mockJobMatchAnalysis.targetRole,
      verifiedEvidenceSummary: description
        ? `Evaluated against custom input for ${company || 'Target Company'}. 7 requirements verified from candidate experience.`
        : mockJobMatchAnalysis.verifiedEvidenceSummary,
    };
  },

  async getProfileConnections(): Promise<ProfileConnection[]> {
    return [...mockProfileConnections];
  },

  async updateProfileConnection(id: string, usernameOrUrl: string, status: 'connected' | 'not_connected'): Promise<ProfileConnection[]> {
    const updated = mockProfileConnections.map((item) =>
      item.id === id ? { ...item, usernameOrUrl, status, lastSynced: status === 'connected' ? 'Just now' : undefined } : item
    );
    return updated;
  },

  async getLearningRoadmap(): Promise<LearningTask[]> {
    return [...mockLearningTasks];
  },

  async getReports(): Promise<CareerReport[]> {
    return [...mockReports];
  },

  async getStudentProfile(): Promise<StudentProfile> {
    return { ...mockStudentProfile };
  },

  async updateStudentProfile(profile: Partial<StudentProfile>): Promise<StudentProfile> {
    return { ...mockStudentProfile, ...profile };
  },
};
