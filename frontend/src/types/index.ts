export type ReadinessTier = 'Ready for Market' | 'Nearly Ready' | 'Needs Improvement' | 'Critical Gaps';

export interface ReadinessScore {
  overall: number; // 0 - 100
  atsScore: number;
  skillAlignment: number;
  experienceImpact: number;
  presentation: number;
  tier: ReadinessTier;
}

export interface ResumeSection {
  id: string;
  title: string;
  content: string;
  wordCount: number;
  completeness: number; // 0 - 100
}

export type FindingSeverity = 'error' | 'improvement' | 'missing' | 'keyword';
export type FindingStatus = 'pending' | 'accepted' | 'rejected';

export interface ReviewFinding {
  id: string;
  type: FindingSeverity;
  title: string;
  location: string;
  explanation: string;
  proposedCorrection: string;
  status: FindingStatus;
  originalSnippet?: string;
  category: string;
}

export interface MatchedSkill {
  name: string;
  category: 'core' | 'framework' | 'tools' | 'soft-skills';
  level: 'advanced' | 'intermediate' | 'foundational';
  evidenceQuote: string;
  location: string;
  confidence: number; // 0 - 100
}

export interface SkillGap {
  name: string;
  importance: 'Required' | 'Preferred' | 'Bonus';
  frequencyInJD: number;
  learningDifficulty: 'Low' | 'Medium' | 'High';
  recommendedResource: string;
}

export interface JobMatchAnalysis {
  id: string;
  targetRole: string;
  targetCompany: string;
  overallMatchScore: number;
  hardSkillMatchScore: number;
  experienceMatchScore: number;
  matchedRequirements: MatchedSkill[];
  skillGaps: SkillGap[];
  verifiedEvidenceSummary: string;
  recommendations: string[];
}

export type ConnectionPlatform = 'github' | 'linkedin' | 'leetcode' | 'hackerrank' | 'portfolio' | 'kaggle';
export type ConnectionStatus = 'not_connected' | 'connected' | 'pending';

export interface ProfileConnection {
  id: ConnectionPlatform;
  name: string;
  iconName: string;
  description: string;
  status: ConnectionStatus;
  usernameOrUrl: string;
  lastSynced?: string;
  metricsPreview?: {
    label: string;
    value: string;
  }[];
}

export interface LearningTask {
  id: string;
  title: string;
  skill: string;
  category: 'Project' | 'Course' | 'Certification' | 'Practice';
  estimatedHours: number;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  status: 'not_started' | 'in_progress' | 'completed';
  linkUrl: string;
}

export interface CareerReport {
  id: string;
  date: string;
  resumeName: string;
  targetRole: string;
  overallScore: number;
  atsScore: number;
  matchScore: number;
  status: 'completed' | 'draft';
}

export interface StudentProfile {
  fullName: string;
  email: string;
  phone: string;
  location: string;
  university: string;
  degree: string;
  graduationYear: string;
  targetRole: string;
  preferredIndustries: string[];
  workPreference: 'Remote' | 'Hybrid' | 'Onsite' | 'Flexible';
  scoringStrictness: 'Lenient' | 'Standard ATS' | 'Strict BigTech';
  emailAlerts: boolean;
}

export type ExtractionStatus = 'success' | 'partial' | 'ocr_unavailable' | 'failed';

export interface LiveResumeUploadResponse {
  resume_id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  page_count: number;
  parser_method: string;
  extraction_status: ExtractionStatus;
  is_scanned: boolean;
  detected_sections: string[];
  word_count: number;
  character_count: number;
  status_message: string;
  extracted_at: string;
}

export interface LiveResumeDetailResponse extends LiveResumeUploadResponse {
  sections: Record<string, string>;
  quality_assessment: {
    total_words: number;
    total_characters: number;
    detected_sections_count: number;
    detected_sections: string[];
    missing_core_sections: string[];
    quality_score: number;
    quality_level: string;
    has_contact_info: boolean;
  };
}

