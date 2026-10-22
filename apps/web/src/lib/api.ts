const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type ApiResponse<T> = { data: T; meta?: Record<string, unknown> };
export type Job = { id: string; title: string; description: string; company_id: string; department?: string; location?: string; employment_type?: string; target_institute?: string | null; target_email_domain?: string | null; created_at?: string; skills: string[]; status: string; scoring_config?: Record<string, number> };
export type Application = { id: string; job_id: string; status: string; created_at: string };
export type CandidateProfile = { id: string; user_id: string; headline?: string; summary?: string; skills: string; experience: string; education: string };
export type JobCandidate = { application: Application; profile: CandidateProfile | null; score: Record<string, unknown> | null };

export async function apiFetch<T>(path: string, options: RequestInit = {}, accessToken?: string): Promise<T> {
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...options.headers,
    },
  });
  const payload = (await response.json()) as ApiResponse<T> | { detail?: string };
  if (!response.ok) {
    throw new Error("detail" in payload && payload.detail ? payload.detail : "Request failed");
  }
  return (payload as ApiResponse<T>).data;
}

export const api = {
  health: () => apiFetch<{ status: string; service: string }>("/health"),
  publicJobs: () => apiFetch<Job[]>("/public/jobs"),
  publicJob: (id: string) => apiFetch<Job>(`/public/jobs/${id}`),
  instituteJobs: (token: string) => apiFetch<Job[]>("/institutes/jobs", {}, token),
  candidateJob: (token: string, id: string) => apiFetch<Job>(`/candidate/jobs/${id}`, {}, token),
  applications: (token: string) => apiFetch<Application[]>("/applications", {}, token),
  companyJobs: (token: string) => apiFetch<Job[]>("/jobs", {}, token),
  createCompany: (token: string, body: Record<string, string>) => apiFetch<Record<string, unknown>>("/companies", { method: "POST", body: JSON.stringify(body) }, token),
  createJob: (token: string, body: Record<string, unknown>) => apiFetch<Job>("/jobs", { method: "POST", body: JSON.stringify(body) }, token),
  analyzeJob: (token: string, id: string) => apiFetch<Record<string, unknown>>(`/jobs/${id}/analyze-jd`, { method: "POST" }, token),
  publishJob: (token: string, id: string) => apiFetch<Job>(`/jobs/${id}/publish`, { method: "POST" }, token),
  updateScoring: (token: string, id: string, body: Record<string, number>) => apiFetch<Job>(`/jobs/${id}/scoring`, { method: "PATCH", body: JSON.stringify(body) }, token),
  jobCandidates: (token: string, id: string) => apiFetch<JobCandidate[]>(`/jobs/${id}/candidates`, {}, token),
  compareCandidates: (token: string, jobId: string, applicationIds: string[]) => apiFetch<Record<string, unknown>[]>(`/jobs/${jobId}/compare?application_ids=${applicationIds.join(",")}`, {}, token),
  recalculateRankings: (token: string, id: string) => apiFetch<Record<string, unknown>[]>(`/jobs/${id}/rankings/recalculate`, { method: "POST" }, token),
  updateApplicationStatus: (token: string, id: string, status: string) => apiFetch<Application>(`/applications/${id}/status`, { method: "PATCH", body: JSON.stringify({ status }) }, token),
  profile: (token: string) => apiFetch<CandidateProfile>("/candidates/profile", {}, token),
  saveProfile: (token: string, body: Record<string, unknown>) => apiFetch<CandidateProfile>("/candidates/profile", { method: "POST", body: JSON.stringify(body) }, token),
  uploadResume: (token: string, file: File) => { const body = new FormData(); body.append("file", file); return apiFetch<Record<string, unknown>>("/candidates/resumes/upload", { method: "POST", body }, token); },
  apply: (token: string, jobId: string) => apiFetch<Application>(`/jobs/${jobId}/apply`, { method: "POST" }, token),
  applicationsWithToken: (token: string) => apiFetch<Application[]>("/applications", {}, token),
  notifications: (token: string, unreadOnly = false) =>
    apiFetch<unknown[]>(`/notifications?unread_only=${unreadOnly}`, {}, token),
  markNotificationRead: (token: string, id: string) =>
    apiFetch<unknown>(`/notifications/${id}`, { method: "PATCH", body: JSON.stringify({ is_read: true }) }, token),
};
