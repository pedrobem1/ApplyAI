export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const ACCESS_TOKEN_STORAGE_KEY = "applyai_access_token";

export type AuthStatusResponse = {
  access_required: boolean;
  demo_login_enabled: boolean;
  demo_username: string | null;
};

export type AuthLoginResponse = {
  access_token: string;
  demo_seeded: boolean;
};

export type ResumeUploadResponse = {
  resume_id: number;
  filename: string;
  character_count: number;
  preview: string;
};

export type ResumeEvidence = {
  id: number;
  skill: string;
  evidence_text: string;
  source: string | null;
  evidence_type: string;
};

export type AdditionalResumeEvidenceRequest = {
  skill: string;
  evidence_text: string;
};

export type ResumeExtractionResponse = {
  resume_id: number;
  filename: string;
  evidence: ResumeEvidence[];
};

export type JobImportResponse = {
  job_id: number;
  source_type: string;
  url: string | null;
  title: string | null;
  company: string | null;
  scrape_status: string | null;
  character_count: number;
  preview: string;
};

export type JobPreviewResponse = Omit<JobImportResponse, "job_id"> & {
  description: string;
};

export type JobListItem = JobImportResponse & {
  location: string | null;
};

export type JobRequirement = {
  id?: number;
  name: string;
  category: string;
  importance: string;
  raw_text: string;
};

export type JobRequirementExtractionResponse = {
  job_id: number | null;
  role: string | null;
  company: string | null;
  location: string | null;
  requirements: JobRequirement[];
};

export type RetrievedEvidence = {
  evidence_id: number;
  skill: string;
  evidence_text: string;
  source: string | null;
  distance: number;
};

export type AnalysisMatch = {
  requirement_id: number;
  requirement_name: string;
  category: string;
  importance: string;
  classification: string;
  confidence: number;
  explanation: string;
  gap_type: string;
  evidence: RetrievedEvidence[];
};

export type AnalysisResponse = {
  job_id: number;
  resume_id: number;
  score: number;
  embedded_resume_evidence: number;
  embedded_job_requirements: number;
  matches: AnalysisMatch[];
};

export type AiRunResponse = {
  id: number;
  user_id: number | null;
  task_type: string;
  model: string;
  input_tokens: number | null;
  output_tokens: number | null;
  estimated_cost: string | null;
  latency_ms: number | null;
  success: string;
  error_message: string | null;
  created_at: string;
};

export class ApiRequestError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
  }
}

export function getAccessToken(): string {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY) ?? "";
}

export function setAccessToken(token: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, token);
}

export function clearAccessToken() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
}

export async function apiRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const accessToken = getAccessToken();
  const shouldSendJsonContentType = options?.body !== undefined && !(options.body instanceof FormData);
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(shouldSendJsonContentType ? { "Content-Type": "application/json" } : {}),
      ...(accessToken ? { "X-ApplyAI-Access-Token": accessToken } : {}),
      ...options?.headers,
    },
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const error = (await response.json()) as { detail?: string };
      message = error.detail ?? message;
    } catch {
      message = await response.text();
    }
    if (response.status === 401) clearAccessToken();
    throw new ApiRequestError(message, response.status);
  }

  if (response.status === 204) return undefined as T;

  const text = await response.text();
  if (!text) return undefined as T;

  return JSON.parse(text) as T;
}