export interface LiveResumeTextResponse {
  resume_id: string;
  filename: string;
  raw_text: string;
  word_count: number;
  character_count: number;
  line_count: number;
  parser_method: string;
  extraction_status: string;
}

export interface LiveResumeStatus {
  services_configured: boolean;
  pdf_parser_available: boolean;
  docx_parser_available: boolean;
  ocr_fallback_available: boolean;
  ai_explainer_configured: boolean;
  ocr_setup_guide?: string;
  status_message: string;
  roadmap_phase: string;
}

export interface LiveSkillItem {
  name: string;
  category: string;
  evidence_snippet: string;
  source_section: string;
  occurrences: number;
}

export interface LiveResumeAnalysisResponse {
  resume_id: string;
  filename: string;
  overall_score: number;
  readiness_tier: string;
  component_scores: {
    structure: number;
    content_quality: number;
    skill_evidence: number;
    ats_readability: number;
  };
  scoring_weights: Record<string, number>;
  scoring_rationale: string[];
  extracted_skills: Record<string, LiveSkillItem[]>;
  detected_sections: string[];
  missing_sections: Array<{ section: string; importance: string; message: string }>;
  findings: ReviewFinding[];
  bullet_point_evaluations: Array<{
    original_snippet: string;
    section: string;
    word_count: number;
    score: number;
    has_metric: boolean;
    has_strong_verb: boolean;
    issues: string[];
    suggested_rewrite: string;
  }>;
  data_quality_warnings: string[];
  disclaimer: string;
  analyzed_at: string;
}

export interface LiveJobMatchRequirementItem {
  name: string;
  category: string;
  importance: 'required' | 'preferred' | string;
  status: 'matched' | 'partial' | 'missing_evidence' | 'needs_verification' | string;
  demonstrated_in_project: boolean;
  evidence_quote: string;
  location: string;
  confidence: number;
  explanation: string;
  recommended_action: string;
  equivalent_found?: string | null;
}

export interface LiveJobMatchResponse {
  match_id: string;
  company: string;
  role: string;
  overall_match_score: number;
  hard_skill_match_score: number;
  preferred_match_score: number;
  experience_match_score: number;
  evidence_strength_score: number;
  readiness_tier: string;
  matched_requirements: LiveJobMatchRequirementItem[];
  partial_matches: LiveJobMatchRequirementItem[];
  missing_evidence: LiveJobMatchRequirementItem[];
  verified_evidence_summary: string;
  recommendations: string[];
  disclaimer: string;
  analyzed_at: string;
}

export interface LiveFetchJobUrlResponse {
  url: string;
  extracted_text: string;
  char_count: number;
  message: string;
}

export interface LiveProfileConnectionItem {
  id: string;
  name: string;
  icon_name: string;
  description: string;
  status: 'connected' | 'not_connected' | 'partially_connected' | 'inaccessible' | 'rate_limited' | string;
  username_or_url: string;
  last_synced?: string | null;
  retrieval_status: string;
  metrics_preview: Array<{ label: string; value: string }>;
  metadata?: Record<string, any>;
}

export interface LiveProfileConnectionsResponse {
  connections: LiveProfileConnectionItem[];
  total_connected: number;
  message: string;
}

export interface LiveClaimVerificationItem {
  claim_id: string;
  claim_type: string;
  original_claim: string;
  project_name?: string | null;
  claimed_technologies: string[];
  evidence_source: string;
  supporting_excerpt: string;
  status: 'supported' | 'partially_supported' | 'unverified' | 'inaccessible' | string;
  confidence: number;
  reason: string;
  evidence_limitations: string;
  recommended_action: string;
  repository_url?: string | null;
  has_test_suite: boolean;
  has_documentation: boolean;
  language_breakdown?: Record<string, any>;
}

