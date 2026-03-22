// ============================================================
// Auth Types
// ============================================================

export interface User {
  id: string;
  email: string;
  name: string;
  organization_id: string;
  organization_name: string;
  role: "admin" | "recruiter" | "viewer";
  created_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  name: string;
  email: string;
  password: string;
  organization_name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// ============================================================
// Project Types
// ============================================================

export type ProjectStatus =
  | "draft"
  | "active"
  | "evaluating"
  | "completed"
  | "archived";

export interface Project {
  id: string;
  name: string;
  company: string;
  role_title: string;
  job_description: string;
  must_have_skills: string[];
  nice_to_have_skills: string[];
  min_experience_years?: number;
  required_location?: string;
  required_degree?: string;
  max_notice_period_days?: number;
  status: ProjectStatus;
  candidate_count: number;
  evaluated_count: number;
  avg_score?: number;
  organization_id: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  company: string;
  role_title: string;
  job_description: string;
  must_have_skills: string[];
  nice_to_have_skills: string[];
  min_experience_years?: number;
  required_location?: string;
  required_degree?: string;
  max_notice_period_days?: number;
}

export interface ProjectStats {
  total_candidates: number;
  evaluated_candidates: number;
  strong_yes_count: number;
  yes_count: number;
  maybe_count: number;
  no_count: number;
  avg_score: number;
  evaluation_progress: number;
}

// ============================================================
// Candidate Types
// ============================================================

export type Recommendation = "strong_yes" | "yes" | "maybe" | "no";

export interface CandidateScore {
  overall: number;
  skills_match: number;
  experience: number;
  education: number;
  communication: number;
  leadership?: number;
  culture_fit?: number;
}

export interface ScoreBreakdown {
  dimension: string;
  score: number;
  max_score: number;
  reasoning: string;
}

export interface Candidate {
  id: string;
  project_id: string;
  name: string;
  email: string;
  phone?: string;
  location?: string;
  linkedin_url?: string;
  github_url?: string;
  portfolio_url?: string;
  education?: string;
  years_experience?: number;
  current_title?: string;
  current_company?: string;
  skills: string[];
  resume_text?: string;
  resume_filename?: string;
  status: "pending" | "evaluating" | "evaluated" | "error";
  rank?: number;
  score?: number;
  recommendation?: Recommendation;
  skills_match_pct?: number;
  score_breakdown?: ScoreBreakdown[];
  strengths?: string[];
  weaknesses?: string[];
  red_flags?: string[];
  missing_requirements?: string[];
  notable_projects?: string[];
  recruiter_takeaway?: string;
  recruiter_notes?: string;
  confidence_level?: "high" | "medium" | "low";
  created_at: string;
  updated_at: string;
}

export interface CandidateFilters {
  search?: string;
  recommendations?: Recommendation[];
  min_score?: number;
  max_score?: number;
  skills?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export interface PaginatedCandidates {
  candidates: Candidate[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ============================================================
// Import Types
// ============================================================

export interface ColumnMapping {
  csv_column: string;
  field: string;
}

export interface ImportPreview {
  columns: string[];
  sample_rows: Record<string, string>[];
  total_rows: number;
}

export interface ImportResult {
  imported: number;
  failed: number;
  errors: string[];
}

// ============================================================
// Evaluation Types
// ============================================================

export interface EvaluationJob {
  id: string;
  project_id: string;
  status: "pending" | "running" | "completed" | "failed";
  total: number;
  processed: number;
  failed: number;
  started_at?: string;
  completed_at?: string;
  error?: string;
}

export interface RecruiterQuery {
  question: string;
  project_id: string;
  candidate_ids?: string[];
}

export interface RecruiterQueryResponse {
  answer: string;
  referenced_candidates: string[];
  query_id: string;
}

export interface QueryHistoryItem {
  id: string;
  question: string;
  answer: string;
  created_at: string;
}

// ============================================================
// Review Types (Candidate Self-Review)
// ============================================================

export interface SelfReviewSubmission {
  resume_file: File;
  job_description: string;
}

export interface SelfReviewPreview {
  token: string;
  score: number;
  strengths: string[];
  preview_message: string;
  payment_required: boolean;
}

export interface SelfReviewReport {
  token: string;
  score: number;
  explanation: string;
  strengths: string[];
  missing_skills: string[];
  weak_bullets: Array<{ original: string; improved: string }>;
  ats_score: number;
  improvement_suggestions: string[];
  created_at: string;
}

// ============================================================
// Dashboard Types
// ============================================================

export interface DashboardStats {
  total_projects: number;
  active_projects: number;
  total_candidates: number;
  evaluated_candidates: number;
}

// ============================================================
// Billing Types
// ============================================================

export interface Plan {
  id: string;
  name: string;
  price_monthly: number;
  price_yearly: number;
  features: string[];
  candidate_limit: number;
  project_limit: number;
}

export interface Subscription {
  id: string;
  plan: Plan;
  status: "active" | "trialing" | "past_due" | "canceled";
  current_period_end: string;
  cancel_at_period_end: boolean;
}

// ============================================================
// API Response Types
// ============================================================

export interface ApiError {
  detail: string;
  status_code: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}
