import axios, { AxiosError, AxiosResponse } from "axios";
import {
  AuthResponse,
  LoginCredentials,
  RegisterData,
  Project,
  ProjectCreate,
  ProjectStats,
  Candidate,
  CandidateFilters,
  PaginatedCandidates,
  ImportPreview,
  ImportResult,
  ColumnMapping,
  EvaluationJob,
  RecruiterQuery,
  RecruiterQueryResponse,
  QueryHistoryItem,
  DashboardStats,
  SelfReviewPreview,
  SelfReviewReport,
  Subscription,
} from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle errors
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// ============================================================
// Auth API
// ============================================================

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const formData = new FormData();
    formData.append("username", credentials.email);
    formData.append("password", credentials.password);
    const response = await api.post<AuthResponse>("/api/v1/auth/login", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  },

  register: async (data: RegisterData): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>("/api/v1/auth/register", data);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post("/api/v1/auth/logout");
  },

  getMe: async () => {
    const response = await api.get("/api/v1/auth/me");
    return response.data;
  },
};

// ============================================================
// Projects API
// ============================================================

export const projectsApi = {
  list: async (): Promise<Project[]> => {
    const response = await api.get<Project[]>("/api/v1/projects");
    return response.data;
  },

  get: async (id: string): Promise<Project> => {
    const response = await api.get<Project>(`/api/v1/projects/${id}`);
    return response.data;
  },

  create: async (data: ProjectCreate): Promise<Project> => {
    const response = await api.post<Project>("/api/v1/projects", data);
    return response.data;
  },

  update: async (id: string, data: Partial<ProjectCreate>): Promise<Project> => {
    const response = await api.put<Project>(`/api/v1/projects/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/api/v1/projects/${id}`);
  },

  getStats: async (id: string): Promise<ProjectStats> => {
    const response = await api.get<ProjectStats>(`/api/v1/projects/${id}/stats`);
    return response.data;
  },

  getDashboardStats: async (): Promise<DashboardStats> => {
    const response = await api.get<DashboardStats>("/api/v1/projects/dashboard/stats");
    return response.data;
  },
};

// ============================================================
// Candidates API
// ============================================================

export const candidatesApi = {
  list: async (
    projectId: string,
    filters?: CandidateFilters
  ): Promise<PaginatedCandidates> => {
    const response = await api.get<PaginatedCandidates>(
      `/api/v1/projects/${projectId}/candidates`,
      { params: filters }
    );
    return response.data;
  },

  get: async (projectId: string, candidateId: string): Promise<Candidate> => {
    const response = await api.get<Candidate>(
      `/api/v1/projects/${projectId}/candidates/${candidateId}`
    );
    return response.data;
  },

  updateNotes: async (
    projectId: string,
    candidateId: string,
    notes: string
  ): Promise<Candidate> => {
    const response = await api.patch<Candidate>(
      `/api/v1/projects/${projectId}/candidates/${candidateId}`,
      { recruiter_notes: notes }
    );
    return response.data;
  },

  exportCSV: async (projectId: string, filters?: CandidateFilters): Promise<Blob> => {
    const response = await api.get(
      `/api/v1/projects/${projectId}/candidates/export`,
      { params: filters, responseType: "blob" }
    );
    return response.data;
  },
};

// ============================================================
// Import API
// ============================================================

export const importApi = {
  previewCSV: async (projectId: string, file: File): Promise<ImportPreview> => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await api.post<ImportPreview>(
      `/api/v1/projects/${projectId}/import/preview`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
    return response.data;
  },

  importCSV: async (
    projectId: string,
    file: File,
    mappings: ColumnMapping[]
  ): Promise<ImportResult> => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("mappings", JSON.stringify(mappings));
    const response = await api.post<ImportResult>(
      `/api/v1/projects/${projectId}/import/csv`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
    return response.data;
  },

  importResumes: async (
    projectId: string,
    files: File[],
    onProgress?: (progress: number) => void
  ): Promise<ImportResult> => {
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));
    const response = await api.post<ImportResult>(
      `/api/v1/projects/${projectId}/import/resumes`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total && onProgress) {
            const progress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            onProgress(progress);
          }
        },
      }
    );
    return response.data;
  },
};

// ============================================================
// Evaluation API
// ============================================================

export const evaluationApi = {
  startEvaluation: async (projectId: string): Promise<EvaluationJob> => {
    const response = await api.post<EvaluationJob>(
      `/api/v1/projects/${projectId}/evaluate`
    );
    return response.data;
  },

  getJobStatus: async (projectId: string, jobId: string): Promise<EvaluationJob> => {
    const response = await api.get<EvaluationJob>(
      `/api/v1/projects/${projectId}/evaluate/${jobId}`
    );
    return response.data;
  },

  query: async (data: RecruiterQuery): Promise<RecruiterQueryResponse> => {
    const response = await api.post<RecruiterQueryResponse>(
      `/api/v1/projects/${data.project_id}/query`,
      data
    );
    return response.data;
  },

  getQueryHistory: async (projectId: string): Promise<QueryHistoryItem[]> => {
    const response = await api.get<QueryHistoryItem[]>(
      `/api/v1/projects/${projectId}/query/history`
    );
    return response.data;
  },
};

// ============================================================
// Self-Review API
// ============================================================

export const reviewApi = {
  submit: async (
    resumeFile: File,
    jobDescription: string
  ): Promise<SelfReviewPreview> => {
    const formData = new FormData();
    formData.append("resume", resumeFile);
    formData.append("job_description", jobDescription);
    const response = await api.post<SelfReviewPreview>(
      "/api/v1/review/submit",
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
    return response.data;
  },

  getReport: async (token: string): Promise<SelfReviewReport> => {
    const response = await api.get<SelfReviewReport>(`/api/v1/review/${token}`);
    return response.data;
  },

  createPaymentIntent: async (token: string): Promise<{ client_secret: string }> => {
    const response = await api.post<{ client_secret: string }>(
      `/api/v1/review/${token}/payment`
    );
    return response.data;
  },
};

// ============================================================
// Billing API
// ============================================================

export const billingApi = {
  getSubscription: async (): Promise<Subscription> => {
    const response = await api.get<Subscription>("/api/v1/billing/subscription");
    return response.data;
  },

  createCheckoutSession: async (planId: string): Promise<{ url: string }> => {
    const response = await api.post<{ url: string }>(
      "/api/v1/billing/checkout",
      { plan_id: planId }
    );
    return response.data;
  },

  cancelSubscription: async (): Promise<Subscription> => {
    const response = await api.post<Subscription>("/api/v1/billing/cancel");
    return response.data;
  },
};

export default api;