export interface LiveEvidenceVerificationResponse {
  verification_id: string;
  user_id?: string | null;
  resume_id: string;
  evaluated_at: string;
  total_claims: number;
  supported_claims: number;
  partially_supported_claims: number;
  unverified_claims: number;
  inaccessible_claims: number;
  verification_score: number;
  claims: LiveClaimVerificationItem[];
  connected_sources: string[];
  summary_message: string;
  disclaimer: string;
}

export interface LiveFindingExplanation {
  finding_id: string;
  issue_title: string;
  section: string;
  original_excerpt: string;
  explanation: string;
  impact_reason: string;
  concrete_suggestion: string;
  missing_facts_requested?: string | null;
}

export interface LiveJobMatchExplanationItem {
  requirement_name: string;
  status: 'matched' | 'partial' | 'missing_evidence' | 'needs_verification' | string;
  importance: 'required' | 'preferred' | string;
  job_requirement_explanation: string;
  candidate_evidence_summary: string;
  evidence_quote: string;
  recommended_action: string;
}

export interface LivePrioritizedRecommendation {
  id: string;
  priority: 'high' | 'medium' | 'low';
  category: 'skills' | 'experience' | 'structure' | 'clarity' | 'verification' | string;
  title: string;
  description: string;
  linked_finding_id?: string | null;
  priority_reason: string;
  effort_estimate: 'quick_fix' | 'moderate' | 'substantial' | string;
}

export interface LiveResumeExplanationResponse {
  resume_id: string;
  is_ai_generated: boolean;
  provider: string;
  overall_score: number;
  readiness_tier: string;
  executive_summary: string;
  finding_explanations: LiveFindingExplanation[];
  prioritized_recommendations: LivePrioritizedRecommendation[];
  disclaimer: string;
  generated_at: string;
}

export interface LiveJobMatchExplanationResponse {
  match_id: string;
  is_ai_generated: boolean;
  provider: string;
  overall_match_score: number;
  company: string;
  role: string;
  match_summary: string;
  requirement_explanations: LiveJobMatchExplanationItem[];
  prioritized_recommendations: LivePrioritizedRecommendation[];
  disclaimer: string;
  generated_at: string;
}

export interface LiveAssistantChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface LiveAssistantChatRequest {
  message: string;
  history?: LiveAssistantChatMessage[];
  resume_id?: string | null;
  match_id?: string | null;
  verification_id?: string | null;
}

export interface LiveAssistantChatResponse {
  reply: string;
  is_ai_generated: boolean;
  provider: string;
  referenced_reports: string[];
  suggested_followups: string[];
}

export interface LiveEducationEntry {
  id: string;
  school: string;
  degree: string;
  field_of_study: string;
  start_date: string;
  end_date: string;
  gpa: string;
  highlights: string;
}

export interface LiveExperienceEntry {
  id: string;
  role: string;
  company: string;
  location: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  bullets: string[];
}

export interface LiveProjectEntry {
  id: string;
  name: string;
  tech_stack: string;
  url: string;
  bullets: string[];
}

export interface LiveCertificationEntry {
  id: string;
  name: string;
  issuer: string;
  date: string;
  url: string;
}

export interface LiveAchievementEntry {
  id: string;
  title: string;
  description: string;
  date: string;
}

export interface LiveSkillsData {
  languages: string;
  frameworks: string;
  databases: string;
  tools: string;
  soft_skills: string;
}

export interface LiveContactData {
  full_name: string;
  email: string;
  phone: string;
  location: string;
  linkedin: string;
  github: string;
  portfolio: string;
}

export interface LiveResumeBuilderData {
  contact: LiveContactData;
  summary: string;
  education: LiveEducationEntry[];
  skills: LiveSkillsData;
  projects: LiveProjectEntry[];
  experience: LiveExperienceEntry[];
  certifications: LiveCertificationEntry[];
  achievements: LiveAchievementEntry[];
  section_order: string[];
  template_id: 'modern' | 'classic' | 'minimal' | string;
}

export interface LiveResumeDraftResponse {
  draft_id: string;
  user_id?: string | null;
  title: string;
  created_at: string;
  updated_at: string;
  current_version: number;
  data: LiveResumeBuilderData;
  is_saved: boolean;
  imported_from_resume_id?: string | null;
}

export interface LiveResumeVersionItem {
  version_id: string;
  version_number: number;
  created_at: string;
  note: string;
  data_snapshot: LiveResumeBuilderData;
}

export interface LiveVersionListResponse {
  draft_id: string;
  total_versions: number;
  versions: LiveResumeVersionItem[];
}

export interface LiveAISuggestionItem {
  id: string;
  target_section: string;
  target_entry_id?: string | null;
  target_bullet_index?: number | null;
  title: string;
  original_text: string;
  proposed_text: string;
  rationale: string;
  missing_facts_prompt?: string | null;
}

export interface LiveAIEditSuggestResponse {
  draft_id: string;
  is_ai_generated: boolean;
  provider: string;
  suggestions: LiveAISuggestionItem[];
  disclaimer: string;
}

export interface LiveBuilderAnalysisResponse {
  draft_id: string;
  overall_score: number;
  readiness_tier: string;
  component_scores: Record<string, number>;
  detected_skills_count: number;
  findings_count: number;
  analyzed_text_sample: string;
}

// ====================================================================
// Phase 10: Personalized Learning Roadmap Types
// ====================================================================

export type SkillEvidenceStatus = 'demonstrated' | 'partial_evidence' | 'not_demonstrated';
export type SkillPriority = 'high' | 'medium' | 'low';
export type RoadmapTaskStatus = 'not_started' | 'in_progress' | 'completed';

export interface LiveSkillGapItem {
  skill: string;
  importance: 'required' | 'preferred' | 'bonus' | string;
  evidence_found: string;
  evidence_status: SkillEvidenceStatus;
  learning_priority: SkillPriority;
  reason: string;
}

export interface LiveLearningResource {
  title: string;
  url?: string | null;
  resource_type: 'documentation' | 'tutorial' | 'project_guide' | 'user_added' | string;
  is_verified: boolean;
}

export interface LiveRoadmapTask {
  id: string;
  milestone_week: number;
  milestone_title: string;
  title: string;
  instructions: string;
  skill: string;
  priority: SkillPriority;
  estimated_hours: number;
  prerequisites: string[];
  resources: LiveLearningResource[];
  practical_exercise: string;
  deliverable: string;
  completion_criteria: string;
  target_role_requirement?: string | null;
  status: RoadmapTaskStatus;
  user_notes?: string | null;
  custom_resources?: LiveLearningResource[];
  started_at?: string | null;
  completed_at?: string | null;
}

export interface LiveRoadmapMilestone {
  week_number: number;
  title: string;
  description: string;
  focus_skills: string[];
  tasks: LiveRoadmapTask[];
}

export interface LiveLearningRoadmapResponse {
  id: string;
  user_id?: string | null;
  target_role: string;
  target_company?: string | null;
  job_description_id?: string | null;
  weekly_hours: number;
  target_weeks: number;
  skill_gaps: LiveSkillGapItem[];
  milestones: LiveRoadmapMilestone[];
  all_tasks: LiveRoadmapTask[];
  total_tasks: number;
  completed_tasks: number;
  in_progress_tasks: number;
  completion_percentage: number;
  total_estimated_hours: number;
  completed_hours: number;
  is_ai_grounded: boolean;
  provider_used: string;
  disclaimer: string;
  created_at: string;
  updated_at: string;
}

export interface LiveRoadmapProgressResponse {
  roadmap_id: string;
  target_role: string;
  total_tasks: number;
  completed_tasks: number;
  in_progress_tasks: number;
  completion_percentage: number;
  total_estimated_hours: number;
  completed_hours: number;
  remaining_hours: number;
  skills_covered_count: number;
  skills_demonstrated_count: number;
  status_summary: {
    not_started: number;
    in_progress: number;
    completed: number;
  };
}

export interface LiveRoadmapGenerateRequest {
  target_role?: string;
  target_company?: string;
  job_description?: string;
  job_match_id?: string;
  resume_id?: string;
  weekly_hours?: number;
  target_weeks?: number;
}

export interface LiveTaskStatusUpdateRequest {
  status: RoadmapTaskStatus;
  notes?: string;
  custom_resources?: LiveLearningResource[];
}

export interface LiveRoadmapPreferencesUpdateRequest {
  weekly_hours?: number;
  target_weeks?: number;
}

export interface LiveRoadmapRefreshRequest {
  resume_id?: string;
  job_match_id?: string;
  job_description?: string;
  target_role?: string;
  target_company?: string;
}

// ====================================================================
// Phase 11: Reports and Progress Analytics Types
// ====================================================================

export interface LiveReportItem {
  id: string;
  date: string;
  resume_name: string;
  target_role: string;
  overall_score: number;
  ats_score: number;
  match_score: number;
  issues_count: number;
  status: string;
  report_title?: string | null;
}

export interface LiveReportsListResponse {
  reports: LiveReportItem[];
  total: number;
  page: number;
  page_size: number;
  message: string;
}

export interface LiveReportSaveRequest {
  resume_id: string;
  report_title?: string;
  target_role?: string;
  job_match_id?: string;
}

export interface LiveDetailedReportResponse {
  id: string;
  user_id?: string | null;
  report_title: string;
  date: string;
  resume_name: string;
  resume_id: string;
  target_role: string;
  overall_score: number;
  readiness_tier: string;
  ats_score: number;
  match_score: number;
  status: string;
  component_scores: Record<string, number>;
  scoring_rationale: Record<string, string>;
  extracted_skills: Record<string, Array<{ name: string; [key: string]: any }>>;
  detected_sections: string[];
  missing_sections: string[];
  findings: Array<{
    id?: string;
    title: string;
    severity?: string;
    description: string;
    suggestion?: string;
    [key: string]: any;
  }>;
  bullet_evaluations: Array<any>;
  job_match_summary?: {
    match_id?: string;
    target_role?: string;
    company_name?: string;
    overall_match_score?: number;
    matching_skills_count?: number;
    missing_skills_count?: number;
  } | null;
  roadmap_summary?: {
    roadmap_id?: string;
    completion_percentage?: number;
    completed_tasks?: number;
    total_tasks?: number;
  } | null;
  disclaimer: string;
}

export interface LiveReportComparisonResponse {
  report_a_id: string;
  report_b_id: string;
  date_a: string;
  date_b: string;
  title_a: string;
  title_b: string;
  score_a: number;
  score_b: number;
  score_delta: number;
  is_compatible: boolean;
  compatibility_notice?: string | null;
  category_deltas: Record<string, { before: number; after: number; delta: number }>;
  issues_resolved: Array<{ title: string; description?: string; severity?: string }>;
  issues_still_present: Array<{ title: string; description?: string; severity?: string }>;
  issues_newly_identified: Array<{ title: string; description?: string; severity?: string }>;
  job_match_delta?: {
    score_before: number;
    score_after: number;
    delta: number;
  } | null;
  recommended_next_actions: string[];
  disclaimer: string;
}

export interface LiveProgressAnalyticsSummaryResponse {
  total_analyses_completed: number;
  latest_score?: number | null;
  previous_score?: number | null;
  score_progression: Array<{
    report_id: string;
    date: string;
    score: number;
    ats_score: number;
    match_score: number;
    target_role: string;
    title: string;
  }>;
  issues_resolved_total: number;
  current_open_issues: number;
  roadmap_tasks_completed: number;
  roadmap_tasks_total: number;
  roadmap_completion_pct: number;
  skills_by_evidence_type: {
    self_reported: number;
    resume_evidence: number;
    independently_verified: number;
  };
  target_role?: string | null;
  has_historical_data: boolean;
  disclaimer: string;
}




